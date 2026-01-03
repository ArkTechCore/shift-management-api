import uuid
from datetime import date, datetime
from pydantic import BaseModel, Field


class LeaveRequestCreate(BaseModel):
    store_id: uuid.UUID
    start_date: date
    end_date: date
    reason: str | None = Field(default=None, max_length=255)


class LeaveDecision(BaseModel):
    # approved | rejected
    status: str = Field(pattern="^(approved|rejected)$")


class LeaveRequestOut(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    store_id: uuid.UUID
    start_date: date
    end_date: date
    reason: str | None
    status: str

    decided_by: uuid.UUID | None
    decided_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True
