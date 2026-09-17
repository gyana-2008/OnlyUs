from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.connection import CoupleConnection
from backend.app.models.notification import Notification
from backend.app.utils.security import get_current_user

router = APIRouter(prefix="/api/connections", tags=["connections"])

class ConnectionRequestPayload(BaseModel):
    target_uid: str = Field(..., description="Recipient's unique UID (e.g. BT-XXXXXX)")

class MilestoneUpdatePayload(BaseModel):
    relationship_start_date: str = Field(..., description="ISO Date string, e.g. 2024-02-14")
    anniversary_title: str | None = "Our Special Day"

@router.post("/request", status_code=status.HTTP_201_CREATED)
def send_connection_request(
    data: ConnectionRequestPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_uid = data.target_uid.strip().upper()
    if target_uid == current_user.uid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot connect with yourself")

    target_user = db.query(User).filter(User.uid == target_uid).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found with this UID")

    # Check if current user already has an active accepted connection
    my_active = db.query(CoupleConnection).filter(
        ((CoupleConnection.requester_id == current_user.id) | (CoupleConnection.recipient_id == current_user.id)),
        CoupleConnection.status == "accepted"
    ).first()
    if my_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an active couple space. Disconnect before connecting to a new partner."
        )

    # Check if target user already has an active accepted connection
    target_active = db.query(CoupleConnection).filter(
        ((CoupleConnection.requester_id == target_user.id) | (CoupleConnection.recipient_id == target_user.id)),
        CoupleConnection.status == "accepted"
    ).first()
    if target_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user is already connected in another private space."
        )

    # Check if there is an existing pending request between them
    existing_req = db.query(CoupleConnection).filter(
        ((CoupleConnection.requester_id == current_user.id) & (CoupleConnection.recipient_id == target_user.id)) |
        ((CoupleConnection.requester_id == target_user.id) & (CoupleConnection.recipient_id == current_user.id)),
        CoupleConnection.status == "pending"
    ).first()

    if existing_req:
        if existing_req.requester_id == current_user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Connection request already sent and pending")
        else:
            # The other person already sent a request to this user! Auto-accept or prompt to accept
            existing_req.status = "accepted"
            existing_req.accepted_at = datetime.now(timezone.utc)
            existing_req.relationship_start_date = datetime.now(timezone.utc)
            db.commit()
            return {"status": "accepted", "message": "Mutual request detected! Connected successfully."}

    # Create new connection
    conn = CoupleConnection(
        requester_id=current_user.id,
        recipient_id=target_user.id,
        status="pending",
        relationship_start_date=datetime.now(timezone.utc)
    )
    db.add(conn)

    # Send notification to target user
    notif = Notification(
        user_id=target_user.id,
        actor_id=current_user.id,
        type="connection_request",
        title="New Connection Request",
        message=f"{current_user.display_name} ({current_user.uid}) wants to connect your private space."
    )
    db.add(notif)
    db.commit()

    return {"status": "pending", "message": "Connection request sent successfully"}

@router.get("")
def get_connections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get active connection and any pending requests."""
    # Active connection
    active_conn = db.query(CoupleConnection).filter(
        ((CoupleConnection.requester_id == current_user.id) | (CoupleConnection.recipient_id == current_user.id)),
        CoupleConnection.status == "accepted"
    ).first()

    # Incoming pending requests
    incoming = db.query(CoupleConnection).filter(
        CoupleConnection.recipient_id == current_user.id,
        CoupleConnection.status == "pending"
    ).all()

    # Outgoing pending requests
    outgoing = db.query(CoupleConnection).filter(
        CoupleConnection.requester_id == current_user.id,
        CoupleConnection.status == "pending"
    ).all()

    return {
        "active": active_conn.to_dict(current_user.id) if active_conn else None,
        "incoming": [
            {
                "id": c.id,
                "requester": c.requester.to_public_partner_dict(),
                "created_at": c.created_at.isoformat()
            }
            for c in incoming
        ],
        "outgoing": [
            {
                "id": c.id,
                "recipient": c.recipient.to_public_partner_dict(),
                "created_at": c.created_at.isoformat()
            }
            for c in outgoing
        ]
    }

@router.post("/{connection_id}/accept")
def accept_connection(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conn = db.query(CoupleConnection).filter(
        CoupleConnection.id == connection_id,
        CoupleConnection.recipient_id == current_user.id,
        CoupleConnection.status == "pending"
    ).first()

    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending request not found")

    conn.status = "accepted"
    conn.accepted_at = datetime.now(timezone.utc)
    if not conn.relationship_start_date:
        conn.relationship_start_date = datetime.now(timezone.utc)

    # Notify requester
    notif = Notification(
        user_id=conn.requester_id,
        actor_id=current_user.id,
        type="connection_accepted",
        title="Connection Accepted",
        message=f"{current_user.display_name} accepted your connection. Your private space is now active!"
    )
    db.add(notif)
    db.commit()

    return {"status": "success", "message": "Connection accepted!", "connection": conn.to_dict(current_user.id)}

@router.post("/{connection_id}/reject")
def reject_connection(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conn = db.query(CoupleConnection).filter(
        CoupleConnection.id == connection_id,
        CoupleConnection.recipient_id == current_user.id,
        CoupleConnection.status == "pending"
    ).first()

    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending request not found")

    conn.status = "rejected"
    db.commit()
    return {"status": "success", "message": "Connection rejected"}

@router.delete("/{connection_id}")
def disconnect_partner(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect active partner space."""
    conn = db.query(CoupleConnection).filter(
        CoupleConnection.id == connection_id,
        ((CoupleConnection.requester_id == current_user.id) | (CoupleConnection.recipient_id == current_user.id)),
        CoupleConnection.status == "accepted"
    ).first()

    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active connection not found")

    partner_id = conn.get_partner_id(current_user.id)
    conn.status = "disconnected"

    # Notify partner
    notif = Notification(
        user_id=partner_id,
        actor_id=current_user.id,
        type="connection_disconnected",
        title="Space Disconnected",
        message=f"{current_user.display_name} has disconnected the private space."
    )
    db.add(notif)
    db.commit()

    return {"status": "success", "message": "Disconnected successfully"}

@router.put("/milestone")
def update_milestone(
    data: MilestoneUpdatePayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update 'Together Since' relationship start date."""
    conn = db.query(CoupleConnection).filter(
        ((CoupleConnection.requester_id == current_user.id) | (CoupleConnection.recipient_id == current_user.id)),
        CoupleConnection.status == "accepted"
    ).first()

    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active connection found")

    try:
        # Parse date
        date_obj = datetime.fromisoformat(data.relationship_start_date.replace("Z", "+00:00"))
        conn.relationship_start_date = date_obj
        if data.anniversary_title:
            conn.anniversary_title = data.anniversary_title.strip()
        db.commit()
        return {"status": "success", "relationship_start_date": conn.relationship_start_date.isoformat()}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid date format: {str(e)}")
