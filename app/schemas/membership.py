import uuid
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class MembershipCreate(BaseModel):
    # You can send either store_id OR store_code (store_code is what you want in admin UI)
    user_id: uuid.UUID

    store_id: Optional[uuid.UUID] = None
    store_code: Optional[str] = None

    store_role: str = Field(default="employee", pattern="^(manager|employee)$")

    # Only required for employee. Manager has no pay rate.
    pay_rate: Optional[str] = None

    @model_validator(mode="after")
    def validate_inputs(self):
        if not self.store_id and not self.store_code:
            raise ValueError("Provide either store_id or store_code")

        if self.store_role == "employee":
            if not self.pay_rate:
                raise ValueError("pay_rate is required for employee membership")
        else:
            # manager: ignore pay rate completely
            self.pay_rate = "0"

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
