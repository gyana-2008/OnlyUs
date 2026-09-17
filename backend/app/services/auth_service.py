import secrets
import string
from datetime import datetime, timedelta, timezone
import jwt
import bcrypt
from backend.app.config import settings

def hash_secret(plain_text: str) -> str:
    """Hash password or PIN securely using bcrypt."""
    if not plain_text:
        return ""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_text.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_secret(plain_text: str, hashed: str) -> bool:
    """Verify password or PIN against bcrypt hash."""
    if not plain_text or not hashed:
        return False
    try:
        return bcrypt.checkpw(plain_text.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def generate_uid() -> str:
    """Generate a unique UID in format 'BT-XXXXXX' using cryptographically secure RNG."""
    chars = string.ascii_uppercase + string.digits
    # Exclude confusing characters: 0/O, 1/I
    safe_chars = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    suffix = "".join(secrets.choice(safe_chars) for _ in range(6))
    return f"BT-{suffix}"

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Generate JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "iat": now,
        "exp": expire,
        "type": "access"
    })
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def create_private_token(user_id: int, couple_id: int = None) -> str:
    """Generate scoped private-access token after PIN/Passkey challenge."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.PRIVATE_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "couple_id": couple_id,
        "type": "private_access",
        "iat": now,
        "exp": expire
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
