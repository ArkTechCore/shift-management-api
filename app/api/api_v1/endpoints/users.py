from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, UserOut

router = APIRouter()


def _is_developer(me) -> bool:
    return (getattr(me, "role", "") or "").lower() == "developer"


def _require_tenant_scoped(me):
    # developer can have tenant_id NULL; tenant users MUST have tenant_id
    if _is_developer(me):
        return
    if getattr(me, "tenant_id", None) is None:
        raise HTTPException(status_code=403, detail="Tenant context missing.")


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    me=Depends(get_current_user),
):
    # Developer: can list users only if you later add tenant filter.
    # For now: block developer from listing tenant users (privacy).
    if _is_developer(me):
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

    # tenant admin controls managers/employees in their tenant
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
