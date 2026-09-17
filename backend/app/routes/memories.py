from datetime import datetime, date, timezone
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.connection import CoupleConnection
from backend.app.models.memory import Memory
from backend.app.models.message import Message
from backend.app.models.notification import Notification
from backend.app.utils.security import get_active_couple

router = APIRouter(prefix="/api/memories", tags=["memories"])

class MemoryPayload(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    story: str | None = None
    memory_date: str = Field(..., description="YYYY-MM-DD format")
    tag: str = Field("Everyday", max_length=50) # 'Trip', 'Firsts', 'Date Night', 'Anniversary', 'Everyday'
    media_url: str | None = None
    media_type: str | None = None # 'image', 'video', 'audio'
    is_favorite: bool = False

class MemoryUpdatePayload(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=150)
    story: str | None = None
    memory_date: str | None = Field(None, description="YYYY-MM-DD format")
    tag: str | None = Field(None, max_length=50)
    media_url: str | None = None
    media_type: str | None = None
    is_favorite: bool | None = None

@router.get("")
def get_memories(
    tag: str | None = None,
    couple_data: tuple[User, CoupleConnection] = Depends(get_active_couple),
    db: Session = Depends(get_db)
):
    current_user, conn = couple_data
    query = db.query(Memory).filter(Memory.connection_id == conn.id)
    
    if tag and tag.lower() != "all":
        query = query.filter(Memory.tag.ilike(tag.strip()))

    memories = query.order_by(Memory.memory_date.desc(), Memory.created_at.desc()).all()
    return [m.to_dict() for m in memories]

@router.get("/stats")
def get_relationship_stats(
    couple_data: tuple[User, CoupleConnection] = Depends(get_active_couple),
    db: Session = Depends(get_db)
):
    """Tasteful relationship analytics and memory metrics."""
    current_user, conn = couple_data

    # Calculate days together
    now = datetime.now(timezone.utc)
    start_date = conn.relationship_start_date or conn.accepted_at or conn.created_at
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    delta = now - start_date
    days_together = max(1, delta.days)

    # Memories metrics
    all_memories = db.query(Memory).filter(Memory.connection_id == conn.id).all()
    memories_count = len(all_memories)

    tag_counts = defaultdict(int)
    monthly_activity = defaultdict(int)
    for m in all_memories:
        tag_counts[m.tag] += 1
        month_str = m.memory_date.strftime("%b %Y")
        monthly_activity[month_str] += 1

    # Messages metrics
    messages_count = db.query(Message).filter(
        Message.connection_id == conn.id,
        Message.is_deleted == False
    ).count()

    # Media count
    media_count = db.query(Message).filter(
        Message.connection_id == conn.id,
        Message.media_url.isnot(None),
        Message.is_deleted == False
    ).count()

    return {
        "days_together": days_together,
        "memories_count": memories_count,
        "messages_count": messages_count,
        "media_count": media_count,
        "tag_counts": dict(tag_counts),
        "monthly_activity": [
            {"month": k, "count": v} for k, v in list(monthly_activity.items())[-6:]
        ]
    }

@router.get("/{memory_id}")
def get_memory(
    memory_id: int,
    couple_data: tuple[User, CoupleConnection] = Depends(get_active_couple),
    db: Session = Depends(get_db)
):
    current_user, conn = couple_data
    mem = db.query(Memory).filter(
        Memory.id == memory_id,
        Memory.connection_id == conn.id
    ).first()

    if not mem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")

    return mem.to_dict()

@router.put("/{memory_id}")
def update_memory(
    memory_id: int,
    data: MemoryUpdatePayload,
    couple_data: tuple[User, CoupleConnection] = Depends(get_active_couple),
    db: Session = Depends(get_db)
):
    current_user, conn = couple_data
    partner_id = conn.get_partner_id(current_user.id)

    mem = db.query(Memory).filter(
        Memory.id == memory_id,
        Memory.connection_id == conn.id
    ).first()

    if not mem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")

    if data.title is not None:
        mem.title = data.title.strip()
    if data.story is not None:
        mem.story = data.story.strip() if data.story else None
    if data.memory_date is not None:
        try:
            mem.memory_date = date.fromisoformat(data.memory_date)
        except Exception:
            pass
    if data.tag is not None:
        mem.tag = data.tag.strip()
    if data.media_url is not None:
        mem.media_url = data.media_url if data.media_url != "" else None
    if data.media_type is not None:
        mem.media_type = data.media_type if data.media_type != "" else None
    if data.is_favorite is not None:
        mem.is_favorite = data.is_favorite

    # Notify partner
    notif = Notification(
        user_id=partner_id,
        actor_id=current_user.id,
        type="memory_updated",
        title="Shared Memory Updated",
        message=f"{current_user.display_name} updated memory: '{mem.title}'",
        link="/memories.html"
    )
    db.add(notif)
    db.commit()
    db.refresh(mem)

    return mem.to_dict()

@router.post("", status_code=status.HTTP_201_CREATED)
def create_memory(
    data: MemoryPayload,
    couple_data: tuple[User, CoupleConnection] = Depends(get_active_couple),
    db: Session = Depends(get_db)
):
    current_user, conn = couple_data
    partner_id = conn.get_partner_id(current_user.id)

    try:
        mem_date = date.fromisoformat(data.memory_date)
    except Exception:
        mem_date = date.today()

    memory = Memory(
        connection_id=conn.id,
        author_id=current_user.id,
        title=data.title.strip(),
        story=data.story.strip() if data.story else None,
        memory_date=mem_date,
        tag=data.tag.strip(),
        media_url=data.media_url,
        media_type=data.media_type,
        is_favorite=data.is_favorite
    )
    db.add(memory)

    # Notify partner
    notif = Notification(
        user_id=partner_id,
        actor_id=current_user.id,
        type="memory_added",
        title="New Shared Memory",
        message=f"{current_user.display_name} added a memory: '{data.title}'",
        link="/memories.html"
    )
    db.add(notif)
    db.commit()
    db.refresh(memory)

    return memory.to_dict()

@router.delete("/{memory_id}")
def delete_memory(
    memory_id: int,
    couple_data: tuple[User, CoupleConnection] = Depends(get_active_couple),
    db: Session = Depends(get_db)
):
    current_user, conn = couple_data
    mem = db.query(Memory).filter(
        Memory.id == memory_id,
        Memory.connection_id == conn.id
    ).first()

    if not mem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")

    db.delete(mem)
    db.commit()
    return {"status": "success", "message": "Memory deleted"}

@router.post("/{memory_id}/favorite")
def toggle_favorite(
    memory_id: int,
    couple_data: tuple[User, CoupleConnection] = Depends(get_active_couple),
    db: Session = Depends(get_db)
):
    current_user, conn = couple_data
    mem = db.query(Memory).filter(
        Memory.id == memory_id,
        Memory.connection_id == conn.id
    ).first()

    if not mem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")

    mem.is_favorite = not mem.is_favorite
    db.commit()
    return {"status": "success", "is_favorite": mem.is_favorite}

