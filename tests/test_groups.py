from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_group():
    payload = {
        "name": "Test Group",
        "description": "Demo",
        "members": ["uuid-123"]
    }

    res = client.post("/groups/", json=payload)
    assert res.status_code == 200
    assert res.json()["ok"] is True

def test_group_validation():
    res = client.post("/groups/", json={
        "name": "",
        "description": "",
        "members": []
    })
    assert res.status_code == 400

def test_get_user_groups():
    res = client.get("/groups/user/uuid-123")
    assert res.status_code == 200
    assert "groups" in res.json()

def test_get_group_members():
    res = client.get("/groups/xyz/members")
    # 200 if valid, 404 if not found
    assert res.status_code in (200, 404)
