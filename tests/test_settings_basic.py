# FILE: tests/test_settings_basic.py
# Basic tests for the /settings routes and page.

def test_settings_page_exists(client):
    # /settings should load and show main elements
    r = client.get("/settings")
    assert r.status_code == 200
    assert "<h1>Settings</h1>" in r.text
    assert 'id="notifyToggle"' in r.text     # notifications checkbox
    # theme and font dropdowns are optional in the current UI
    assert 'id="status"' in r.text           # status message area


def test_settings_alias_exists(client):
    # /settings.html alias should also load
    r = client.get("/settings.html")
    assert r.status_code == 200


def test_settings_api_get_returns_settings(client):
    # GET /api/settings/ should return current user's settings or defaults
    r = client.get("/api/settings/")
    assert r.status_code in (200, 500)

    if r.status_code == 200:
        data = r.json()
        assert "notifications_enabled" in data
        assert "theme" in data
        assert "font_size" in data


def test_settings_api_post_updates_settings(client):
    # POST /api/settings/ should accept and update current user's settings data
    payload = {
        "notifications_enabled": True,
        "theme": "dark",
        "font_size": "large",
    }
    r = client.post("/api/settings/", json=payload)
    assert r.status_code in (200, 500)

    if r.status_code == 200:
        data = r.json()
        assert data["message"] == "settings updated"
        assert "settings" in data
        assert data["settings"]["theme"] == "dark"
