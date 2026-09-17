import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_memories_and_analytics():
    alex_auth = client.post("/api/demo/switch/alex").json()
    token = alex_auth["access_token"]

    # Create memory
    create_res = client.post(
        "/api/memories",
        json={
            "title": "Sunset on Santorini cliffs",
            "story": "Watching the golden hour over the Aegean caldera with white wine.",
            "memory_date": "2024-06-15",
            "tag": "Trip",
            "is_favorite": True
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_res.status_code == 201
    mem_id = create_res.json()["id"]

    # List memories
    list_res = client.get("/api/memories", headers={"Authorization": f"Bearer {token}"})
    assert list_res.status_code == 200
    assert any(m["id"] == mem_id for m in list_res.json())

    # Tag filter
    filter_res = client.get("/api/memories?tag=Trip", headers={"Authorization": f"Bearer {token}"})
    assert filter_res.status_code == 200
    assert all(m["tag"] == "Trip" for m in filter_res.json())

    # Toggle favorite
    fav_res = client.post(f"/api/memories/{mem_id}/favorite", headers={"Authorization": f"Bearer {token}"})
    assert fav_res.status_code == 200

    # Analytics stats
    stats_res = client.get("/api/memories/stats", headers={"Authorization": f"Bearer {token}"})
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "days_together" in stats
    assert stats["days_together"] >= 1
    assert "memories_count" in stats
    assert "monthly_activity" in stats
