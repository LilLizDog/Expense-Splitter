# tests/test_groups.py
import os

# --- Ensure supabase_client.py doesn't raise ValueError ---
os.environ["SUPABASE_URL"] = "http://fake-url"
os.environ["SUPABASE_KEY"] = "fake-key"
os.environ["TESTING"] = "1"  # triggers in-memory fake client

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# --- Tests ---
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
