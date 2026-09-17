from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class SharedNote(Base):
    __tablename__ = "shared_notes"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("couple_connections.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    title = Column(String(150), nullable=False)
    content = Column(Text, nullable=False)
    is_pinned = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    connection = relationship("CoupleConnection", back_populates="notes")
    author = relationship("User", foreign_keys=[author_id])

    def to_dict(self):
        return {
            "id": self.id,
            "connection_id": self.connection_id,
            "author_id": self.author_id,
            "author_name": self.author.display_name if self.author else None,
            "title": self.title,
            "content": self.content,
            "is_pinned": self.is_pinned,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class ImportantDate(Base):
    __tablename__ = "important_dates"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("couple_connections.id", ondelete="CASCADE"), nullable=False, index=True)
    
    title = Column(String(150), nullable=False)
    event_date = Column(Date, nullable=False)
    category = Column(String(50), default="milestone") # 'anniversary', 'birthday', 'trip', 'milestone'
    notes = Column(String(300), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "connection_id": self.connection_id,
            "title": self.title,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "category": self.category,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
