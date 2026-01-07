import uuid
from sqlalchemy import Column, String, Boolean, Float, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class Store(Base):
    __tablename__ = "stores"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_stores_tenant_code"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Tenant boundary
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    code = Column(String(50), index=True, nullable=False)
    name = Column(String(100), nullable=False)

    timezone = Column(String(64), nullable=False, default="America/New_York")

    geofence_lat = Column(Float, nullable=True)
    geofence_lng = Column(Float, nullable=True)
    geofence_radius_m = Column(Integer, nullable=False, default=150)

    is_active = Column(Boolean, default=True, nullable=False)
