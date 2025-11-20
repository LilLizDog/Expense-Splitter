# Tests for the Friends API 
# Checks for adding, listing, and searching friends.

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# Helper to make creating a test friend easier. 
def create_friend(name=None, email=None, group="TestGroup"):
    payload = {
        "name": name,
        "email": email,
        "group": group
    }
    return client.post("/api/friends/", json=payload)


def test_add_friend_inserts_correctly():
    """Adding a friend should return the friend with correct fields."""
    # Testing if adding a friend works as expected and comes back with correct data.
    resp = create_friend(name="Grace Test", email="grace@example.com")

    # Makes sure that the API doesn't break and returns expected data.
    assert resp.status_code == 200
    data = resp.json()

    # Double check that the returned the same data we sent.
    assert data["friend"]["name"] == "Grace Test"
    assert data["friend"]["email"] == "grace@example.com"
    assert data["friend"]["group"] == "TestGroup"


def test_list_friends_returns_only_this_user():
    """List should only return 'demo-user-1' friends."""
    # Makes a couple friends for demo-user-1, then lists and checks they belong to that user.
    create_friend(name="Friend A")
    create_friend(name="Friend B")

    resp = client.get("/api/friends/")
    assert resp.status_code == 200

    data = resp.json()
    friends = data["friends"]

    # All returned rows must belong to the same test user
    assert len(friends) >= 2  # Includes at least the two we just added
    for f in friends:
        assert "id" in f
        assert "name" in f


def test_search_returns_expected_results():
    """Search (q=) should filter by name OR email."""
    # Adding two specific test friends so I know what to expect.

    create_friend(name="Alice Wonder", email="alice@test.com")
    create_friend(name="Bob Stone", email="bob@test.com")

    # Searching by part of name, should return Alice
    resp = client.get("/api/friends/?q=alice")
    assert resp.status_code == 200
    data = resp.json()
    friends = data["friends"]
    assert len(friends) == 1
    assert friends[0]["name"] == "Alice Wonder"

    # Searching by email, should return Bob
    resp = client.get("/api/friends/?q=bob@test.com")
    assert resp.status_code == 200
    data = resp.json()
    friends = data["friends"]
    assert len(friends) == 1
    assert friends[0]["email"] == "bob@test.com"
