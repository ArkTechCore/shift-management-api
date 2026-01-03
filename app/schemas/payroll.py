from pydantic import BaseModel
from typing import List
import uuid


class EmployeePayrollLine(BaseModel):
    employee_id: uuid.UUID
    total_minutes: int
    out_of_zone_seconds: int
    open_entries: int  # missed clock-out count


class StoreWeekPayrollSummary(BaseModel):
    store_id: uuid.UUID
    week_start: str  # ISO date string
    week_end: str    # ISO date string
    lines: List[EmployeePayrollLine]
