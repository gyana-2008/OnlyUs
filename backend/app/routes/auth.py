import time
import re
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.user import User, UserSettings
from backend.app.models.connection import CoupleConnection
from backend.app.services.auth_service import (
    hash_secret, verify_secret, generate_uid, create_access_token, create_private_token
)
from backend.app.utils.security import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

# In-memory tracking for PIN brute-force protection
FAILED_PIN_ATTEMPTS: dict[int, dict] = {}
MAX_PIN_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 60

class RegisterRequest(BaseModel):
    uid: str | None = None
    email: str | None = None
    mobile_number: str | None = None
    username: str | None = None
    password: str = Field(..., min_length=6, max_length=100)
    confirm_password: str | None = None
    display_name: str = Field(..., min_length=1, max_length=50)
    bio: str | None = None
    avatar_url: str | None = None
    pin: str | None = None

class LoginRequest(BaseModel):
    login_identifier: str = Field(..., description="Email, Mobile Number, Username, or UID")
    password: str

class PinRequest(BaseModel):
    pin: str = Field(..., min_length=4, max_length=8)

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    clean_email = data.email.strip().lower() if data.email and data.email.strip() else None
    clean_phone = data.mobile_number.strip() if data.mobile_number and data.mobile_number.strip() else None

    if not clean_email and not clean_phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or Mobile Number is required")

    if clean_email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean_email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format")

    if data.confirm_password and data.password != data.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")

    # Check existing email
    if clean_email:
        existing_email = db.query(User).filter(User.email == clean_email).first()
        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Check existing phone
    if clean_phone:
        existing_phone = db.query(User).filter(User.phone == clean_phone).first()
        if existing_phone:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mobile number already registered")

    # Allocate or validate UID
    if data.uid and data.uid.strip():
        chosen_uid = data.uid.strip().upper()
        if not re.match(r"^[A-Z0-9_-]{4,16}$", chosen_uid):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="UID must be 4-16 alphanumeric characters")
        if db.query(User).filter(User.uid == chosen_uid).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="UID already taken. Please choose another.")
        assigned_uid = chosen_uid
    else:
        for _ in range(10):
            uid_cand = generate_uid()
            if not db.query(User).filter(User.uid == uid_cand).first():
                assigned_uid = uid_cand
                break
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to allocate unique UID")

    # Determine username
    if data.username and data.username.strip():
        uname = data.username.strip().lower()
        if db.query(User).filter(User.username == uname).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
    else:
        uname = assigned_uid.lower()

    # Hash password with bcrypt
    hashed_pwd = hash_secret(data.password)

    # Optional initial PIN
    hashed_pin = None
    if data.pin and data.pin.strip().isdigit() and 4 <= len(data.pin.strip()) <= 8:
        hashed_pin = hash_secret(data.pin.strip())

    new_user = User(
        uid=assigned_uid,
        email=clean_email,
        phone=clean_phone,
        username=uname,
        hashed_password=hashed_pwd,
        hashed_pin=hashed_pin,
        display_name=data.display_name.strip(),
        bio=data.bio.strip() if data.bio else None,
        avatar_url=data.avatar_url or "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80",
        is_demo=False
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
    ident = data.login_identifier.strip()
    ident_lower = ident.lower()
    ident_upper = ident.upper()

    # Search by email, phone, username, or UID
    user = db.query(User).filter(
        (User.email == ident_lower) |
        (User.phone == ident) |
        (User.username == ident_lower) |
        (User.uid == ident_upper)
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
        CoupleConnection.status.in_(["active", "accepted"])
    ).first()

    data = current_user.to_dict()
    data["connection"] = connection.to_dict(current_user.id) if connection else None
    return data

@router.post("/setup-pin")
def setup_pin(data: PinRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Set or update 4-8 digit Private Access PIN."""
    pin_str = data.pin.strip()
    if not pin_str.isdigit() or len(pin_str) < 4 or len(pin_str) > 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PIN must be between 4 and 8 digits")

    current_user.hashed_pin = hash_secret(pin_str)
    db.commit()
    return {"status": "success", "message": "Private PIN configured successfully"}

@router.post("/verify-pin")
def verify_pin(data: PinRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Verify PIN with brute-force protection and rate limiting."""
    now = time.time()
    attempt_info = FAILED_PIN_ATTEMPTS.get(current_user.id, {"count": 0, "locked_until": 0.0})

    if attempt_info["locked_until"] > now:
        remaining = int(attempt_info["locked_until"] - now)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed PIN attempts. Access locked for {remaining} seconds."
        )

    if not current_user.hashed_pin:
        # If user hasn't set a PIN yet, indicate so they are guided to create one
        return {
            "status": "need_pin",
            "has_pin": False,
            "message": "PIN not configured. Please create a private PIN."
        }

    if not verify_secret(data.pin.strip(), current_user.hashed_pin):
        attempt_info["count"] += 1
        if attempt_info["count"] >= MAX_PIN_ATTEMPTS:
            attempt_info["locked_until"] = now + LOCKOUT_DURATION_SECONDS
            attempt_info["count"] = 0
            FAILED_PIN_ATTEMPTS[current_user.id] = attempt_info
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed attempts. Locked for {LOCKOUT_DURATION_SECONDS} seconds."
            )
        FAILED_PIN_ATTEMPTS[current_user.id] = attempt_info
        remaining = MAX_PIN_ATTEMPTS - attempt_info["count"]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Incorrect Private PIN. ({remaining} attempts remaining)"
        )

    # Success: reset failed attempts
    FAILED_PIN_ATTEMPTS.pop(current_user.id, None)
    private_token = create_private_token(current_user.id)
    return {
        "status": "success",
        "private_token": private_token,
        "has_pin": True,
        "message": "Private space unlocked."
    }

@router.post("/logout")
def logout():
    return {"status": "success", "message": "Logged out successfully"}
