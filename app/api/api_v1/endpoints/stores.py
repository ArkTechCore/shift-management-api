from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.store import Store
from app.models.membership import StoreMembership
from app.schemas.store import StoreCreate, StoreOut  # keep your existing schemas

router = APIRouter()


@router.get("", response_model=list[StoreOut])
def list_stores(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    return (
        db.query(Store)
        .filter(Store.is_active == True)
        .order_by(Store.name.asc())
        .all()
    )


@router.get("/me", response_model=list[StoreOut])
def my_stores(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Admin can see all stores (active)
    if user.role == "admin":
        return (
            db.query(Store)
            .filter(Store.is_active == True)
            .order_by(Store.name.asc())
            .all()
        )

    # Manager/Employee: stores based on active memberships
    store_ids = (
        db.query(StoreMembership.store_id)
        .filter(
            StoreMembership.user_id == user.id,
            StoreMembership.is_active == True,
        )
        .all()
    )
    store_ids = [row[0] for row in store_ids]

    if not store_ids:
        return []

    return (
        db.query(Store)
        .filter(Store.id.in_(store_ids), Store.is_active == True)
        .order_by(Store.name.asc())
        .all()
    )


@router.post("", response_model=StoreOut, status_code=201)
def create_store(
    data: StoreCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    existing = db.query(Store).filter(Store.code == data.code).first()
    if existing:
        # If store exists but inactive, re-activate it
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return existing

    st = Store(
        code=data.code,
        name=data.name,
        timezone=data.timezone,
        geofence_lat=data.geofence_lat,
        geofence_lng=data.geofence_lng,
        geofence_radius_m=data.geofence_radius_m,
        is_active=True,
    )
    db.add(st)
    db.commit()
    db.refresh(st)
    return st


@router.delete("/{store_id}", status_code=200)
def delete_store(
    store_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    st = db.query(Store).filter(Store.id == store_id).first()
    if not st:
        raise HTTPException(status_code=404, detail="Store not found")

    st.is_active = False
    db.commit()
    return {"ok": True, "store_id": store_id}
