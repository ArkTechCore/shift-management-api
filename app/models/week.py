import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Tenant boundary (NULL only for developer/super admin)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    email = Column(String(255), unique=True, index=True, nullable=False)
    role = Column(String(50), nullable=False, default="employee")  # developer|tenant_admin|manager|employee
    hashed_password = Column(String(255), nullable=False)

    # Profile
    name = Column(String(120), nullable=True)
    phone = Column(String(32), nullable=True)

    # Status + security
    status = Column(String(24), nullable=False, default="active")  # active|disabled
    must_change_password = Column(Boolean, nullable=False, default=False)
    temp_password_issued_at = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)

    failed_login_count = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
