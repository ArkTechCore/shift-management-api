import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_db, get_current_user
from app.core.access import require_store_access
from app.models.user import User
from app.models.schedule import Schedule, Shift, ShiftAssignment
from app.models.week import Week
from app.schemas.schedule import (
    ScheduleOut,
    ShiftOut,
    ShiftCreateRequest,
    ShiftAssignRequest,
    ShiftAssignmentOut,
    PublishScheduleRequest,
)

router = APIRouter()


@router.get("/ping")
def ping():
    return {"ok": True, "msg": "schedules endpoint alive"}


def _to_uuid(val: str) -> uuid.UUID:
    try:
        return uuid.UUID(val)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {val}")


def _ensure_week_not_locked(db: Session, week_id: uuid.UUID):
    w = db.query(Week).filter(Week.id == week_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Week not found")
    if w.is_locked:
        raise HTTPException(status_code=400, detail="Week is locked. Schedule cannot be edited.")


def _get_schedule_or_404(db: Session, schedule_id: str) -> Schedule:
    sid = _to_uuid(schedule_id)
    s = (
        db.query(Schedule)
        .options(selectinload(Schedule.shifts).selectinload(Shift.assignments))
        .filter(Schedule.id == sid)
        .first()
    )
    if not s:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return s


@router.get("/{store_id}/{week_id}", response_model=ScheduleOut)
def get_schedule(
    store_id: str,
    week_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_store_access(db, user, store_id)

    schedule = (
        db.query(Schedule)
        .options(selectinload(Schedule.shifts).selectinload(Shift.assignments))
        .filter(
            Schedule.store_id == _to_uuid(store_id),
            Schedule.week_id == _to_uuid(week_id),
        )
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return schedule


@router.post("/{store_id}/{week_id}", response_model=ScheduleOut, status_code=201)
def create_schedule(
    store_id: str,
    week_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_store_access(db, user, store_id)

    store_uuid = _to_uuid(store_id)
    week_uuid = _to_uuid(week_id)

    _ensure_week_not_locked(db, week_uuid)

    existing = (
        db.query(Schedule)
        .filter(Schedule.store_id == store_uuid, Schedule.week_id == week_uuid)
        .first()
    )
    if existing:
        return existing

    schedule = Schedule(store_id=store_uuid, week_id=week_uuid, is_published=False)
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.post("/{schedule_id}/shifts", response_model=ShiftOut, status_code=201)
def add_shift(
    schedule_id: str,
    data: ShiftCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    schedule = _get_schedule_or_404(db, schedule_id)
    require_store_access(db, user, str(schedule.store_id))

    _ensure_week_not_locked(db, schedule.week_id)

    if schedule.is_published:
        raise HTTPException(status_code=400, detail="Schedule is published. Unpublish to edit.")

    if data.end_at <= data.start_at:
        raise HTTPException(status_code=400, detail="end_at must be after start_at")

    shift = Shift(
        schedule_id=schedule.id,
        role=data.role,
        start_at=data.start_at,
        end_at=data.end_at,
        headcount_required=data.headcount_required,
    )
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift


@router.post("/shifts/{shift_id}/assign", response_model=ShiftAssignmentOut, status_code=201)
def assign_employee(
    shift_id: str,
    data: ShiftAssignRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    shift_uuid = _to_uuid(shift_id)

    shift = (
        db.query(Shift)
        .options(selectinload(Shift.assignments))
        .filter(Shift.id == shift_uuid)
        .first()
    )
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")

    schedule = db.query(Schedule).filter(Schedule.id == shift.schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    require_store_access(db, user, str(schedule.store_id))
    _ensure_week_not_locked(db, schedule.week_id)

    if schedule.is_published:
        raise HTTPException(status_code=400, detail="Schedule is published. Unpublish to edit.")

    if any(a.employee_id == data.employee_id for a in shift.assignments):
        raise HTTPException(status_code=400, detail="Employee already assigned to this shift")

    if len(shift.assignments) >= shift.headcount_required:
        raise HTTPException(status_code=400, detail="Shift is already full")

    assignment = ShiftAssignment(shift_id=shift.id, employee_id=data.employee_id)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.delete("/assignments/{assignment_id}", status_code=204)
def unassign_employee(
    assignment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    aid = _to_uuid(assignment_id)

    a = db.query(ShiftAssignment).filter(ShiftAssignment.id == aid).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assignment not found")

    shift = db.query(Shift).filter(Shift.id == a.shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")

    schedule = db.query(Schedule).filter(Schedule.id == shift.schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    require_store_access(db, user, str(schedule.store_id))
    _ensure_week_not_locked(db, schedule.week_id)

    if schedule.is_published:
        raise HTTPException(status_code=400, detail="Schedule is published. Unpublish to edit.")

    db.delete(a)
    db.commit()
    return None


@router.post("/{schedule_id}/publish", response_model=ScheduleOut)
def set_published(
    schedule_id: str,
    data: PublishScheduleRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    schedule = _get_schedule_or_404(db, schedule_id)
    require_store_access(db, user, str(schedule.store_id))
    _ensure_week_not_locked(db, schedule.week_id)

    schedule.is_published = data.is_published
    db.commit()
    db.refresh(schedule)
    return schedule
