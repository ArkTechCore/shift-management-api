from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional
import uuid


# ------------------------------------------------------------
# Base (what API returns)
# ------------------------------------------------------------
class UserBase(BaseModel):
    email: EmailStr
    role: str

    # Canonical display name in your app
    full_name: Optional[str] = None

    # Keep legacy field so old UI won’t break if it expects "name"
    # We’ll keep it optional and auto-fill it from full_name when possible.
    name: Optional[str] = None

    phone: Optional[str] = None
    status: str = "active"  # active|disabled


# ------------------------------------------------------------
# Create
# ------------------------------------------------------------
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "employee"  # tenant_admin|manager|employee

    # New preferred field
    full_name: Optional[str] = None

    # Legacy input support (if frontend still sends "name")
    name: Optional[str] = None

    phone: Optional[str] = None
    must_change_password: bool = False

    @model_validator(mode="after")
    def _normalize_names(self):
        # If only legacy "name" is provided, copy it into full_name
        if not (self.full_name or "").strip() and (self.name or "").strip():
            self.full_name = self.name.strip()
        # Keep legacy in sync too (helpful for older UI)
        if not (self.name or "").strip() and (self.full_name or "").strip():
            self.name = self.full_name.strip()
        return self


# ------------------------------------------------------------
# Update
# ------------------------------------------------------------
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = None

    full_name: Optional[str] = None
    name: Optional[str] = None

    phone: Optional[str] = None
    status: Optional[str] = None  # active|disabled

    @model_validator(mode="after")
    def _normalize_names(self):
        # If only legacy "name" is provided, copy it into full_name
        if self.full_name is None and self.name is not None:
            self.full_name = self.name
        # If only full_name is provided, keep name in sync
        if self.name is None and self.full_name is not None:
            self.name = self.full_name
        return self


# ------------------------------------------------------------
# Output
# ------------------------------------------------------------
class UserOut(UserBase):
    id: uuid.UUID
    tenant_id: Optional[uuid.UUID] = None

    must_change_password: bool = False

    # convenience flag for UI
    is_active: bool = True

    class Config:
        from_attributes = True


# ------------------------------------------------------------
# Reset Password response (admin issues temp password)
# ------------------------------------------------------------
class ResetPasswordOut(BaseModel):
    user_id: str
    email: str
    temp_password: str
    must_change_password: bool = True
