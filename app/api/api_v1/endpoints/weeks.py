from datetime import date, datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.week import Week
from app.models.user import User
from app.services.week_service import get_week_start, get_week_end

router = APIRouter()


@router.get("/current")
def get_current_week(db: Session = Depends(get_db)):
    today = date.today()
    week_start = get_week_start(today)
    week_end = get_week_end(week_start)

    wk = db.query(Week).filter(Week.week_start == week_start).first()
    if not wk:
        wk = Week(week_start=week_start, week_end=week_end, is_locked=False, locked_at=None)
        db.add(wk)
        db.commit()
        db.refresh(wk)

    return {
        "id": str(wk.id),
        "week_start": wk.week_start,
        "week_end": wk.week_end,
        "is_locked": wk.is_locked,
        "locked_at": wk.locked_at,
    }


def _to_uuid(val: str) -> uuid.UUID:
    try:
        return uuid.UUID(val)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {val}")


@router.post("/{week_id}/lock")
def lock_week(
    week_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role not in ("manager", "admin"):
        raise HTTPException(status_code=403, detail="Managers/Admin only")

    wid = _to_uuid(week_id)
    wk = db.query(Week).filter(Week.id == wid).first()
    if not wk:
        raise HTTPException(status_code=404, detail="Week not found")

    if wk.is_locked:
        return {"id": str(wk.id), "is_locked": wk.is_locked, "locked_at": wk.locked_at}

    wk.is_locked = True
    wk.locked_at = datetime.utcnow()
    db.commit()
    db.refresh(wk)

    return {"id": str(wk.id), "is_locked": wk.is_locked, "locked_at": wk.locked_at}


@router.post("/{week_id}/unlock")
def unlock_week(
    week_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role not in ("manager", "admin"):
        raise HTTPException(status_code=403, detail="Managers/Admin only")

    wid = _to_uuid(week_id)
    wk = db.query(Week).filter(Week.id == wid).first()
    if not wk:
        raise HTTPException(status_code=404, detail="Week not found")

    if not wk.is_locked:
        return {"id": str(wk.id), "is_locked": wk.is_locked, "locked_at": wk.locked_at}

    wk.is_locked = False
    wk.locked_at = None
    db.commit()
    db.refresh(wk)

    return {"id": str(wk.id), "is_locked": wk.is_locked, "locked_at": wk.locked_at}
