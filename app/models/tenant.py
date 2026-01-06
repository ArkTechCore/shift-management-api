import uuid
from sqlalchemy import Column, String, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # public-ish identifier you can show in developer portal (not sensitive)
    code = Column(String(64), unique=True, index=True, nullable=False)

    # company/client name
    name = Column(String(128), nullable=False)

    # plan + billing controls (payment gateway later)
    plan = Column(String(32), nullable=False, default="growth")  # growth|pro|premium
    billing_cycle = Column(String(16), nullable=False, default="monthly")  # monthly|yearly

    # store-based limits (you said: limit on stores, not users)
    max_stores = Column(Integer, nullable=False, default=3)

    # feature toggles (developer can enable/disable)
    feature_payroll = Column(Boolean, nullable=False, default=True)
    feature_timeclock = Column(Boolean, nullable=False, default=True)
    feature_scheduling = Column(Boolean, nullable=False, default=True)
    feature_ai = Column(Boolean, nullable=False, default=False)

    # lifecycle
    is_active = Column(Boolean, nullable=False, default=True)
