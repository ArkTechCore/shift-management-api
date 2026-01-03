from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserOut

router = APIRouter()


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    return (
        db.query(User)
        .filter(User.is_active == True)
        .order_by(User.email.asc())
        .all()
    )


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    existing = db.query(User).filter(User.email == data.email).first()

    if existing:
        # Reactivate + reset role + reset password + update profile fields
        existing.is_active = True
        existing.role = data.role
        existing.full_name = data.full_name
        existing.phone = data.phone
        existing.hashed_password = hash_password(data.password)
        db.commit()
        db.refresh(existing)
        return existing

    u = User(
        email=data.email,
        role=data.role,
        full_name=data.full_name,
        phone=data.phone,
        hashed_password=hash_password(data.password),
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@router.delete("/{user_id}", status_code=200)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    u.is_active = False
    db.commit()
    return {"ok": True, "user_id": user_id}
