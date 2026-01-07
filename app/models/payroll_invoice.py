import uuid
from sqlalchemy import Column, Date, DateTime, String, Numeric, Boolean, Integer, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import Base


class PayrollInvoice(Base):
    __tablename__ = "payroll_invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    store_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    week_start = Column(Date, nullable=False, index=True)

    # DB: bigint with sequence default
    invoice_no = Column(BigInteger, nullable=False, index=True)

    pay_rate_hourly = Column(Numeric(10, 2), nullable=False, default=0)

    regular_minutes = Column(Integer, nullable=False, default=0)
    overtime_minutes = Column(Integer, nullable=False, default=0)

    gross_pay = Column(Numeric(12, 2), nullable=False, default=0)

    # DB: boolean
    tax_enabled = Column(Boolean, nullable=False, default=False)
    tax_rate_percent = Column(Numeric(5, 2), nullable=False, default=0)
    tax_withheld = Column(Numeric(12, 2), nullable=False, default=0)

    net_pay = Column(Numeric(12, 2), nullable=False, default=0)

    status = Column(String(24), nullable=False, default="issued")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
