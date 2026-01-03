import uuid
from datetime import datetime
from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Integer,
    Boolean,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Schedule(Base):
    """
    One schedule per store per week.
    Week itself is defined in `weeks` table (Friday -> Thursday).
    """
    __tablename__ = "schedules"
    __table_args__ = (
        UniqueConstraint("store_id", "week_id", name="uq_schedules_store_week"),

    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
    )

    week_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("weeks.id", ondelete="CASCADE"),
        nullable=False,
    )

    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    shifts = relationship(
        "Shift",
        back_populates="schedule",
        cascade="all, delete-orphan",
    )


class Shift(Base):
    """
    Shift definition (no employee here).
    Supports headcount > 1.
    """
    __tablename__ = "shifts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schedules.id", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(String(50), nullable=False)

    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    headcount_required: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    schedule = relationship("Schedule", back_populates="shifts")
    assignments = relationship(
        "ShiftAssignment",
        back_populates="shift",
        cascade="all, delete-orphan",
    )


class ShiftAssignment(Base):
    """
    One employee filling one slot in a shift.
    """
    __tablename__ = "shift_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    shift_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shifts.id", ondelete="CASCADE"),
        nullable=False,
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    shift = relationship("Shift", back_populates="assignments")
