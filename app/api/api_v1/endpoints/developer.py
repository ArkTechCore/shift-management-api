from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.deps import get_db, get_current_user
from app.core.security import get_password_hash
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.tenant import TenantCreate, TenantOut, TenantUpdate
from pydantic import BaseModel, EmailStr
from app.models.store import Store
from app.models.schedule import Schedule
from app.models.timeentry import TimeEntry
from app.models.payroll_invoice import PayrollInvoice
from app.schemas.developer_insights import TenantInsightsOut

import secrets
import string

router = APIRouter()


def _require_developer(user):
    role = (getattr(user, "role", "") or "").lower()
    if role != "developer":
        raise HTTPException(status_code=403, detail="Developer access required.")


def _gen_temp_password(length: int = 12) -> str:
    # easy to type, strong enough for temp use
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _validate_temp_password(pw: str) -> str:
    pw = (pw or "").strip()
    if len(pw) < 8:
        raise HTTPException(status_code=400, detail="Temp password must be at least 8 characters.")
    return pw


class _CreateTenantAdminBody(BaseModel):
    email: EmailStr
    # optional: if not provided, backend generates it
    temp_password: str | None = None
    name: str | None = None
    phone: str | None = None


class _CreateTenantAdminOut(BaseModel):
    ok: bool
    tenant_id: str
    user_id: str
    email: str
    role: str
    must_change_password: bool
    temp_password: str


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


@router.post("/tenants/{tenant_id}/create-admin", response_model=_CreateTenantAdminOut)
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

    # Optional rule: allow only ONE tenant admin created via developer endpoint
    # Comment this block if you want multiple.
    existing_admin = (
        db.query(User)
        .filter(User.tenant_id == t.id, User.role == "tenant_admin")
        .first()
    )
    if existing_admin:
        raise HTTPException(status_code=409, detail="Tenant admin already exists for this tenant.")

    email = body.email.strip().lower()
    exists = db.query(User).filter(User.email == email).first()
    if exists:
        raise HTTPException(status_code=409, detail="Email already exists.")

    temp_pw = body.temp_password.strip() if body.temp_password else _gen_temp_password()
    temp_pw = _validate_temp_password(temp_pw)

    u = User(
        tenant_id=t.id,
        email=email,
        role="tenant_admin",
        hashed_password=get_password_hash(temp_pw),
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
        "temp_password": temp_pw,  # returned ONE TIME to developer
    }

@router.get("/tenants/{tenant_id}/insights", response_model=TenantInsightsOut)
def tenant_insights(
    tenant_id: str,
    db: Session = Depends(get_db),
    me=Depends(get_current_user),
):
    _require_developer(me)

    t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found.")

    stores_count = db.query(func.count(Store.id)).filter(Store.tenant_id == t.id).scalar() or 0

    users_count = db.query(func.count(User.id)).filter(User.tenant_id == t.id).scalar() or 0
    active_users_count = (
        db.query(func.count(User.id))
        .filter(User.tenant_id == t.id, func.lower(User.status) == "active")
        .scalar()
        or 0
    )

    managers_count = (
        db.query(func.count(User.id))
        .filter(User.tenant_id == t.id, func.lower(User.role) == "manager")
        .scalar()
        or 0
    )
    employees_count = (
        db.query(func.count(User.id))
        .filter(User.tenant_id == t.id, func.lower(User.role) == "employee")
        .scalar()
        or 0
    )

    schedules_count = db.query(func.count(Schedule.id)).filter(Schedule.tenant_id == t.id).scalar() or 0
    published_schedules_count = (
        db.query(func.count(Schedule.id))
        .filter(Schedule.tenant_id == t.id, Schedule.published == True)  # noqa: E712
        .scalar()
        or 0
    )

    open_time_entries_count = (
        db.query(func.count(TimeEntry.id))
        .filter(TimeEntry.tenant_id == t.id, TimeEntry.clock_out_at.is_(None))
        .scalar()
        or 0
    )

    invoices_count = (
        db.query(func.count(PayrollInvoice.id))
        .filter(PayrollInvoice.tenant_id == t.id)
        .scalar()
        or 0
    )

    return TenantInsightsOut(
        tenant_id=t.id,
        tenant_code=t.code,
        tenant_name=t.name,
        is_active=bool(t.is_active),

        stores_count=int(stores_count),
        users_count=int(users_count),
        active_users_count=int(active_users_count),
        managers_count=int(managers_count),
        employees_count=int(employees_count),

        schedules_count=int(schedules_count),
        published_schedules_count=int(published_schedules_count),

        open_time_entries_count=int(open_time_entries_count),
        invoices_count=int(invoices_count),
    )


@router.get("/tenants/insights", response_model=list[TenantInsightsOut])
def tenants_insights(
    db: Session = Depends(get_db),
    me=Depends(get_current_user),
):
    _require_developer(me)

    tenants = db.query(Tenant).order_by(Tenant.name.asc()).all()
    out: list[TenantInsightsOut] = []

    for t in tenants:
        stores_count = db.query(func.count(Store.id)).filter(Store.tenant_id == t.id).scalar() or 0

        users_count = db.query(func.count(User.id)).filter(User.tenant_id == t.id).scalar() or 0
        active_users_count = (
            db.query(func.count(User.id))
            .filter(User.tenant_id == t.id, func.lower(User.status) == "active")
            .scalar()
            or 0
        )

        managers_count = (
            db.query(func.count(User.id))
            .filter(User.tenant_id == t.id, func.lower(User.role) == "manager")
            .scalar()
            or 0
        )
        employees_count = (
            db.query(func.count(User.id))
            .filter(User.tenant_id == t.id, func.lower(User.role) == "employee")
            .scalar()
            or 0
        )

        schedules_count = db.query(func.count(Schedule.id)).filter(Schedule.tenant_id == t.id).scalar() or 0
        published_schedules_count = (
            db.query(func.count(Schedule.id))
            .filter(Schedule.tenant_id == t.id, Schedule.published == True)  # noqa: E712
            .scalar()
            or 0
        )

        open_time_entries_count = (
            db.query(func.count(TimeEntry.id))
            .filter(TimeEntry.tenant_id == t.id, TimeEntry.clock_out_at.is_(None))
            .scalar()
            or 0
        )

        invoices_count = (
            db.query(func.count(PayrollInvoice.id))
            .filter(PayrollInvoice.tenant_id == t.id)
            .scalar()
            or 0
        )

        out.append(
            TenantInsightsOut(
                tenant_id=t.id,
                tenant_code=t.code,
                tenant_name=t.name,
                is_active=bool(t.is_active),

                stores_count=int(stores_count),
                users_count=int(users_count),
                active_users_count=int(active_users_count),
                managers_count=int(managers_count),
                employees_count=int(employees_count),

                schedules_count=int(schedules_count),
                published_schedules_count=int(published_schedules_count),

                open_time_entries_count=int(open_time_entries_count),
                invoices_count=int(invoices_count),
            )
        )

    return out

