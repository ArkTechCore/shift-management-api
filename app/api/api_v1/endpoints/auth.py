from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.security import verify_password, create_access_token, get_password_hash
from app.models.user import User
from app.models.tenant import Tenant
from app.schemas.auth import LoginRequest, TokenResponse, ChangePasswordRequest

router = APIRouter()


def _now_utc():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)


def _validate_new_password(pw: str):
    pw = (pw or "").strip()
    if len(pw) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    return pw


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if (getattr(user, "status", "active") or "").lower() != "active":
        raise HTTPException(status_code=403, detail="Account disabled. Contact admin.")

    if getattr(user, "locked_until", None) is not None:
        # (optional) implement locked_until check later
        pass

    if not verify_password(body.password, user.hashed_password):
        # (optional) increment failed counts later
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    # Tenant active check (only for tenant-scoped users)
    if getattr(user, "tenant_id", None) is not None and (user.role or "").lower() != "developer":
        t = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
        if not t or not t.is_active:
            raise HTTPException(status_code=403, detail="Tenant disabled. Contact support.")

    token = create_access_token(
        subject=str(user.id),
        extra_claims={
            "role": user.role,
            "tenant_id": str(user.tenant_id) if getattr(user, "tenant_id", None) else None,
            "email": user.email,
        },
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=user.role,
        must_change_password=bool(getattr(user, "must_change_password", False)),
        tenant_id=str(user.tenant_id) if getattr(user, "tenant_id", None) else None,
        email=user.email,
    )


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    # verify current password (works for normal + temp password flow)
    if not verify_password(body.current_password, me.hashed_password):
        raise HTTPException(status_code=401, detail="Current password is incorrect.")

    new_pw = _validate_new_password(body.new_password)

    # don’t allow same password
    if verify_password(new_pw, me.hashed_password):
        raise HTTPException(status_code=400, detail="New password must be different.")

    me.hashed_password = get_password_hash(new_pw)
    me.must_change_password = False
    me.password_changed_at = _now_utc()

    # clear temp + locks
    me.temp_password_issued_at = None
    me.failed_login_count = 0
    me.locked_until = None

    db.add(me)
    db.commit()

    return {"ok": True}
