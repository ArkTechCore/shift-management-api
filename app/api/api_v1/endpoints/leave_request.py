from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user, require_role
from app.core.access import require_store_access
from app.models.leave_request import LeaveRequest
from app.models.user import User
from app.schemas.leave_request import LeaveRequestCreate, LeaveDecision, LeaveRequestOut

router = APIRouter()


@router.get("/me", response_model=list[LeaveRequestOut])
def my_leave_requests(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(LeaveRequest).filter(LeaveRequest.employee_id == user.id).all()


@router.post("/me", response_model=LeaveRequestOut, status_code=201)
def create_my_leave_request(
    data: LeaveRequestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != "employee":
        raise HTTPException(status_code=403, detail="Employees only")

    if data.end_date < data.start_date:
        raise HTTPException(status_code=400, detail="end_date must be >= start_date")

    lr = LeaveRequest(
        employee_id=user.id,
        store_id=data.store_id,
        start_date=data.start_date,
        end_date=data.end_date,
        reason=data.reason,
        status="pending",
    )
    db.add(lr)
    db.commit()
    db.refresh(lr)
    return lr


@router.get("/store/{store_id}", response_model=list[LeaveRequestOut])
def list_store_leave_requests(
    store_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_store_access(db, user, store_id)
    return db.query(LeaveRequest).filter(LeaveRequest.store_id == store_id).all()


@router.post("/{leave_request_id}/decide", response_model=LeaveRequestOut)
def decide_leave_request(
    leave_request_id: str,
    data: LeaveDecision,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # must be manager/admin for that store
    lr = db.query(LeaveRequest).filter(LeaveRequest.id == leave_request_id).first()
    if not lr:
        raise HTTPException(status_code=404, detail="Leave request not found")

    require_store_access(db, user, str(lr.store_id))

    if lr.status not in ("pending",):
        raise HTTPException(status_code=400, detail="Leave request already decided")

    lr.status = data.status
    lr.decided_by = user.id
    lr.decided_at = datetime.utcnow()

    db.commit()
    db.refresh(lr)
    return lr
