from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.deps import get_db, get_current_user
from app.core.security import verify_password, create_access_token, get_password_hash
from app.models.user import User
from app.models.tenant import Tenant
from app.schemas.auth import LoginRequest, TokenResponse, ChangePasswordRequest

router = APIRouter()

# ---- Lockout policy ----
MAX_FAILED = 5
LOCK_MINUTES = 15


def _utcnow():
    return datetime.now(timezone.utc)


def _validate_new_password(pw: str) -> str:
    pw = (pw or "").strip()
    if len(pw) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    return pw


def _is_locked(user: User) -> bool:
    locked_until = getattr(user, "locked_until", None)
    if not locked_until:
        return False

    # handle DB timestamp being naive or aware
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)

    return locked_until > _utcnow()


def _lock_remaining_seconds(user: User) -> int:
    locked_until = getattr(user, "locked_until", None)
    if not locked_until:
        return 0
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)
    sec = int((locked_until - _utcnow()).total_seconds())
    return max(sec, 0)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()

    # Don't leak existence
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    # status check
    if (getattr(user, "status", "active") or "").lower() != "active":
        raise HTTPException(status_code=403, detail="Account disabled. Contact admin.")

    # lockout check
    if _is_locked(user):
        remain = _lock_remaining_seconds(user)
        raise HTTPException(
            status_code=403,
            detail=f"Account locked. Try again in {remain} seconds.",
        )

    # password check
    if not verify_password(body.password, user.hashed_password):
        # increment failures
        cur = int(getattr(user, "failed_login_count", 0) or 0) + 1
        user.failed_login_count = cur

        # lock if reached threshold
        if cur >= MAX_FAILED:
            user.locked_until = _utcnow() + timedelta(minutes=LOCK_MINUTES)

        db.add(user)
        db.commit()

        raise HTTPException(status_code=401, detail="Invalid email or password.")

    # success: clear counters/lock
    if hasattr(user, "failed_login_count"):
        user.failed_login_count = 0
    if hasattr(user, "locked_until"):
        user.locked_until = None

    # Tenant active check (tenant-scoped users except developer)
    if getattr(user, "tenant_id", None) is not None and (user.role or "").lower() != "developer":
        t = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
        if not t or not t.is_active:
            raise HTTPException(status_code=403, detail="Tenant disabled. Contact support.")

    db.add(user)
    db.commit()

    token = create_access_token(
        subject=str(user.id),
        extra_claims={
            "role": user.role,
            "tenant_id": str(user.tenant_id) if user.tenant_id else None,
            "email": user.email,
            "must_change_password": bool(getattr(user, "must_change_password", False)),
        },
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=user.role,
        must_change_password=bool(getattr(user, "must_change_password", False)),
        tenant_id=str(user.tenant_id) if user.tenant_id else None,
        email=user.email,
    )


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    if not verify_password(body.current_password, me.hashed_password):
        raise HTTPException(status_code=401, detail="Current password is incorrect.")

    new_pw = _validate_new_password(body.new_password)

    if verify_password(new_pw, me.hashed_password):
        raise HTTPException(status_code=400, detail="New password must be different.")

    me.hashed_password = get_password_hash(new_pw)
    me.must_change_password = False

    # record timestamps if present
    if hasattr(me, "password_changed_at"):
        me.password_changed_at = func.now()

    # clear temp + lock fields if present
    if hasattr(me, "temp_password_issued_at"):
        me.temp_password_issued_at = None
    if hasattr(me, "failed_login_count"):
        me.failed_login_count = 0
    if hasattr(me, "locked_until"):
        me.locked_until = None

    db.add(me)
    db.commit()

    return {"ok": True}
