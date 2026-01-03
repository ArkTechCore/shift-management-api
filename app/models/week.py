# app/models/week.py

import uuid
from datetime import date, datetime
from sqlalchemy import Column, Date, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class Week(Base):
    __tablename__ = "weeks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Always FRIDAY
    week_start = Column(Date, nullable=False, unique=True)

    # Always THURSDAY
    week_end = Column(Date, nullable=False)

    # Locking
    is_locked = Column(Boolean, default=False, nullable=False)
    locked_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
