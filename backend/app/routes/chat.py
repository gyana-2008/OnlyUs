from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.connection import CoupleConnection
from backend.app.models.message import Message
from backend.app.models.notification import Notification
from backend.app.services.storage_service import storage_service
from backend.app.utils.security import get_active_couple

router = APIRouter(prefix="/api/chat", tags=["chat"])

class SendMessagePayload(BaseModel):
    content: str | None = None
    media_url: str | None = None
    media_type: str | None = None # 'image', 'video', 'audio'
    media_name: str | None = None
    media_duration: float | None = None
    reply_to_id: int | None = None

@router.get("/messages")
def get_messages(
    limit: int = Query(50, ge=1, le=100),
    before_id: int | None = None,
    couple_data: tuple[User, CoupleConnection] = Depends(get_active_couple),
    db: Session = Depends(get_db)
):
    current_user, conn = couple_data
    partner_id = conn.get_partner_id(current_user.id)

    query = db.query(Message).filter(Message.connection_id == conn.id)
    if before_id:
        query = query.filter(Message.id < before_id)

    messages = query.order_by(Message.created_at.desc()).limit(limit).all()
    # Reverse so they are returned in chronological order
    messages = list(reversed(messages))

    # Mark unread incoming messages as read
    now = datetime.now(timezone.utc)
    db.query(Message).filter(
        Message.connection_id == conn.id,
        Message.recipient_id == current_user.id,
        Message.read_at.is_(None)
    ).update({"read_at": now})
    db.commit()

    return [m.to_dict() for m in messages]

@router.post("/messages", status_code=status.HTTP_201_CREATED)
def send_message(
    data: SendMessagePayload,
    couple_data: tuple[User, CoupleConnection] = Depends(get_active_couple),
    db: Session = Depends(get_db)
):
    current_user, conn = couple_data
    partner_id = conn.get_partner_id(current_user.id)

    if not data.content and not data.media_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message must contain text or media")

    msg = Message(
        connection_id=conn.id,
        sender_id=current_user.id,
        recipient_id=partner_id,
        content=data.content.strip() if data.content else None,
        media_url=data.media_url,
        media_type=data.media_type,
        media_name=data.media_name,
        media_duration=data.media_duration,
        reply_to_id=data.reply_to_id,
    )
    db.add(msg)

    # Add notification for partner
    snippet = data.content[:60] if data.content else f"Sent a {data.media_type or 'file'}"
    notif = Notification(
        user_id=partner_id,
        actor_id=current_user.id,
        type="new_message",
        title=f"Message from {current_user.display_name}",
        message=snippet,
        link="/chat.html"
    )
    db.add(notif)
    db.commit()
    db.refresh(msg)

    return msg.to_dict()

@router.post("/upload")
async def upload_chat_media(
    file: UploadFile = File(...),
    couple_data: tuple[User, CoupleConnection] = Depends(get_active_couple)
):
    """Upload photo, video, or recorded voice note."""
    result = await storage_service.save_upload(file)
    return result

@router.delete("/messages/{message_id}")
def delete_message(
    message_id: int,
    couple_data: tuple[User, CoupleConnection] = Depends(get_active_couple),
    db: Session = Depends(get_db)
):
    current_user, conn = couple_data
    msg = db.query(Message).filter(
        Message.id == message_id,
        Message.connection_id == conn.id
    ).first()

    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    if msg.sender_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own messages")

    # Soft delete
    msg.is_deleted = True
    msg.content = None
    if msg.media_url:
        storage_service.delete_file(msg.media_url)
        msg.media_url = None

    db.commit()
    return {"status": "success", "message": "Message deleted"}

@router.post("/thinking-of-you")
def thinking_of_you(
    couple_data: tuple[User, CoupleConnection] = Depends(get_active_couple),
    db: Session = Depends(get_db)
):
    """Send an instant 'Thinking of you' warm ping to partner."""
    current_user, conn = couple_data
    partner_id = conn.get_partner_id(current_user.id)

    notif = Notification(
        user_id=partner_id,
        actor_id=current_user.id,
        type="thinking_of_you",
        title="Thinking of you",
        message=f"{current_user.display_name} just sent you a warm thought 💕",
        link="/private.html"
    )
    db.add(notif)
    db.commit()

    return {"status": "success", "message": "Ping sent to partner"}
