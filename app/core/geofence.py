# app/core/geofence.py

from math import radians, sin, cos, sqrt, atan2


def distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    # Haversine distance (meters)
    r = 6371000.0
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return r * c


def inside_geofence(
    user_lat: float,
    user_lng: float,
    store_lat: float | None,
    store_lng: float | None,
    radius_m: int,
) -> bool:
    # If store fence not configured yet, allow clock-in (or flip this to block if you want strict)
    if store_lat is None or store_lng is None:
        return True
    return distance_m(user_lat, user_lng, store_lat, store_lng) <= radius_m
