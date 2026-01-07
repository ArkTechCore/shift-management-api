from pydantic import BaseModel
import uuid
from datetime import date, datetime


class PayrollInvoiceOut(BaseModel):
    id: uuid.UUID
    invoice_no: int

    tenant_id: uuid.UUID
    store_id: uuid.UUID
    employee_id: uuid.UUID

    week_start: date

    pay_rate_hourly: float
    regular_minutes: int
    overtime_minutes: int

    gross_pay: float
    tax_enabled: bool
    tax_rate_percent: float
    tax_withheld: float
    net_pay: float

    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class GenerateInvoicesResult(BaseModel):
    ok: bool = True
    created: int
    skipped_existing: int
