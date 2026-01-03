import uuid
from datetime import datetime, date

from sqlalchemy import Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Availability(Base):
    """
    Employee availability for a specific store + week + day.
    Keep it simple + normalized (one row per day).
    """
    __tablename__ = "availability"
    __table_args__ = (
        UniqueConstraint("employee_id", "store_id", "week_id", "day", name="uq_availability_emp_store_week_day"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False
    )

    week_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("weeks.id", ondelete="CASCADE"), nullable=False
    )

    day: Mapped[date] = mapped_column(Date, nullable=False)

    # ISO timestamps stored as UTC
    available_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    available_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
