import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_news_system_resilience():
    # Fetch all news
    res = client.get("/api/news")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["count"] > 0
    assert len(data["articles"]) > 0

    # Category filter
    world_res = client.get("/api/news?category=world")
    assert world_res.status_code == 200
    assert len(world_res.json()["articles"]) > 0
    assert all(a["category"].lower() == "world" for a in world_res.json()["articles"])

    # Search filter
    search_res = client.get("/api/news?search=climate")
    assert search_res.status_code == 200
    assert len(search_res.json()["articles"]) >= 1

    # Article detail by ID
    first_id = data["articles"][0]["id"]
    detail_res = client.get(f"/api/news/{first_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == first_id
    assert "content" in detail_res.json()
