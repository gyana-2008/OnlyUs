import uuid
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.auth_service import generate_uid

client = TestClient(app)

def test_uid_generation():
    uid = generate_uid()
    assert uid.startswith("BT-")
    assert len(uid) == 9
    assert uid[3:].isalnum()

def test_user_registration_and_login():
    rand_id = uuid.uuid4().hex[:8]
    reg_data = {
        "email": f"test_{rand_id}@between.local",
        "username": f"user_{rand_id}",
        "password": "securepassword123",
        "display_name": f"User {rand_id}"
    }

    # Register
    res = client.post("/api/auth/register", json=reg_data)
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == reg_data["email"]
    assert data["user"]["uid"].startswith("BT-")
    token = data["access_token"]
    user_uid = data["user"]["uid"]

    # Duplicate registration rejected
    dup_res = client.post("/api/auth/register", json=reg_data)
    assert dup_res.status_code == 400

    # Login by email
    login_res = client.post("/api/auth/login", json={
        "login_identifier": reg_data["email"],
        "password": "securepassword123"
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # Login by UID
    login_uid_res = client.post("/api/auth/login", json={
        "login_identifier": user_uid,
        "password": "securepassword123"
    })
    assert login_uid_res.status_code == 200

    # Test me endpoint with bearer
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["username"] == reg_data["username"]

def test_pin_setup_and_verification():
    rand_id = uuid.uuid4().hex[:8]
    # Register user
    res = client.post("/api/auth/register", json={
        "email": f"pin_{rand_id}@between.local",
        "username": f"pin_{rand_id}",
        "password": "securepassword123",
        "display_name": "PIN Tester"
    })
    assert res.status_code == 201
    token = res.json()["access_token"]

    # Setup PIN
    pin_res = client.post(
        "/api/auth/setup-pin",
        json={"pin": "8492"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert pin_res.status_code == 200

    # Wrong PIN fails
    fail_res = client.post(
        "/api/auth/verify-pin",
        json={"pin": "0000"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert fail_res.status_code == 401

    # Correct PIN succeeds and returns scoped private token
    success_res = client.post(
        "/api/auth/verify-pin",
        json={"pin": "8492"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert success_res.status_code == 200
    assert "private_token" in success_res.json()
