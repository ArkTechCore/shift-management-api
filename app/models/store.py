import uuid
from sqlalchemy import Column, String, Boolean, Float, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class Store(Base):
    __tablename__ = "stores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)

    # Critical for week logic + UI
    timezone = Column(String(64), nullable=False, default="America/New_York")

    # Geo-fence (simple circle fence)
    geofence_lat = Column(Float, nullable=True)
    geofence_lng = Column(Float, nullable=True)
    geofence_radius_m = Column(Integer, nullable=False, default=150)

    is_active = Column(Boolean, default=True, nullable=False)
