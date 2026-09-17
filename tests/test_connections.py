import uuid
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_couple_connection_lifecycle():
    rand_a = uuid.uuid4().hex[:6]
    rand_b = uuid.uuid4().hex[:6]

    # Register User A
    res_a = client.post("/api/auth/register", json={
        "email": f"alpha_{rand_a}@between.local",
        "username": f"alpha_{rand_a}",
        "password": "password123",
        "display_name": "Alpha"
    })
    assert res_a.status_code == 201
    token_a = res_a.json()["access_token"]
    uid_a = res_a.json()["user"]["uid"]

    # Register User B
    res_b = client.post("/api/auth/register", json={
        "email": f"beta_{rand_b}@between.local",
        "username": f"beta_{rand_b}",
        "password": "password123",
        "display_name": "Beta"
    })
    assert res_b.status_code == 201
    token_b = res_b.json()["access_token"]
    uid_b = res_b.json()["user"]["uid"]

    # Alpha searches for Beta by UID
    search_res = client.get(f"/api/users/search?uid={uid_b}", headers={"Authorization": f"Bearer {token_a}"})
    assert search_res.status_code == 200
    assert search_res.json()["display_name"] == "Beta"

    # Self connection attempt fails
    self_res = client.post("/api/connections/request", json={"target_uid": uid_a}, headers={"Authorization": f"Bearer {token_a}"})
    assert self_res.status_code == 400

    # Alpha sends request to Beta
    req_res = client.post("/api/connections/request", json={"target_uid": uid_b}, headers={"Authorization": f"Bearer {token_a}"})
    assert req_res.status_code == 201

    # Beta checks incoming requests
    conn_list_res = client.get("/api/connections", headers={"Authorization": f"Bearer {token_b}"})
    assert conn_list_res.status_code == 200
    incoming = conn_list_res.json()["incoming"]
    assert len(incoming) >= 1
    req_id = [r["id"] for r in incoming if r["requester"]["uid"] == uid_a][0]

    # Beta accepts request
    accept_res = client.post(f"/api/connections/{req_id}/accept", headers={"Authorization": f"Bearer {token_b}"})
    assert accept_res.status_code == 200
    assert accept_res.json()["connection"]["status"] == "accepted"

    # Both users now see active connection in /me
    me_a = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_a}"}).json()
    me_b = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_b}"}).json()
    assert me_a["connection"] is not None
    assert me_b["connection"] is not None
    assert me_a["connection"]["partner"]["display_name"] == "Beta"
    assert me_b["connection"]["partner"]["display_name"] == "Alpha"

    # Update relationship start date milestone
    milestone_res = client.put(
        "/api/connections/milestone",
        json={"relationship_start_date": "2024-02-14T00:00:00"},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert milestone_res.status_code == 200

    # Disconnect
    active_conn_id = me_a["connection"]["id"]
    disc_res = client.delete(f"/api/connections/{active_conn_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert disc_res.status_code == 200

    # Connection should now be disconnected
    me_after = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_a}"}).json()
    assert me_after["connection"] is None
