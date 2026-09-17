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

    # Get single memory
    single_res = client.get(f"/api/memories/{mem_id}", headers={"Authorization": f"Bearer {token}"})
    assert single_res.status_code == 200
    assert single_res.json()["title"] == "Sunset on Santorini cliffs"

    # Update (change) memory
    update_res = client.put(
        f"/api/memories/{mem_id}",
        json={
            "title": "Golden Sunset on Oia cliffs",
            "story": "Updated note: The view of the Aegean caldera was breathtaking.",
            "memory_date": "2024-06-16",
            "tag": "Date Night",
            "is_favorite": False
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["title"] == "Golden Sunset on Oia cliffs"
    assert updated_data["tag"] == "Date Night"
    assert updated_data["is_favorite"] is False

    # Partner Maya can view and edit the shared memory
    maya_auth = client.post("/api/demo/switch/maya").json()
    maya_token = maya_auth["access_token"]
    maya_get = client.get(f"/api/memories/{mem_id}", headers={"Authorization": f"Bearer {maya_token}"})
    assert maya_get.status_code == 200
    assert maya_get.json()["title"] == "Golden Sunset on Oia cliffs"

    # Delete memory
    del_res = client.delete(f"/api/memories/{mem_id}", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # Verify deleted
    get_deleted = client.get(f"/api/memories/{mem_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_deleted.status_code == 404
