import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.access import require_store_access
from app.models.user import User
from app.models.membership import StoreMembership
from app.schemas.membership import MembershipCreate, MembershipOut

router = APIRouter()


@router.post("", response_model=MembershipOut, status_code=201)
def create_membership(
    data: MembershipCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # admin can assign anywhere, manager only within their store
    if user.role != "admin":
        require_store_access(db, user, str(data.store_id))

    existing = (
        db.query(StoreMembership)
        .filter(
            StoreMembership.user_id == data.user_id,
            StoreMembership.store_id == data.store_id,
        )
        .first()
    )
    if existing:
        return existing

    m = StoreMembership(
        user_id=data.user_id,
        store_id=data.store_id,
        store_role=data.store_role,
        pay_rate=data.pay_rate,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@router.get("/store/{store_id}", response_model=list[MembershipOut])
def list_store_memberships(
    store_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != "admin":
        require_store_access(db, user, store_id)

    return db.query(StoreMembership).filter(StoreMembership.store_id == store_id).all()
