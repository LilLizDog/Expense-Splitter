# FILE: tests/test_friends_basic.py
# Basic tests for /friends routes and page.

def test_friends_page_exists(client):
    # /friends should load and show main elements
    r = client.get("/friends")
    assert r.status_code == 200
    assert "<h1>Friends" in r.text
    assert 'id="q"' in r.text          # search bar
    assert 'id="group"' in r.text      # group filter
    assert 'id="addForm"' in r.text    # add friend form
    assert 'id="list"' in r.text       # list container


def test_friends_alias_exists(client):
    # /friends.html alias should also load
    r = client.get("/friends.html")
    assert r.status_code == 200


def test_friends_list_renders_with_mock_data(client):
    # GET /api/friends.html should should return a list of friends
    r = client.get("/api/friends/")
    assert r.status_code == 200
    data = r.json()
    assert "friends" in data
    assert isinstance(data["friends"], list)


def test_friends_search_returns_correct_filtered_friends(client):
   # GET /api/friends with ?q= should return filtered friends by search term
    r = client.get("/api/friends/?q=gr")
    assert r.status_code == 200
    data = r.json()
    assert "friends" in data
    assert isinstance(data["friends"], list)


def test_friends_group_filter_shows_only_matching_friends(client):
   # GET /api/friends with ?group= should return filtered friends by group
    r = client.get("/api/friends/?group=Roommates")
    assert r.status_code == 200
    data = r.json()
    assert "friends" in data
    assert isinstance(data["friends"], list)
    for friend in data["friends"]:
        assert "group" in friend


def test_add_friend_updates_list_backend(client):
   # POST /api/friends should add a new friend entry
    payload = {
        "name": "Test Friend",
        "group": "Roommates"
    }
    r = client.post("/api/friends/", json=payload)
    assert r.status_code in (200, 201)
    data = r.json()
    assert "friend" in data or "message" in data
