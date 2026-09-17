import io
import uuid
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_full_user_journey_and_media_upload():
    r_em = uuid.uuid4().hex[:6]
    r_li = uuid.uuid4().hex[:6]

    # 1. Register User Emily
    res_emily = client.post("/api/auth/register", json={
        "email": f"emily_{r_em}@between.domain",
        "username": f"emily_{r_em}",
        "password": "EmilyPassword123!",
        "display_name": "Emily"
    })
    assert res_emily.status_code == 201
    emily_data = res_emily.json()
    token_emily = emily_data["access_token"]
    uid_emily = emily_data["user"]["uid"]

    # 2. Register User Liam
    res_liam = client.post("/api/auth/register", json={
        "email": f"liam_{r_li}@between.domain",
        "username": f"liam_{r_li}",
        "password": "LiamPassword123!",
        "display_name": "Liam"
    })
    assert res_liam.status_code == 201
    liam_data = res_liam.json()
    token_liam = liam_data["access_token"]
    uid_liam = liam_data["user"]["uid"]

    # 3. Emily configures her Private PIN
    pin_res = client.post(
        "/api/auth/setup-pin",
        json={"pin": "5566"},
        headers={"Authorization": f"Bearer {token_emily}"}
    )
    assert pin_res.status_code == 200

    # 4. Emily verifies PIN and gets scoped private token
    unlock_res = client.post(
        "/api/auth/verify-pin",
        json={"pin": "5566"},
        headers={"Authorization": f"Bearer {token_emily}"}
    )
    assert unlock_res.status_code == 200
    private_token_emily = unlock_res.json()["private_token"]

    # 5. Emily searches for Liam by UID and sends request
    search_res = client.get(f"/api/users/search?uid={uid_liam}", headers={"Authorization": f"Bearer {token_emily}"})
    assert search_res.status_code == 200
    assert search_res.json()["display_name"] == "Liam"

    req_res = client.post(
        "/api/connections/request",
        json={"target_uid": uid_liam},
        headers={"Authorization": f"Bearer {token_emily}"}
    )
    assert req_res.status_code == 201

    # 6. Liam checks incoming requests and accepts
    conn_res = client.get("/api/connections", headers={"Authorization": f"Bearer {token_liam}"})
    incoming = conn_res.json()["incoming"]
    assert len(incoming) >= 1
    target_req_id = [req["id"] for req in incoming if req["requester"]["uid"] == uid_emily][0]

    accept_res = client.post(f"/api/connections/{target_req_id}/accept", headers={"Authorization": f"Bearer {token_liam}"})
    assert accept_res.status_code == 200

    # 7. Both users now share an active space. Test sending a photo attachment!
    fake_image_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00" + (b"\x00" * 50)
    upload_res = client.post(
        "/api/chat/upload",
        files={"file": ("moment.jpg", fake_image_bytes, "image/jpeg")},
        headers={"Authorization": f"Bearer {token_emily}"}
    )
    assert upload_res.status_code == 200
    uploaded_url = upload_res.json()["media_url"]
    assert uploaded_url.startswith("/uploads/")

    # 8. Emily sends message with the photo
    photo_msg_res = client.post(
        "/api/chat/messages",
        json={
            "content": "Our view this afternoon",
            "media_url": uploaded_url,
            "media_type": "image"
        },
        headers={"Authorization": f"Bearer {token_emily}"}
    )
    assert photo_msg_res.status_code == 201

    # 9. Liam fetches conversation and sees the photo message
    msgs_res = client.get("/api/chat/messages", headers={"Authorization": f"Bearer {token_liam}"})
    assert msgs_res.status_code == 200
    all_msgs = msgs_res.json()
    assert any(m["media_url"] == uploaded_url for m in all_msgs)

    # 10. Test Location distance between New York and Paris
    client.post(
        "/api/location/update",
        json={"latitude": 40.7128, "longitude": -74.0060, "city": "New York", "country": "USA"},
        headers={"Authorization": f"Bearer {token_emily}"}
    )
    client.put("/api/location/permission", json={"sharing_level": "city_only"}, headers={"Authorization": f"Bearer {token_emily}"})

    client.post(
        "/api/location/update",
        json={"latitude": 48.8566, "longitude": 2.3522, "city": "Paris", "country": "France"},
        headers={"Authorization": f"Bearer {token_liam}"}
    )
    client.put("/api/location/permission", json={"sharing_level": "city_only"}, headers={"Authorization": f"Bearer {token_liam}"})

    dist_res = client.get("/api/location/distance", headers={"Authorization": f"Bearer {token_emily}"})
    assert dist_res.status_code == 200
    dist_data = dist_res.json()
    assert dist_data["allowed"] is True
    assert dist_data["distance_km"] > 5800  # NY to Paris is ~5830 km
    assert dist_data["my_city"] == "New York"
    assert dist_data["partner_city"] == "Paris"

    # 11. Test Notifications
    notifs_res = client.get("/api/users/notifications/list", headers={"Authorization": f"Bearer {token_liam}"})
    assert notifs_res.status_code == 200
    assert len(notifs_res.json()) >= 1

    read_res = client.post("/api/users/notifications/read-all", headers={"Authorization": f"Bearer {token_liam}"})
    assert read_res.status_code == 200
