# app/schemas/user.py

from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid


class UserBase(BaseModel):
    email: EmailStr
    role: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserOut(UserBase):
    id: uuid.UUID
    is_active: bool

    class Config:
        from_attributes = True
