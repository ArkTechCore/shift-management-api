from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.schemas.user import UserCreate, UserOut
from app.models.user import User
from app.core.security import hash_password

router = APIRouter()

@router.post("", response_model=UserOut, dependencies=[Depends(require_role("admin"))])
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    user = User(email=data.email, hashed_password=hash_password(data.password), role=data.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
