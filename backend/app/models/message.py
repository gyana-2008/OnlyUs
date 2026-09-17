from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("couple_connections.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    content = Column(Text, nullable=True)
    media_url = Column(String(500), nullable=True)
    media_type = Column(String(32), nullable=True) # 'image', 'video', 'audio'
    media_name = Column(String(255), nullable=True)
    media_duration = Column(Float, nullable=True) # seconds, for voice notes
    
    reply_to_id = Column(Integer, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    # Relationships
    connection = relationship("CoupleConnection", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_messages")
    reply_to = relationship("Message", remote_side=[id])

    def to_dict(self):
        reply_snippet = None
        if self.reply_to and not self.reply_to.is_deleted:
            reply_snippet = {
                "id": self.reply_to.id,
                "sender_id": self.reply_to.sender_id,
                "content": (self.reply_to.content[:60] + "...") if self.reply_to.content and len(self.reply_to.content) > 60 else (self.reply_to.content or f"[{self.reply_to.media_type}]")
            }

        return {
            "id": self.id,
            "connection_id": self.connection_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "content": "[Message deleted]" if self.is_deleted else self.content,
            "media_url": None if self.is_deleted else self.media_url,
            "media_type": None if self.is_deleted else self.media_type,
            "media_name": None if self.is_deleted else self.media_name,
            "media_duration": None if self.is_deleted else self.media_duration,
            "reply_to": reply_snippet,
            "is_deleted": self.is_deleted,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
