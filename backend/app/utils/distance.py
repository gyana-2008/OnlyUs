import math
from typing import Optional, Dict, Any

EARTH_RADIUS_KM = 6371.0

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points on the Earth in kilometers."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    distance_km = EARTH_RADIUS_KM * c
    return round(distance_km, 1)

def compute_privacy_aware_distance(
    user_settings,
    partner_settings
) -> Dict[str, Any]:
    """
    Compute distance respecting both users' privacy levels.
    Levels: 'off', 'distance_only', 'city_only', 'approximate', 'exact'
    """
    if not user_settings or not partner_settings:
        return {"allowed": False, "message": "Location settings not configured"}

    level_a = user_settings.location_sharing_level
    level_b = partner_settings.location_sharing_level

    # If either user has disabled sharing completely
    if level_a == "off" or level_b == "off":
        return {
            "allowed": False,
            "message": "Location sharing is disabled by one or both partners",
            "sharing_level": level_a
        }

    # Check if coordinates exist
    if user_settings.latitude is None or partner_settings.latitude is None:
        return {
            "allowed": False,
            "message": "Waiting for partner or your location update",
            "sharing_level": level_a
        }

    dist_km = calculate_haversine_distance(
        user_settings.latitude, user_settings.longitude,
        partner_settings.latitude, partner_settings.longitude
    )
    dist_miles = round(dist_km * 0.621371, 1)

    result = {
        "allowed": True,
        "distance_km": dist_km,
        "distance_miles": dist_miles,
        "formatted_km": f"{int(dist_km):,} km",
        "formatted_miles": f"{int(dist_miles):,} miles",
        "my_sharing_level": level_a,
        "partner_sharing_level": level_b,
    }

    # Reveal city names if both allow city_only or higher
    if level_a in ("city_only", "approximate", "exact") and level_b in ("city_only", "approximate", "exact"):
        result["my_city"] = user_settings.city
        result["partner_city"] = partner_settings.city

    # Reveal exact coordinates only if BOTH explicitly enable 'exact'
    if level_a == "exact" and level_b == "exact":
        result["my_coords"] = {"lat": user_settings.latitude, "lon": user_settings.longitude}
        result["partner_coords"] = {"lat": partner_settings.latitude, "lon": partner_settings.longitude}

    return result
