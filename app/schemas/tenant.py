import uuid
from pydantic import BaseModel, Field


class TenantBase(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=128)

    plan: str = "growth"  # growth|pro|premium
    billing_cycle: str = "monthly"  # monthly|yearly

    max_stores: int = Field(default=3, ge=1, le=9999)

    feature_payroll: bool = True
    feature_timeclock: bool = True
    feature_scheduling: bool = True
    feature_ai: bool = False

    is_active: bool = True


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    name: str | None = None
    plan: str | None = None
    billing_cycle: str | None = None
    max_stores: int | None = None

    feature_payroll: bool | None = None
    feature_timeclock: bool | None = None
    feature_scheduling: bool | None = None
    feature_ai: bool | None = None

    is_active: bool | None = None


class TenantOut(TenantBase):
    id: uuid.UUID

    class Config:
        from_attributes = True
