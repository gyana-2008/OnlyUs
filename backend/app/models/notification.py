from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    type = Column(String(50), nullable=False) # 'connection_request', 'connection_accepted', 'new_message', 'thinking_of_you', 'memory_added'
    title = Column(String(150), nullable=False)
    message = Column(String(300), nullable=False)
    link = Column(String(150), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="notifications")
    actor = relationship("User", foreign_keys=[actor_id])

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "actor_id": self.actor_id,
            "actor_name": self.actor.display_name if self.actor else None,
            "actor_uid": self.actor.uid if self.actor else None,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "link": self.link,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
