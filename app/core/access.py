import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.membership import StoreMembership
from app.models.user import User


def _to_uuid(val):
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {val}")


def require_store_access(db: Session, user: User, store_id):
    store_uuid = _to_uuid(store_id)

    if user.role == "admin":
        return

    if user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Store access requires manager/admin role",
        )

    membership = (
        db.query(StoreMembership)
        .filter(
            StoreMembership.user_id == user.id,
            StoreMembership.store_id == store_uuid,
            StoreMembership.is_active.is_(True),
        )
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this store",
        )
