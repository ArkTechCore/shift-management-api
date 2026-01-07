from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.security import verify_password, create_access_token, get_password_hash
from app.models.user import User
from app.models.tenant import Tenant
from app.schemas.auth import LoginRequest, TokenResponse, ChangePasswordRequest

router = APIRouter()

# lockout policy
MAX_FAILED = 5
LOCKOUT_MINUTES = 15


def _now_utc() -> datetime:
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
    # locked_until from DB might be timezone-aware
    return locked_until > _now_utc()


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()

    # IMPORTANT: do not reveal if email exists
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    # status check
    if (getattr(user, "status", "active") or "").lower() != "active":
        raise HTTPException(status_code=403, detail="Account disabled. Contact admin.")

    # lockout check
    if _is_locked(user):
        raise HTTPException(status_code=423, detail="Account temporarily locked. Try again later.")

    # password check
    if not verify_password(body.password, user.hashed_password):
        # increment failed count
        user.failed_login_count = int(getattr(user, "failed_login_count", 0) or 0) + 1

        # apply lockout if threshold reached
        if user.failed_login_count >= MAX_FAILED:
            user.locked_until = _now_utc() + timedelta(minutes=LOCKOUT_MINUTES)

        db.add(user)
        db.commit()

        raise HTTPException(status_code=401, detail="Invalid email or password.")

    # success: reset lock counters
    user.failed_login_count = 0
    user.locked_until = None
    db.add(user)
    db.commit()

    # Tenant active check (only tenant-scoped users except developer)
    if getattr(user, "tenant_id", None) is not None and (user.role or "").lower() != "developer":
        t = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
        if not t or not t.is_active:
            raise HTTPException(status_code=403, detail="Tenant disabled. Contact support.")

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
    # Verify current password (works for temp password flow too)
    if not verify_password(body.current_password, me.hashed_password):
        raise HTTPException(status_code=401, detail="Current password is incorrect.")

    new_pw = _validate_new_password(body.new_password)

    # Don’t allow same password
    if verify_password(new_pw, me.hashed_password):
        raise HTTPException(status_code=400, detail="New password must be different.")

    me.hashed_password = get_password_hash(new_pw)
    me.must_change_password = False
    me.password_changed_at = _now_utc()

    # clear temp + lockout state
    me.temp_password_issued_at = None
    me.failed_login_count = 0
    me.locked_until = None

    db.add(me)
    db.commit()

    return {"ok": True}
