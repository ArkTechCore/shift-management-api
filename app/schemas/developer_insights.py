from pydantic import BaseModel
from typing import Optional
import uuid

class TenantInsightsOut(BaseModel):
    tenant_id: uuid.UUID
    tenant_code: Optional[str] = None
    tenant_name: Optional[str] = None
    is_active: bool

    stores_count: int
    users_count: int
    active_users_count: int
    managers_count: int
    employees_count: int

    schedules_count: int
    published_schedules_count: int

    open_time_entries_count: int
    invoices_count: int
