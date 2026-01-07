from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.store import Store
from app.models.tenant import Tenant
from app.schemas.store import StoreCreate, StoreOut

router = APIRouter()


def _is_developer(me) -> bool:
    return (getattr(me, "role", "") or "").lower() == "developer"


def _require_tenant_scoped(me):
    if _is_developer(me):
        # developer doesn't manage stores directly (privacy boundary)
        raise HTTPException(status_code=403, detail="Developer cannot access tenant stores.")
    if getattr(me, "tenant_id", None) is None:
        raise HTTPException(status_code=403, detail="Tenant context missing.")


def _require_tenant_active(db: Session, me):
    t = db.query(Tenant).filter(Tenant.id == me.tenant_id).first()
    if not t or not t.is_active:
        raise HTTPException(status_code=403, detail="Tenant disabled. Contact support.")
    return t


@router.get("", response_model=list[StoreOut])
def list_stores(db: Session = Depends(get_db), me=Depends(get_current_user)):
    _require_tenant_scoped(me)
    _require_tenant_active(db, me)

    items = (
        db.query(Store)
        .filter(Store.tenant_id == me.tenant_id)
        .order_by(Store.code.asc())
        .all()
    )
    return items


@router.get("/me", response_model=list[StoreOut])
def my_stores(db: Session = Depends(get_db), me=Depends(get_current_user)):
    _require_tenant_scoped(me)
    _require_tenant_active(db, me)

    items = (
        db.query(Store)
        .filter(Store.tenant_id == me.tenant_id)
        .order_by(Store.code.asc())
        .all()
    )
    return items


@router.post("", response_model=StoreOut)
def create_store(body: StoreCreate, db: Session = Depends(get_db), me=Depends(get_current_user)):
    _require_tenant_scoped(me)
    t = _require_tenant_active(db, me)

    code = (body.code or "").strip()
    if not code:
        raise HTTPException(status_code=400, detail="Store code required.")

    name = (body.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Store name required.")

    # ✅ PLAN LIMIT: max stores (store-based limit, not user-based)
    max_stores = int(getattr(t, "max_stores", 0) or 0)
    if max_stores > 0:
        current = db.query(Store).filter(Store.tenant_id == me.tenant_id).count()
        if current >= max_stores:
            raise HTTPException(
                status_code=403,
                detail=f"Plan limit reached: max {max_stores} stores. Upgrade plan to add more stores.",
            )

    # ✅ uniqueness per tenant
    exists = db.query(Store).filter(Store.tenant_id == me.tenant_id, Store.code == code).first()
    if exists:
        raise HTTPException(status_code=409, detail="Store code already exists in this tenant.")

    s = Store(
        tenant_id=me.tenant_id,
        code=code,
        name=name,
        timezone=getattr(body, "timezone", None) or "America/New_York",
        geofence_lat=getattr(body, "geofence_lat", None),
        geofence_lng=getattr(body, "geofence_lng", None),
        geofence_radius_m=getattr(body, "geofence_radius_m", None) or 150,
        is_active=True,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.delete("/{store_id}")
def delete_store(store_id: str, db: Session = Depends(get_db), me=Depends(get_current_user)):
    _require_tenant_scoped(me)
    _require_tenant_active(db, me)

    s = db.query(Store).filter(Store.id == store_id, Store.tenant_id == me.tenant_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Store not found.")

    db.delete(s)
    db.commit()
    return {"ok": True}
