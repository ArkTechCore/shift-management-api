from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user, require_role
from app.models.availability import Availability
from app.models.user import User
from app.schemas.availability import AvailabilityUpsert, AvailabilityOut

router = APIRouter()


@router.get("/me", response_model=list[AvailabilityOut])
def my_availability(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Availability).filter(Availability.employee_id == user.id).all()


@router.post("/me", response_model=AvailabilityOut)
def upsert_my_availability(
    data: AvailabilityUpsert,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != "employee":
        raise HTTPException(status_code=403, detail="Employees only")

    row = (
        db.query(Availability)
        .filter(
            Availability.employee_id == user.id,
            Availability.store_id == data.store_id,
            Availability.week_id == data.week_id,
            Availability.day == data.day,
        )
        .first()
    )

    if not row:
        row = Availability(
            employee_id=user.id,
            store_id=data.store_id,
            week_id=data.week_id,
            day=data.day,
        )
        db.add(row)

    row.available_start_at = data.available_start_at
    row.available_end_at = data.available_end_at

    db.commit()
    db.refresh(row)
    return row


@router.get("/store/{store_id}", response_model=list[AvailabilityOut])
def store_availability(
    store_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("admin", "manager")),
):
    return db.query(Availability).filter(Availability.store_id == store_id).all()
