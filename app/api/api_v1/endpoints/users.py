from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, ResetPasswordOut

router = APIRouter()


def _role(me) -> str:
    return (getattr(me, "role", "") or "").lower()


def _is_developer(me) -> bool:
    return _role(me) == "developer"


def _is_tenant_admin(me) -> bool:
    return _role(me) == "tenant_admin"


def _is_manager(me) -> bool:
    return _role(me) == "manager"


def _is_admin_like(me) -> bool:
    return _is_tenant_admin(me) or _is_manager(me)


def _require_tenant_scoped(me):
    # developer is NOT tenant-scoped
    if _is_developer(me):
        raise HTTPException(status_code=403, detail="Developer cannot access tenant users here.")
    if getattr(me, "tenant_id", None) is None:
        raise HTTPException(status_code=403, detail="Tenant context missing.")


def _gen_temp_password(length: int = 12) -> str:
    import secrets

    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789@#"
    return "".join(secrets.choice(alphabet) for _ in range(length))


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), me=Depends(get_current_user)):
    _require_tenant_scoped(me)

    users = (
        db.query(User)
        .filter(User.tenant_id == me.tenant_id)
        .order_by(User.email.asc())
        .all()
    )
    return users


@router.post("", response_model=UserOut)
def create_user(body: UserCreate, db: Session = Depends(get_db), me=Depends(get_current_user)):
    _require_tenant_scoped(me)

    # only tenant_admin can create users (manager cannot)
    if not _is_tenant_admin(me):
        raise HTTPException(status_code=403, detail="Tenant admin access required.")

    email = body.email.strip().lower()
    exists = db.query(User).filter(User.email == email).first()
    if exists:
        raise HTTPException(status_code=409, detail="Email already exists.")

    role = (body.role or "employee").lower()
    if role not in ["tenant_admin", "manager", "employee"]:
        raise HTTPException(status_code=400, detail="Invalid role.")

    u = User(
        email=email,
        role=role,
        tenant_id=me.tenant_id,
        name=(getattr(body, "name", None) or getattr(body, "full_name", None)),
        full_name=(getattr(body, "full_name", None) or getattr(body, "name", None)),

        
        phone=getattr(body, "phone", None),
        hashed_password=get_password_hash(body.password),
        status="active",
        is_active=True,
        must_change_password=bool(getattr(body, "must_change_password", False)),
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@router.post("/{user_id}/reset-password", response_model=ResetPasswordOut)
def reset_password(user_id: str, db: Session = Depends(get_db), me=Depends(get_current_user)):
    _require_tenant_scoped(me)

    # tenant_admin OR manager can reset passwords
    if not _is_admin_like(me):
        raise HTTPException(status_code=403, detail="Manager/Admin access required.")

    u = (
        db.query(User)
        .filter(User.id == user_id, User.tenant_id == me.tenant_id)
        .first()
    )
    if not u:
        raise HTTPException(status_code=404, detail="User not found.")

    # never allow resetting developer accounts from tenant context
    if (u.role or "").lower() == "developer":
        raise HTTPException(status_code=403, detail="Cannot reset developer account.")

    temp_pw = _gen_temp_password()

    u.hashed_password = get_password_hash(temp_pw)
    u.must_change_password = True

    # optional security columns exist in your DB
    if hasattr(u, "temp_password_issued_at"):
        from sqlalchemy import func
        u.temp_password_issued_at = func.now()

    if hasattr(u, "failed_login_count"):
        u.failed_login_count = 0
    if hasattr(u, "locked_until"):
        u.locked_until = None

    db.add(u)
    db.commit()

    return ResetPasswordOut(
        user_id=str(u.id),
        email=u.email,
        temp_password=temp_pw,
        must_change_password=True,
    )


@router.delete("/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db), me=Depends(get_current_user)):
    _require_tenant_scoped(me)

    # only tenant_admin can delete users
    if not _is_tenant_admin(me):
        raise HTTPException(status_code=403, detail="Tenant admin access required.")

    u = (
        db.query(User)
        .filter(User.id == user_id, User.tenant_id == me.tenant_id)
        .first()
    )
    if not u:
        raise HTTPException(status_code=404, detail="User not found.")

    db.delete(u)
    db.commit()
    return {"ok": True}
