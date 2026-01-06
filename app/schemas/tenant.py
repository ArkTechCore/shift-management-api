from pydantic import BaseModel, Field


class TenantCreate(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=128)

    plan: str = "growth"  # growth|pro|premium
    billing_cycle: str = "monthly"  # monthly|yearly
    max_stores: int = 3

    feature_payroll: bool = True
    feature_timeclock: bool = True
    feature_scheduling: bool = True
    feature_ai: bool = False


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


class TenantOut(BaseModel):
    id: str
    code: str
    name: str

    plan: str
    billing_cycle: str
    max_stores: int

    feature_payroll: bool
    feature_timeclock: bool
    feature_scheduling: bool
    feature_ai: bool

    is_active: bool

    class Config:
        from_attributes = True
