from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from backend.app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class CoupleConnection(Base):
    __tablename__ = "couple_connections"

    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(32), default="pending", nullable=False) # 'pending', 'active', 'accepted', 'ended', 'rejected'
    
    # Relationship milestone timer settings
    relationship_start_date = Column(DateTime, nullable=True) # e.g. 2024-10-14 00:00:00
    anniversary_title = Column(String(100), default="Our Special Day", nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    requester = relationship("User", foreign_keys=[requester_id])
    recipient = relationship("User", foreign_keys=[recipient_id])
    messages = relationship("Message", back_populates="connection", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="connection", cascade="all, delete-orphan")
    notes = relationship("SharedNote", back_populates="connection", cascade="all, delete-orphan")

    @property
    def is_active(self) -> bool:
        return self.status in ("active", "accepted")

    def is_member(self, user_id: int) -> bool:
        return self.requester_id == user_id or self.recipient_id == user_id

    def get_partner_id(self, user_id: int) -> int:
        if self.requester_id == user_id:
            return self.recipient_id
        elif self.recipient_id == user_id:
            return self.requester_id
        raise ValueError("User is not a member of this couple connection")

    def to_dict(self, current_user_id: int = None):
        partner = None
        if current_user_id:
            if self.requester_id == current_user_id:
                partner = self.recipient.to_public_partner_dict() if self.recipient else None
            else:
                partner = self.requester.to_public_partner_dict() if self.requester else None

        return {
            "id": self.id,
            "requester_id": self.requester_id,
            "recipient_id": self.recipient_id,
            "status": self.status,
            "relationship_start_date": self.relationship_start_date.isoformat() if self.relationship_start_date else None,
            "anniversary_title": self.anniversary_title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "partner": partner
        }
