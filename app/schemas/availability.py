import uuid
from datetime import datetime, date
from pydantic import BaseModel, Field


class AvailabilityUpsert(BaseModel):
    store_id: uuid.UUID
    week_id: uuid.UUID
    day: date

    available_start_at: datetime | None = None
    available_end_at: datetime | None = None


class AvailabilityOut(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    store_id: uuid.UUID
    week_id: uuid.UUID
    day: date

    available_start_at: datetime | None
    available_end_at: datetime | None

    created_at: datetime

    class Config:
        from_attributes = True
