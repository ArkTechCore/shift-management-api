import uuid
from pydantic import BaseModel, Field


class MembershipCreate(BaseModel):
    user_id: uuid.UUID
    store_id: uuid.UUID
    store_role: str = Field(default="employee", pattern="^(manager|employee)$")
    pay_rate: str = "0"


class MembershipOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    store_id: uuid.UUID
    store_role: str
    pay_rate: str

    class Config:
        from_attributes = True
