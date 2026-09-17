from datetime import datetime, timedelta, date, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.user import User, UserSettings
from backend.app.models.connection import CoupleConnection
from backend.app.models.message import Message
from backend.app.models.memory import Memory
from backend.app.models.shared import SharedNote, ImportantDate
from backend.app.services.auth_service import hash_secret, create_access_token, create_private_token

router = APIRouter(prefix="/api/demo", tags=["demo"])

def check_demo_enabled():
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo Mode is disabled in this environment."
        )

@router.get("/status")
def demo_status():
    return {
        "demo_mode_enabled": settings.DEMO_MODE,
        "environment": settings.ENVIRONMENT
    }

@router.post("/seed")
def seed_demo_data(db: Session = Depends(get_db)):
    check_demo_enabled()

    # Clear previous demo accounts cleanly
    demo_users = db.query(User).filter(User.is_demo == True).all()
    for du in demo_users:
        db.delete(du)
    db.commit()

    # 1. Create Demo User A: Alex
    alex = User(
        uid="BT-ALEX01",
        email="alex@between.local",
        username="alex",
        hashed_password=hash_secret("demo1234"),
        hashed_pin=hash_secret("1234"),
        display_name="Alex Vance",
        avatar_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80",
        bio="Architecture & design. Currently based in New York.",
        status_message="Thinking of you 💕",
        is_demo=True,
    )
    db.add(alex)
    db.flush()

    alex_settings = UserSettings(
        user_id=alex.id,
        location_sharing_level="city_only",
        latitude=40.7128,
        longitude=-74.0060,
        city="New York",
        country="United States"
    )
    db.add(alex_settings)

    # 2. Create Demo User B: Maya
    maya = User(
        uid="BT-MAYA02",
        email="maya@between.local",
        username="maya",
        hashed_password=hash_secret("demo1234"),
        hashed_pin=hash_secret("1234"),
        display_name="Maya Lin",
        avatar_url="https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=300&q=80",
        bio="Curator & researcher. Living in London.",
        status_message="Listening to rain & writing ☕",
        is_demo=True,
    )
    db.add(maya)
    db.flush()

    maya_settings = UserSettings(
        user_id=maya.id,
        location_sharing_level="city_only",
        latitude=51.5074,
        longitude=-0.1278,
        city="London",
        country="United Kingdom"
    )
    db.add(maya_settings)

    # 3. Create active Couple Connection
    # Start date set to Oct 14, 2023
    together_date = datetime(2023, 10, 14, 18, 30, 0, tzinfo=timezone.utc)
    conn = CoupleConnection(
        requester_id=alex.id,
        recipient_id=maya.id,
        status="accepted",
        relationship_start_date=together_date,
        anniversary_title="Our First Day in Kyoto",
        accepted_at=together_date,
        created_at=together_date
    )
    db.add(conn)
    db.flush()

    # 4. Seed realistic conversation
    now = datetime.now(timezone.utc)
    demo_msgs = [
        (alex.id, maya.id, "Good morning from NYC! Just woke up and saw your note. How is London today? ☀️", None, None, now - timedelta(hours=5)),
        (maya.id, alex.id, "Morning love! Rainy as usual, but drinking hot Earl Grey tea at my favorite bookshop.", None, None, now - timedelta(hours=4, minutes=45)),
        (alex.id, maya.id, "Sending you a little view from my studio window.", "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?auto=format&fit=crop&w=800&q=80", "image", now - timedelta(hours=3)),
        (maya.id, alex.id, "That light is magical! Can't wait until our flight next month.", None, None, now - timedelta(hours=2, minutes=30)),
        (alex.id, maya.id, "Me too. 28 days left on our countdown card!", None, None, now - timedelta(minutes=40)),
        (maya.id, alex.id, "Counting down every second 💕", None, None, now - timedelta(minutes=15)),
    ]

    for s_id, r_id, content, media_url, media_type, created_time in demo_msgs:
        m = Message(
            connection_id=conn.id,
            sender_id=s_id,
            recipient_id=r_id,
            content=content,
            media_url=media_url,
            media_type=media_type,
            read_at=created_time + timedelta(minutes=2),
            created_at=created_time
        )
        db.add(m)

    # 5. Seed Shared Memories
    memories = [
        Memory(
            connection_id=conn.id,
            author_id=alex.id,
            title="The Bamboo Forest in Arashiyama",
            story="We got lost looking for tea in Kyoto and ended up finding the quietest temple garden right at sunset.",
            memory_date=date(2023, 10, 15),
            tag="Trip",
            media_url="https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=800&q=80",
            media_type="image",
            is_favorite=True,
            created_at=now - timedelta(days=200)
        ),
        Memory(
            connection_id=conn.id,
            author_id=maya.id,
            title="First Anniversary Picnic at Primrose Hill",
            story="Strawberries, handmade sourdough, and looking out over the London skyline under golden hour.",
            memory_date=date(2024, 10, 14),
            tag="Anniversary",
            media_url="https://images.unsplash.com/photo-1517457373958-b7bdd4587205?auto=format&fit=crop&w=800&q=80",
            media_type="image",
            is_favorite=True,
            created_at=now - timedelta(days=120)
        ),
        Memory(
            connection_id=conn.id,
            author_id=alex.id,
            title="Late Night Stargazing in the Catskills",
            story="Wrapped in wool blankets on the wooden cabin porch. We spotted four shooting stars in twenty minutes.",
            memory_date=date(2024, 12, 31),
            tag="Date Night",
            media_url="https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80",
            media_type="image",
            is_favorite=False,
            created_at=now - timedelta(days=60)
        )
    ]
    for mem in memories:
        db.add(mem)

    # 6. Seed Shared Note
    note = SharedNote(
        connection_id=conn.id,
        author_id=maya.id,
        title="Our Next European Summer Itinerary",
        content="1. Zurich train through the Alps\n2. Lake Como weekend\n3. Gelato in Florence\n4. Sunset ferry in Positano",
        is_pinned=True,
        created_at=now - timedelta(days=10)
    )
    db.add(note)

    db.commit()

    return {
        "status": "success",
        "message": "Demo data seeded successfully!",
        "accounts": [
            {"name": "Alex", "email": "alex@between.local", "uid": "BT-ALEX01", "pin": "1234"},
            {"name": "Maya", "email": "maya@between.local", "uid": "BT-MAYA02", "pin": "1234"},
        ]
    }

@router.post("/switch/{user_key}")
def switch_demo_user(user_key: str, db: Session = Depends(get_db)):
    """Instant 1-click login switch for developers/testers to switch between Alex and Maya."""
    check_demo_enabled()
    
    email = "alex@between.local" if user_key.lower() == "alex" else "maya@between.local"
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # If demo accounts haven't been seeded yet, seed them now
        seed_demo_data(db)
        user = db.query(User).filter(User.email == email).first()

    token = create_access_token({"sub": str(user.id), "uid": user.uid})
    private_token = create_private_token(user.id)

    return {
        "status": "success",
        "access_token": token,
        "private_token": private_token,
        "token_type": "bearer",
        "user": user.to_dict()
    }

@router.post("/reset")
def reset_demo_data(db: Session = Depends(get_db)):
    check_demo_enabled()
    demo_users = db.query(User).filter(User.is_demo == True).all()
    for du in demo_users:
        db.delete(du)
    db.commit()
    return {"status": "success", "message": "Demo data cleared"}
