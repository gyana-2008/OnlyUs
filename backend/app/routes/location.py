from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.user import User, UserSettings
from backend.app.models.connection import CoupleConnection
from backend.app.utils.security import get_active_couple
from backend.app.utils.distance import compute_privacy_aware_distance

router = APIRouter(prefix="/api/location", tags=["location"])

class LocationUpdatePayload(BaseModel):
    latitude: float
    longitude: float
    city: str | None = None
    country: str | None = None

class PermissionPayload(BaseModel):
    sharing_level: str = Field(..., description="'off' | 'distance_only' | 'city_only' | 'approximate' | 'exact'")

@router.post("/update")
def update_location(
    data: LocationUpdatePayload,
    current_user: User = Depends(get_active_couple),
    db: Session = Depends(get_db)
):
    user, conn = current_user
    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    if not settings:
        settings = UserSettings(user_id=user.id)
        db.add(settings)

    settings.latitude = data.latitude
    settings.longitude = data.longitude
    if data.city:
        settings.city = data.city.strip()
    if data.country:
        settings.country = data.country.strip()
    settings.last_location_updated_at = datetime.now(timezone.utc)

    db.commit()
    return {"status": "success", "message": "Location updated"}

@router.put("/permission")
def update_permission(
    data: PermissionPayload,
    couple_data: tuple[User, CoupleConnection] = Depends(get_active_couple),
    db: Session = Depends(get_db)
):
    valid_levels = ("off", "distance_only", "city_only", "approximate", "exact")
    if data.sharing_level not in valid_levels:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid level. Must be one of {valid_levels}")

    user, conn = couple_data
    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    if not settings:
        settings = UserSettings(user_id=user.id)
        db.add(settings)

    settings.location_sharing_level = data.sharing_level
    db.commit()
    return {"status": "success", "sharing_level": settings.location_sharing_level}

@router.get("/distance")
def get_distance(
    couple_data: tuple[User, CoupleConnection] = Depends(get_active_couple),
    db: Session = Depends(get_db)
):
    user, conn = couple_data
    partner_id = conn.get_partner_id(user.id)

    user_settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    partner_settings = db.query(UserSettings).filter(UserSettings.user_id == partner_id).first()

    return compute_privacy_aware_distance(user_settings, partner_settings)
