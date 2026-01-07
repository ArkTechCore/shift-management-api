import uuid
from datetime import datetime, date

from sqlalchemy import Column, Date, DateTime, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import Base


class Week(Base):
    """
    Defines the scheduling week boundary (Fri -> Thu).
    This table typically stores one row per week_start (Friday).
    """
    __tablename__ = "weeks"
    __table_args__ = (
        UniqueConstraint("week_start", name="uq_weeks_week_start"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Friday date (YYYY-MM-DD)
    week_start = Column(Date, nullable=False)

    # Lock state (admin controls)
    is_locked = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    @staticmethod
    def _as_date(v) -> date:
        if isinstance(v, date) and not isinstance(v, datetime):
            return v
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, str):
            return date.fromisoformat(v[:10])
        raise ValueError("Invalid date")

