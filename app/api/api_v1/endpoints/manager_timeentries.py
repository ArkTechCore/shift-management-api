from datetime import date
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.access import require_store_access
from app.models.user import User
from app.models.timeentry import TimeEntry
from app.models.week import Week
from app.schemas.timeclock import TimeEntryOut

router = APIRouter()


def _to_uuid(val: str) -> uuid.UUID:
    try:
        return uuid.UUID(val)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {val}")


@router.get("/stores/{store_id}/week/{week_start}/entries", response_model=list[TimeEntryOut])
def list_time_entries_for_store_week(
    store_id: str,
    week_start: date,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role not in ("manager", "admin"):
        raise HTTPException(status_code=403, detail="Managers/Admin only")

    store_uuid = _to_uuid(store_id)
    require_store_access(db, user, store_uuid)

    wk = db.query(Week).filter(Week.week_start == week_start).first()
    if not wk:
        raise HTTPException(status_code=404, detail="Week not found")

    return (
        db.query(TimeEntry)
        .filter(TimeEntry.store_id == store_uuid, TimeEntry.week_id == wk.id)
        .order_by(TimeEntry.clock_in_at.asc())
        .all()
    )


@router.get("/stores/{store_id}/open-entries", response_model=list[TimeEntryOut])
def list_open_entries_for_store(
    store_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role not in ("manager", "admin"):
        raise HTTPException(status_code=403, detail="Managers/Admin only")

    store_uuid = _to_uuid(store_id)
    require_store_access(db, user, store_uuid)

    return (
        db.query(TimeEntry)
        .filter(TimeEntry.store_id == store_uuid, TimeEntry.clock_out_at.is_(None))
        .order_by(TimeEntry.clock_in_at.asc())
        .all()
    )
