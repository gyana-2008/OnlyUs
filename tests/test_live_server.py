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

    # Verify Hidden Entry Point on Public News Page
    home_res = requests.get(base + "/")
    assert home_res.status_code == 200
    home_html = home_res.text
    # 1. Masthead brand logo trigger must exist
    assert 'id="brand-title-trigger"' in home_html
    # 2. Secret glyph trigger must NOT exist in the public edition bar
    assert 'secret-glyph-trigger' not in home_html
    # 3. Private space selection modal markup must exist
    assert 'id="secret-choice-view"' in home_html
    assert 'Demo Account' in home_html
    assert 'Real Account' in home_html
    # 4. Public HTML must NOT render DEV DEMO banner
    assert 'dev-demo-banner' not in home_html
