from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.notification import Notification
from backend.app.utils.security import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])

class UpdateProfileRequest(BaseModel):
    display_name: str | None = Field(None, min_length=1, max_length=50)
    bio: str | None = None
    status_message: str | None = Field(None, max_length=150)
    avatar_url: str | None = None

@router.get("/search")
def search_users(
    uid: str = Query(..., min_length=3, description="Partner UID (e.g. BT-XXXXXX)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search for another user by their unique UID."""
    target_uid = uid.strip().upper()
    if target_uid == current_user.uid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot search for yourself")

    user = db.query(User).filter(User.uid == target_uid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No user found with this UID")

    return user.to_public_partner_dict()

@router.get("/{uid}")
def get_user_by_uid(
    uid: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.uid == uid.strip().upper()).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user.to_public_partner_dict()

@router.put("/profile")
def update_profile(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if data.display_name:
        current_user.display_name = data.display_name.strip()
    if data.bio is not None:
        current_user.bio = data.bio.strip()
    if data.status_message is not None:
        current_user.status_message = data.status_message.strip()
    if data.avatar_url:
        current_user.avatar_url = data.avatar_url.strip()

    db.commit()
    db.refresh(current_user)
    return {"status": "success", "user": current_user.to_dict()}

@router.get("/notifications/list")
def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notifs = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).limit(20).all()

    return [n.to_dict() for n in notifs]

@router.post("/notifications/read-all")
def mark_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"status": "success"}
