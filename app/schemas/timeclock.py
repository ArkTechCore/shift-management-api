# app/schemas/timeclock.py

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ClockInRequest(BaseModel):
    store_id: UUID
    lat: float
    lng: float


class ClockOutRequest(BaseModel):
    time_entry_id: UUID
    lat: float
    lng: float


class OutOfZonePingRequest(BaseModel):
    time_entry_id: UUID
    is_out_of_zone: bool
    seconds_since_last_ping: int = Field(ge=0, le=3600)


class TimeEntryOut(BaseModel):
    id: UUID
    store_id: UUID
    employee_id: UUID

    clock_in_at: datetime
    clock_out_at: Optional[datetime] = None

    out_of_zone_seconds: int
    is_out_of_zone: bool

    created_at: datetime

    class Config:
        from_attributes = True
