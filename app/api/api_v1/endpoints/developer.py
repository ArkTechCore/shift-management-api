from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.deps import get_db, get_current_user
from app.core.security import get_password_hash
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.tenant import TenantCreate, TenantOut, TenantUpdate
from pydantic import BaseModel, EmailStr

router = APIRouter()


def _require_developer(user):
    role = (getattr(user, "role", "") or "").lower()
    if role != "developer":
        raise HTTPException(status_code=403, detail="Developer access required.")


class _CreateTenantAdminBody(BaseModel):
    email: EmailStr
    temp_password: str
    name: str | None = None
    phone: str | None = None


@router.get("/tenants", response_model=list[TenantOut])
def list_tenants(db: Session = Depends(get_db), me=Depends(get_current_user)):
    _require_developer(me)
    return db.query(Tenant).order_by(Tenant.name.asc()).all()


@router.post("/tenants", response_model=TenantOut)
def create_tenant(body: TenantCreate, db: Session = Depends(get_db), me=Depends(get_current_user)):
    _require_developer(me)

    code = body.code.strip().lower()
    if not code:
        raise HTTPException(status_code=400, detail="Tenant code required.")

    exists = db.query(Tenant).filter(Tenant.code == code).first()
    if exists:
        raise HTTPException(status_code=409, detail="Tenant code already exists.")

    t = Tenant(
        code=code,
        name=body.name.strip(),
        plan=body.plan,
        billing_cycle=body.billing_cycle,
        max_stores=body.max_stores,
        feature_payroll=body.feature_payroll,
        feature_timeclock=body.feature_timeclock,
        feature_scheduling=body.feature_scheduling,
        feature_ai=body.feature_ai,
        is_active=True,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.patch("/tenants/{tenant_id}", response_model=TenantOut)
def update_tenant(tenant_id: str, body: TenantUpdate, db: Session = Depends(get_db), me=Depends(get_current_user)):
    _require_developer(me)

    t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found.")

    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(t, k, v)

    db.commit()
    db.refresh(t)
    return t


@router.post("/tenants/{tenant_id}/disable", response_model=TenantOut)
def disable_tenant(tenant_id: str, db: Session = Depends(get_db), me=Depends(get_current_user)):
    _require_developer(me)
    t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found.")
    t.is_active = False
    db.commit()
    db.refresh(t)
    return t


@router.post("/tenants/{tenant_id}/enable", response_model=TenantOut)
def enable_tenant(tenant_id: str, db: Session = Depends(get_db), me=Depends(get_current_user)):
    _require_developer(me)
    t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found.")
    t.is_active = True
    db.commit()
    db.refresh(t)
    return t


@router.post("/tenants/{tenant_id}/create-admin")
def create_tenant_admin(
    tenant_id: str,
    body: _CreateTenantAdminBody,
    db: Session = Depends(get_db),
    me=Depends(get_current_user),
):
    """
    Developer creates the first tenant_admin for a tenant with a TEMP password.
    Tenant admin will be forced to change password on first login.
    """
    _require_developer(me)

    t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found.")
    if not t.is_active:
        raise HTTPException(status_code=403, detail="Tenant is disabled.")

    email = body.email.strip().lower()
    exists = db.query(User).filter(User.email == email).first()
    if exists:
        raise HTTPException(status_code=409, detail="Email already exists.")

    u = User(
        tenant_id=t.id,
        email=email,
        role="tenant_admin",
        hashed_password=get_password_hash(body.temp_password),
        name=body.name,
        phone=body.phone,
        status="active",
        must_change_password=True,
        temp_password_issued_at=func.now(),
    )
    db.add(u)
    db.commit()
    db.refresh(u)

    return {
        "ok": True,
        "tenant_id": str(t.id),
        "user_id": str(u.id),
        "email": u.email,
        "role": u.role,
        "must_change_password": True,
    }
