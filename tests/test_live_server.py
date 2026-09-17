import requests

def test_live_server_endpoints():
    base = "http://127.0.0.1:8000"
    pages = [
        "/",
        "/news.html",
        "/article.html",
        "/private.html",
        "/chat.html",
        "/memories.html",
        "/settings.html",
        "/login.html",
        "/register.html"
    ]
    assets = [
        "/css/base.css",
        "/css/news.css",
        "/css/private.css",
        "/css/chat.css",
        "/css/memories.css",
        "/css/components.css",
        "/js/api.js",
        "/js/news.js",
        "/js/auth.js",
        "/js/dashboard.js",
        "/js/chat.js",
        "/js/memories.js",
        "/js/settings.js",
        "/js/demo.js"
    ]

    for p in pages:
        res = requests.get(base + p)
        assert res.status_code == 200, f"Page {p} returned {res.status_code}"
        assert len(res.text) > 50, f"Page {p} is empty"

    for a in assets:
        res = requests.get(base + a)
        assert res.status_code == 200, f"Asset {a} returned {res.status_code}"
        assert len(res.text) > 50, f"Asset {a} is empty"

    # Test Demo Switch on live running server
    demo_res = requests.post(base + "/api/demo/switch/alex")
    assert demo_res.status_code == 200
    token = demo_res.json()["access_token"]

    # Test /api/auth/me
    me_res = requests.get(base + "/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["display_name"] == "Alex Vance"
    assert me_data["connection"]["partner"]["display_name"] == "Maya Lin"

    # Test news API
    news_res = requests.get(base + "/api/news")
    assert news_res.status_code == 200
    assert news_res.json()["count"] > 0
