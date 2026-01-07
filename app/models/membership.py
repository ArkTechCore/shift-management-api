import uuid
from sqlalchemy import String, ForeignKey, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class StoreMembership(Base):
    __tablename__ = "store_memberships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
    )

    store_role: Mapped[str] = mapped_column(String(20), nullable=False, default="employee")

    # legacy (keep it)
    pay_rate: Mapped[str] = mapped_column(String(20), nullable=False, default="0")

    # NEW (used by payroll invoices)
    pay_rate_hourly: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    tax_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tax_rate_percent: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
