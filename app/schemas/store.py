import uuid
from pydantic import BaseModel, Field


class StoreCreate(BaseModel):
    code: str
    name: str
    timezone: str = "America/New_York"

    geofence_lat: float | None = None
    geofence_lng: float | None = None
    geofence_radius_m: int = Field(default=150, ge=20, le=2000)


class StoreOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    timezone: str

    geofence_lat: float | None
    geofence_lng: float | None
    geofence_radius_m: int

    is_active: bool

    class Config:
        from_attributes = True
