from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.access import require_store_access
from app.models.user import User
from app.models.membership import StoreMembership
from app.models.store import Store
from app.schemas.membership import MembershipCreate, MembershipOut

router = APIRouter()


@router.post("", response_model=MembershipOut, status_code=201)
def create_membership(
    data: MembershipCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Resolve store_id from store_code if needed
    store_id = data.store_id
    if store_id is None:
        code = (data.store_code or "").strip()
        st = (
            db.query(Store)
            .filter(Store.code == code, Store.is_active == True)
            .first()
        )
        if not st:
            raise HTTPException(status_code=404, detail="Store not found by code")
        store_id = st.id

    # Admin can assign anywhere. Manager only within their store access.
    if user.role != "admin":
        require_store_access(db, user, str(store_id))

    existing = (
        db.query(StoreMembership)
        .filter(
            StoreMembership.user_id == data.user_id,
            StoreMembership.store_id == store_id,
        )
        .first()
    )

    # Enforce pay_rate rules: manager has no pay_rate
    final_pay_rate = "0"
    if data.store_role == "employee":
        final_pay_rate = (data.pay_rate or "0").strip() or "0"

    if existing:
        existing.is_active = True
        existing.store_role = data.store_role
        existing.pay_rate = final_pay_rate
        db.commit()
        db.refresh(existing)
        return existing

    m = StoreMembership(
        user_id=data.user_id,
        store_id=store_id,
        store_role=data.store_role,
        pay_rate=final_pay_rate,
        is_active=True,
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

    return (
        db.query(StoreMembership)
        .filter(
            StoreMembership.store_id == store_id,
            StoreMembership.is_active == True,
        )
        .order_by(StoreMembership.user_id.asc())
        .all()
    )


@router.delete("/{membership_id}", status_code=200)
def delete_membership(
    membership_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    m = db.query(StoreMembership).filter(StoreMembership.id == membership_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Membership not found")

    m.is_active = False
    db.commit()
    return {"ok": True, "membership_id": membership_id}
