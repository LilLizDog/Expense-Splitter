# Tests for the Friends API 
# Checks for adding, listing, and searching friends.

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.supabase_client import supabase

client = TestClient(app)

def clear_friends():
    # Only delete rows for the demo test user so we don't wipe out real data
    supabase.table("friends").delete().neq("id", 0).execute()


# Helper to make creating a test friend easier. 
def create_friend(name=None, email=None, group="TestGroup"):
    payload = {
        "name": name,
        "email": email,
        "group": group
    }
    return client.post("/api/friends/", json=payload)


def test_add_friend_inserts_correctly():
    clear_friends()
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
    clear_friends()
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
    clear_friends()
    """Search (q=) should filter by name OR email."""
    # Adding two specific test friends so I know what to expect.

    create_friend(name="Alice Wonder", email="alice@test.com")
    create_friend(name="Bob Stone", email="bob@test.com")

        # Searching by part of name, should return at least one Alice match
    resp = client.get("/api/friends/?q=alice")
    assert resp.status_code == 200
    data = resp.json()
    friends = data["friends"]

    # Make sure we got *some* results back
    assert len(friends) >= 1

    # And at least one of them is exactly "Alice Wonder"
    assert any(f["name"] == "Alice Wonder" for f in friends)


    # Searching by email, should return Bob
    resp = client.get("/api/friends/?q=bob@test.com")
    assert resp.status_code == 200
    data = resp.json()

    friends = data["friends"]

    # At least one of the results should be Bob's email
    assert any(f["email"] == "bob@test.com" for f in friends)

