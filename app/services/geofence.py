# app/services/geofence.py

import math
from typing import Optional


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Distance in meters between two lat/lng points.
    """
    R = 6371000.0  # meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def is_inside_geofence(
    store_lat: Optional[float],
    store_lng: Optional[float],
    radius_m: int,
    user_lat: float,
    user_lng: float,
) -> bool:
    """
    If store geofence is not set, allow (fail-open).
    """
    if store_lat is None or store_lng is None:
        return True
    return haversine_m(store_lat, store_lng, user_lat, user_lng) <= float(radius_m)
