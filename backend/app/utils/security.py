from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.connection import CoupleConnection
from backend.app.services.auth_service import decode_token

security = HTTPBearer(auto_error=False)

def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Validate Bearer JWT and return authenticated User."""
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        payload = decode_token(auth.credentials)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    return user

def get_optional_user(
    auth: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User | None:
    """Optional user authentication for public endpoints."""
    if not auth or not auth.credentials:
        return None
    try:
        payload = decode_token(auth.credentials)
        user_id = payload.get("sub")
        if user_id:
            return db.query(User).filter(User.id == int(user_id)).first()
    except Exception:
        return None
    return None

def get_active_couple(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> tuple[User, CoupleConnection]:
    """Ensure user is part of an active couple connection."""
    conn = db.query(CoupleConnection).filter(
        ((CoupleConnection.requester_id == current_user.id) | (CoupleConnection.recipient_id == current_user.id)),
        CoupleConnection.status == "accepted"
    ).first()

    if not conn:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No active couple connection found. Please connect with your partner first."
        )

    return current_user, conn
