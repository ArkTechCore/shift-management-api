# app/schemas/schedule.py
from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class ShiftAssignmentOut(BaseModel):
    id: uuid.UUID
    shift_id: uuid.UUID
    employee_id: uuid.UUID
    assigned_at: datetime

    class Config:
        from_attributes = True


class ShiftOut(BaseModel):
    id: uuid.UUID
    schedule_id: uuid.UUID
    role: str
    start_at: datetime
    end_at: datetime
    headcount_required: int
    created_at: datetime
    assignments: list[ShiftAssignmentOut] = []

    class Config:
        from_attributes = True


class ScheduleOut(BaseModel):
    id: uuid.UUID
    store_id: uuid.UUID
    week_id: uuid.UUID
    is_published: bool
    created_at: datetime
    shifts: list[ShiftOut] = []

    class Config:
        from_attributes = True


class ShiftCreateRequest(BaseModel):
    role: str = Field(min_length=1, max_length=50)
    start_at: datetime
    end_at: datetime
    headcount_required: int = Field(default=1, ge=1, le=50)


class ShiftAssignRequest(BaseModel):
    employee_id: uuid.UUID


class PublishScheduleRequest(BaseModel):
    is_published: bool
