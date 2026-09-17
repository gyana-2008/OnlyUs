from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("couple_connections.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    title = Column(String(150), nullable=False)
    story = Column(Text, nullable=True)
    memory_date = Column(Date, nullable=False)
    tag = Column(String(50), default="Everyday", nullable=False) # 'Trip', 'Firsts', 'Date Night', 'Anniversary', 'Everyday'
    
    media_url = Column(String(500), nullable=True)
    media_type = Column(String(32), nullable=True) # 'image', 'video', 'audio'
    is_favorite = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    connection = relationship("CoupleConnection", back_populates="memories")
    author = relationship("User", foreign_keys=[author_id])

    def to_dict(self):
        return {
            "id": self.id,
            "connection_id": self.connection_id,
            "author_id": self.author_id,
            "author_name": self.author.display_name if self.author else None,
            "title": self.title,
            "story": self.story,
            "memory_date": self.memory_date.isoformat() if self.memory_date else None,
            "tag": self.tag,
            "media_url": self.media_url,
            "media_type": self.media_type,
            "is_favorite": self.is_favorite,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
