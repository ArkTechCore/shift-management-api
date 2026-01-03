# app/models/timeentry.py

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TimeEntry(Base):
    __tablename__ = "time_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    week_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("weeks.id", ondelete="CASCADE"),
    nullable=False,
    )


    clock_in_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    clock_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    out_of_zone_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_out_of_zone: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
