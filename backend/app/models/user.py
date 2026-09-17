from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String(16), unique=True, index=True, nullable=False) # e.g. BT-4A82F9
    email = Column(String(255), unique=True, index=True, nullable=True)
    phone = Column(String(32), unique=True, index=True, nullable=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    hashed_pin = Column(String(255), nullable=True) # 4-6 digit private unlock PIN
    display_name = Column(String(100), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    status_message = Column(String(150), nullable=True, default="Reading")
    passkey_credential_id = Column(String(255), nullable=True)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.recipient_id", back_populates="recipient")
    notifications = relationship("Notification", foreign_keys="Notification.user_id", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self, include_private=False):
        data = {
            "id": self.id,
            "uid": self.uid,
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "status_message": self.status_message,
            "has_pin": bool(self.hashed_pin),
            "has_passkey": bool(self.passkey_credential_id),
            "is_demo": self.is_demo,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        return data

    def to_public_partner_dict(self):
        """Discreet data returned to authenticated partner"""
        return {
            "uid": self.uid,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "status_message": self.status_message,
            "bio": self.bio
        }


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Location privacy: 'off' | 'distance_only' | 'city_only' | 'approximate' | 'exact'
    location_sharing_level = Column(String(32), default="off", nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    last_location_updated_at = Column(DateTime, nullable=True)
    
    # Appearance & preferences
    theme = Column(String(20), default="editorial-dark", nullable=False)
    notify_messages = Column(Boolean, default=True)
    notify_moments = Column(Boolean, default=True)

    user = relationship("User", back_populates="settings")

    def to_dict(self):
        return {
            "location_sharing_level": self.location_sharing_level,
            "city": self.city if self.location_sharing_level in ("city_only", "approximate", "exact") else None,
            "country": self.country if self.location_sharing_level in ("city_only", "approximate", "exact") else None,
            "theme": self.theme,
            "notify_messages": self.notify_messages,
            "notify_moments": self.notify_moments
        }
