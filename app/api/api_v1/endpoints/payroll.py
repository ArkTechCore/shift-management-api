from datetime import datetime, date, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.store import Store
from app.models.timeentry import TimeEntry
from app.models.week import Week
from app.schemas.payroll import StoreWeekPayrollSummary, EmployeePayrollLine

router = APIRouter()


@router.get("/stores/{store_id}/week/{week_start}/summary", response_model=StoreWeekPayrollSummary)
def store_week_payroll_summary(
    store_id: str,
    week_start: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("manager", "admin"):
        raise HTTPException(status_code=403, detail="Managers/Admin only")

    store = db.query(Store).filter(Store.id == store_id, Store.is_active == True).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    wk = db.query(Week).filter(Week.week_start == week_start).first()
    if not wk:
        raise HTTPException(status_code=404, detail="Week not found")

    start_dt = datetime.combine(wk.week_start, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = datetime.combine(wk.week_end, datetime.max.time(), tzinfo=timezone.utc)

    # Total minutes per employee (clock_out_at NULL rows count as open_entries, not included in minutes)
    # minutes = EXTRACT(EPOCH FROM (clock_out - clock_in))/60
    total_minutes_expr = func.coalesce(
        func.sum(
            case(
                (TimeEntry.clock_out_at.isnot(None),
                 func.floor(func.extract("epoch", (TimeEntry.clock_out_at - TimeEntry.clock_in_at)) / 60)),
                else_=0
            )
        ),
        0
    ).label("total_minutes")

    out_of_zone_expr = func.coalesce(func.sum(TimeEntry.out_of_zone_seconds), 0).label("out_of_zone_seconds")

    open_entries_expr = func.coalesce(
        func.sum(case((TimeEntry.clock_out_at.is_(None), 1), else_=0)),
        0
    ).label("open_entries")

    rows = (
        db.query(
            TimeEntry.employee_id.label("employee_id"),
            total_minutes_expr,
            out_of_zone_expr,
            open_entries_expr,
        )
        .filter(
            TimeEntry.store_id == store.id,
            TimeEntry.clock_in_at >= start_dt,
            TimeEntry.clock_in_at <= end_dt,
        )
        .group_by(TimeEntry.employee_id)
        .order_by(TimeEntry.employee_id.asc())
        .all()
    )

    lines = [
        EmployeePayrollLine(
            employee_id=r.employee_id,
            total_minutes=int(r.total_minutes),
            out_of_zone_seconds=int(r.out_of_zone_seconds),
            open_entries=int(r.open_entries),
        )
        for r in rows
    ]

    return StoreWeekPayrollSummary(
        store_id=store.id,
        week_start=wk.week_start.isoformat(),
        week_end=wk.week_end.isoformat(),
        lines=lines,
    )
