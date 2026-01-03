from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.geofence import inside_geofence
from app.core.access_employee import require_employee_store_membership

from app.models.store import Store
from app.models.timeentry import TimeEntry
from app.models.user import User
from app.models.week import Week
from app.services.week_service import get_week_start, get_week_end

from app.schemas.timeclock import (
    TimeEntryOut,
    ClockInRequest,
    ClockOutRequest,
    OutOfZonePingRequest,
)

router = APIRouter()


def _get_or_create_current_week(db: Session) -> Week:
    today = date.today()
    week_start = get_week_start(today)
    week_end = get_week_end(week_start)

    wk = db.query(Week).filter(Week.week_start == week_start).first()
    if wk:
        return wk

    wk = Week(week_start=week_start, week_end=week_end, is_locked=False, locked_at=None)
    db.add(wk)
    db.commit()
    db.refresh(wk)
    return wk


@router.post("/clock-in", response_model=TimeEntryOut)
def clock_in(
    data: ClockInRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "employee":
        raise HTTPException(status_code=403, detail="Employees only")

    require_employee_store_membership(db, current_user, str(data.store_id))

    store = db.query(Store).filter(Store.id == data.store_id, Store.is_active.is_(True)).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    if not inside_geofence(data.lat, data.lng, store.geofence_lat, store.geofence_lng, store.geofence_radius_m):
        raise HTTPException(status_code=403, detail="You must be at the store to clock in")

    open_entry = (
        db.query(TimeEntry)
        .filter(TimeEntry.employee_id == current_user.id, TimeEntry.clock_out_at.is_(None))
        .first()
    )
    if open_entry:
        raise HTTPException(status_code=400, detail="Already clocked in")

    wk = _get_or_create_current_week(db)

    entry = TimeEntry(
        store_id=store.id,
        employee_id=current_user.id,
        week_id=wk.id,
        clock_in_at=datetime.utcnow(),
        clock_out_at=None,
        out_of_zone_seconds=0,
        is_out_of_zone=False,
        created_at=datetime.utcnow(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.post("/clock-out", response_model=TimeEntryOut)
def clock_out(
    data: ClockOutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "employee":
        raise HTTPException(status_code=403, detail="Employees only")

    entry = (
        db.query(TimeEntry)
        .filter(TimeEntry.id == data.time_entry_id, TimeEntry.employee_id == current_user.id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")

    if entry.clock_out_at is not None:
        raise HTTPException(status_code=400, detail="Already clocked out")

    store = db.query(Store).filter(Store.id == entry.store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    if not inside_geofence(data.lat, data.lng, store.geofence_lat, store.geofence_lng, store.geofence_radius_m):
        raise HTTPException(status_code=403, detail="You must be at the store to clock out")

    entry.clock_out_at = datetime.utcnow()
    entry.is_out_of_zone = False
    db.commit()
    db.refresh(entry)
    return entry


@router.post("/out-of-zone-ping", response_model=TimeEntryOut)
def out_of_zone_ping(
    data: OutOfZonePingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = (
        db.query(TimeEntry)
        .filter(TimeEntry.id == data.time_entry_id, TimeEntry.employee_id == current_user.id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")

    if entry.clock_out_at is not None:
        raise HTTPException(status_code=400, detail="Shift already ended")

    if data.is_out_of_zone:
        entry.out_of_zone_seconds += data.seconds_since_last_ping
        entry.is_out_of_zone = True
    else:
        entry.is_out_of_zone = False

    db.commit()
    db.refresh(entry)
    return entry
