from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.schemas.store import StoreCreate, StoreOut
from app.models.store import Store

from app.core.deps import get_current_user
from app.models.membership import StoreMembership
from app.models.user import User

router = APIRouter()

@router.post("", response_model=StoreOut, dependencies=[Depends(require_role("admin"))])
def create_store(data: StoreCreate, db: Session = Depends(get_db)):
    store = Store(
        code=data.code,
        name=data.name,
        timezone=data.timezone,
        geofence_lat=data.geofence_lat,
        geofence_lng=data.geofence_lng,
        geofence_radius_m=data.geofence_radius_m,
    )
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


@router.get("", response_model=list[StoreOut], dependencies=[Depends(require_role("admin"))])
def list_stores(db: Session = Depends(get_db)):
    return db.query(Store).order_by(Store.name.asc()).all()

@router.get("/me", response_model=list[StoreOut])
def my_stores(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # admin sees all stores
    if user.role == "admin":
        return db.query(Store).order_by(Store.name.asc()).all()

    store_ids = (
        db.query(StoreMembership.store_id)
        .filter(StoreMembership.user_id == user.id)
        .all()
    )
    store_ids = [sid[0] for sid in store_ids]

    if not store_ids:
        return []

    return db.query(Store).filter(Store.id.in_(store_ids)).order_by(Store.name.asc()).all()