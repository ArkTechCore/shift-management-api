import uuid
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class MembershipCreate(BaseModel):
    user_id: uuid.UUID

    # Either store_id or store_code is required
    store_id: Optional[uuid.UUID] = None
    store_code: Optional[str] = None

    store_role: str = Field(default="employee", pattern="^(manager|employee)$")

    # Pay rate applies only for employee memberships
    pay_rate: Optional[str] = "0"

    @model_validator(mode="after")
    def validate_store_target(self):
        if not self.store_id and not (self.store_code and self.store_code.strip()):
            raise ValueError("Either store_id or store_code is required")
        return self


class MembershipOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    store_id: uuid.UUID
    store_role: str
    pay_rate: str
    is_active: bool

    class Config:
        from_attributes = True
