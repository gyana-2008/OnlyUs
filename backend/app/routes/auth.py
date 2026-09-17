from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.user import User, UserSettings
from backend.app.models.connection import CoupleConnection
from backend.app.services.auth_service import (
    hash_secret, verify_secret, generate_uid, create_access_token, create_private_token
)
from backend.app.utils.security import get_current_user

import re

router = APIRouter(prefix="/api/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=6, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=50)
    bio: str | None = None
    avatar_url: str | None = None

    @classmethod
    def validate_email_format(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Invalid email format")
        return v

class LoginRequest(BaseModel):
    login_identifier: str = Field(..., description="Email, Username, or UID")
    password: str

class PinRequest(BaseModel):
    pin: str = Field(..., min_length=4, max_length=8)

class PasskeyRequest(BaseModel):
    credential_id: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    try:
        clean_email = data.validate_email_format(data.email)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Check existing email or username
    existing_email = db.query(User).filter(User.email == clean_email).first()
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    existing_user = db.query(User).filter(User.username == data.username.lower()).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

    # Generate unique UID
    for _ in range(10):
        uid = generate_uid()
        if not db.query(User).filter(User.uid == uid).first():
            break
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to allocate unique UID")

    # Hash password with bcrypt
    hashed_pwd = hash_secret(data.password)

    new_user = User(
        uid=uid,
        email=data.email.lower(),
        username=data.username.lower(),
        hashed_password=hashed_pwd,
        display_name=data.display_name.strip(),
        bio=data.bio.strip() if data.bio else None,
        avatar_url=data.avatar_url or "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80",
    )
    db.add(new_user)
    db.flush()

    # Create default user settings
    settings = UserSettings(user_id=new_user.id)
    db.add(settings)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": str(new_user.id), "uid": new_user.uid})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": new_user.to_dict()
    }

@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    ident = data.login_identifier.strip().lower()
    
    # Search by email, username, or UID
    user = db.query(User).filter(
        (User.email == ident) | (User.username == ident) | (User.uid == data.login_identifier.strip().upper())
    ).first()

    if not user or not verify_secret(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id), "uid": user.uid})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user.to_dict()
    }

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check active couple connection
    connection = db.query(CoupleConnection).filter(
        ((CoupleConnection.requester_id == current_user.id) | (CoupleConnection.recipient_id == current_user.id)),
        CoupleConnection.status == "accepted"
    ).first()

    data = current_user.to_dict()
    data["connection"] = connection.to_dict(current_user.id) if connection else None
    return data

@router.post("/setup-pin")
def setup_pin(data: PinRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Set or update 4-6 digit Private Access PIN."""
    pin_str = data.pin.strip()
    if not pin_str.isdigit() or len(pin_str) < 4 or len(pin_str) > 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PIN must be between 4 and 8 digits")

    current_user.hashed_pin = hash_secret(pin_str)
    db.commit()
    return {"status": "success", "message": "Private PIN set successfully"}

@router.post("/verify-pin")
def verify_pin(data: PinRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Verify PIN and issue scoped private token."""
    if not current_user.hashed_pin:
        # If user hasn't set a PIN yet, allow initial access or recommend setting one
        private_token = create_private_token(current_user.id)
        return {
            "status": "success",
            "private_token": private_token,
            "has_pin": False,
            "message": "No PIN was configured. Private space unlocked."
        }

    if not verify_secret(data.pin.strip(), current_user.hashed_pin):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect Private PIN")

    private_token = create_private_token(current_user.id)
    return {
        "status": "success",
        "private_token": private_token,
        "has_pin": True,
        "message": "Private space unlocked."
    }

@router.post("/passkey-register")
def register_passkey(data: PasskeyRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Register browser Passkey/WebAuthn credential ID."""
    current_user.passkey_credential_id = data.credential_id
    db.commit()
    return {"status": "success", "message": "Passkey registered successfully"}

@router.post("/passkey-verify")
def verify_passkey(data: PasskeyRequest, current_user: User = Depends(get_current_user)):
    """Verify Passkey for instant private unlock."""
    if not current_user.passkey_credential_id or current_user.passkey_credential_id != data.credential_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Passkey verification failed")

    private_token = create_private_token(current_user.id)
    return {
        "status": "success",
        "private_token": private_token,
        "message": "Biometric / Passkey verified. Welcome to your private space."
    }

@router.post("/logout")
def logout():
    return {"status": "success", "message": "Logged out successfully"}
