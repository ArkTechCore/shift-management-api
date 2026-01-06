from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.store import Store
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


@router.get("", response_model=list[StoreOut])
def list_stores(db: Session = Depends(get_db), me=Depends(get_current_user)):
    _require_tenant_scoped(me)
    items = db.query(Store).filter(Store.tenant_id == me.tenant_id).order_by(Store.code.asc()).all()
    return items


@router.get("/me", response_model=list[StoreOut])
def my_stores(db: Session = Depends(get_db), me=Depends(get_current_user)):
    _require_tenant_scoped(me)
    items = db.query(Store).filter(Store.tenant_id == me.tenant_id).order_by(Store.code.asc()).all()
    return items


@router.post("", response_model=StoreOut)
def create_store(body: StoreCreate, db: Session = Depends(get_db), me=Depends(get_current_user)):
    _require_tenant_scoped(me)

    code = body.code.strip()
    if not code:
        raise HTTPException(status_code=400, detail="Store code required.")

    # enforce uniqueness per tenant in API (DB might still be global unique)
    exists = db.query(Store).filter(Store.tenant_id == me.tenant_id, Store.code == code).first()
    if exists:
        raise HTTPException(status_code=409, detail="Store code already exists in this tenant.")

    s = Store(
        tenant_id=me.tenant_id,
        code=code,
        name=body.name.strip(),
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

    s = db.query(Store).filter(Store.id == store_id, Store.tenant_id == me.tenant_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Store not found.")

    db.delete(s)
    db.commit()
    return {"ok": True}
