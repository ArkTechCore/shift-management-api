from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid


class UserBase(BaseModel):
    email: EmailStr
    role: str
    name: Optional[str] = None
    phone: Optional[str] = None
    status: str = "active"  # active|disabled


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "employee"  # tenant_admin|manager|employee

    name: Optional[str] = None
    phone: Optional[str] = None

    must_change_password: bool = False


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None  # active|disabled


class UserOut(UserBase):
    id: uuid.UUID
    tenant_id: Optional[uuid.UUID] = None

    must_change_password: bool = False

    # convenience flag for UI
    is_active: bool = True

    class Config:
        from_attributes = True


class ResetPasswordOut(BaseModel):
    user_id: str
    email: str
    temp_password: str
    must_change_password: bool = True