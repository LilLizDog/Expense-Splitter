# tests/test_groups.py

import pytest

def test_create_group(client):
    """Test creating a new group."""
    payload = {
        "name": "Test Group",
        "description": "Demo group",
        "members": ["uuid-123"]  # matches the mock user in conftest
    }

    res = client.post("/groups/", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data.get("ok") is True
    assert data.get("group") is not None
    assert data["group"]["name"] == "Test Group"

def test_create_group_validation(client):
    """Test validation error when sending invalid data."""
    res = client.post("/groups/", json={
        "name": "",
        "description": "",
        "members": []
    })
    assert res.status_code == 400

def test_get_user_groups(client):
    """Test retrieving groups for a specific user."""
    user_id = "uuid-123"
    res = client.get(f"/groups/user/{user_id}")
    assert res.status_code == 200
    data = res.json()
    assert "groups" in data
    assert isinstance(data["groups"], list)

def test_get_group_members(client):
    """Test retrieving members of a group."""
    group_id = "xyz"
    res = client.get(f"/groups/{group_id}/members")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    # Each member should have id, name, email
    if data:
        member = data[0]
        assert "id" in member
        assert "name" in member
        assert "email" in member

def test_get_nonexistent_group_members(client):
    """Test retrieving members for a group that does not exist."""
    res = client.get("/groups/nonexistent-group/members")
    assert res.status_code == 404
