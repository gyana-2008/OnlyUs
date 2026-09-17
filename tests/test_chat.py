import uuid
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_chat_messaging_workflow():
    # 1. Use demo switch to get tokens for Alex and Maya
    alex_auth = client.post("/api/demo/switch/alex").json()
    token_alex = alex_auth["access_token"]

    maya_auth = client.post("/api/demo/switch/maya").json()
    token_maya = maya_auth["access_token"]

    # Alex sends message
    send_res = client.post(
        "/api/chat/messages",
        json={"content": "Hey Maya, are you free for a call tonight?"},
        headers={"Authorization": f"Bearer {token_alex}"}
    )
    assert send_res.status_code == 201
    msg_data = send_res.json()
    assert msg_data["content"] == "Hey Maya, are you free for a call tonight?"
    msg_id = msg_data["id"]

    # Maya replies
    reply_res = client.post(
        "/api/chat/messages",
        json={
            "content": "Yes! Around 8pm London time works perfectly.",
            "reply_to_id": msg_id
        },
        headers={"Authorization": f"Bearer {token_maya}"}
    )
    assert reply_res.status_code == 201
    assert reply_res.json()["reply_to"]["id"] == msg_id

    # Maya fetches messages (which marks incoming messages as read)
    fetch_res = client.get("/api/chat/messages", headers={"Authorization": f"Bearer {token_maya}"})
    assert fetch_res.status_code == 200
    messages = fetch_res.json()
    assert len(messages) >= 2

    # Alex deletes a message
    del_res = client.delete(f"/api/chat/messages/{msg_id}", headers={"Authorization": f"Bearer {token_alex}"})
    assert del_res.status_code == 200

    # Thinking of you reaction
    ping_res = client.post("/api/chat/thinking-of-you", json={}, headers={"Authorization": f"Bearer {token_alex}"})
    assert ping_res.status_code == 200

def test_chat_security_isolation():
    rand_id = uuid.uuid4().hex[:6]
    # Register an unconnected third user
    third_res = client.post("/api/auth/register", json={
        "email": f"intruder_{rand_id}@between.local",
        "username": f"intruder_{rand_id}",
        "password": "password123",
        "display_name": "Intruder"
    })
    assert third_res.status_code == 201
    third_token = third_res.json()["access_token"]

    # Attempting to fetch or send messages fails with 403 Forbidden
    fetch_res = client.get("/api/chat/messages", headers={"Authorization": f"Bearer {third_token}"})
    assert fetch_res.status_code == 403

    send_res = client.post(
        "/api/chat/messages",
        json={"content": "Unauthorized message"},
        headers={"Authorization": f"Bearer {third_token}"}
    )
    assert send_res.status_code == 403
