from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, ResetPasswordOut

router = APIRouter()


def _is_developer(me) -> bool:
    return (getattr(me, "role", "") or "").lower() == "developer"


def _is_tenant_admin(me) -> bool:
    return (getattr(me, "role", "") or "").lower() == "tenant_admin"


def _require_tenant_scoped(me):
    if _is_developer(me):
        return
    if getattr(me, "tenant_id", None) is None:
        raise HTTPException(status_code=403, detail="Tenant context missing.")


def _now_utc():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)


def _gen_temp_password(length: int = 10) -> str:
    # readable but strong enough; you can change style later
    import secrets
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789@#"
    return "".join(secrets.choice(alphabet) for _ in range(length))


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    me=Depends(get_current_user),
):
    if _is_developer(me):
        # privacy boundary
        raise HTTPException(status_code=403, detail="Developer cannot list tenant users.")

    _require_tenant_scoped(me)

    tenant_id = me.tenant_id
    users = db.query(User).filter(User.tenant_id == tenant_id).order_by(User.email.asc()).all()
    return users


@router.post("", response_model=UserOut)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    me=Depends(get_current_user),
):
    if _is_developer(me):
        raise HTTPException(status_code=403, detail="Developer cannot create tenant users here.")

    _require_tenant_scoped(me)

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
        name=getattr(body, "name", None),
        phone=getattr(body, "phone", None),
        hashed_password=get_password_hash(body.password),
        status="active",
        must_change_password=bool(getattr(body, "must_change_password", False)),
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@router.post("/{user_id}/reset-password", response_model=ResetPasswordOut)
def reset_password(
    user_id: str,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    """
    Admin issues a temp password.
    User MUST change password on next login (must_change_password=true).
    """
    _require_tenant_scoped(me)

    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")

    my_role = (getattr(me, "role", "") or "").lower()
    target_role = (getattr(target, "role", "") or "").lower()

    # ---- Permission rules ----
    if my_role == "developer":
        # Developer can reset only tenant_admin accounts (not managers/employees)
        if target_role != "tenant_admin":
            raise HTTPException(status_code=403, detail="Developer can reset only tenant admin accounts.")
    elif my_role == "tenant_admin":
        # Tenant admin can reset manager/employee only inside their tenant
        if getattr(target, "tenant_id", None) != getattr(me, "tenant_id", None):
            raise HTTPException(status_code=403, detail="Cannot reset user outside your tenant.")
        if target_role not in ["manager", "employee"]:
            raise HTTPException(status_code=403, detail="Tenant admin can reset only manager/employee.")
    else:
        raise HTTPException(status_code=403, detail="Not allowed.")

    # ---- Issue temp password ----
    temp_pw = _gen_temp_password(10)

    target.hashed_password = get_password_hash(temp_pw)
    target.must_change_password = True
    target.temp_password_issued_at = _now_utc()

    # optional: clear lockouts
    target.failed_login_count = 0
    target.locked_until = None

    db.add(target)
    db.commit()

    # IMPORTANT: return temp password ONE time
    return ResetPasswordOut(
        user_id=str(target.id),
        email=target.email,
        temp_password=temp_pw,
        must_change_password=True,
    )


@router.delete("/{user_id}")
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    me=Depends(get_current_user),
):
    if _is_developer(me):
        raise HTTPException(status_code=403, detail="Developer cannot delete tenant users.")

    _require_tenant_scoped(me)

    u = db.query(User).filter(User.id == user_id, User.tenant_id == me.tenant_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found.")

    db.delete(u)
    db.commit()
    return {"ok": True}
