import pytest
from fastapi.testclient import TestClient
from app.main import app

# FakeResponse just to mimic Supabase response structure
class FakeResponse:
    def __init__(self, data=None):
        self.data = data

# This class pretends to be the query builder for a Supabase table
# Instead of actually talking to a database, it just manipulates an in-memory list
class FakeQuery:
    def __init__(self, store):
        self.store = store
        self.mode = None
        self.payload = None
        self.filters = {}
        self._order_desc = False
        self._limit = None

    # Pretend SELECT(*)
    def select(self, *_args):
        self.mode = "select"
        return self

    #Pretend INSERT
    def insert(self, payload, **_kwargs):
        self.mode = "insert"
        self.payload = payload
        return self

    # Pretend UPDATE
    def update(self, payload, **_kwargs):
        self.mode = "update"
        self.payload = payload
        return self

    # Pretend .eq("column", value)
    def eq(self, col, val):
        self.filters[col] = val
        return self

    # Pretend .order(..., desc=bool)
    def order(self, _col, desc=False):
        self._order_desc = desc
        return self

    # Pretend .limit(n)
    def limit(self, n):
        self._limit = n
        return self

    # This performs the fake query and returns a FakeResponse
    def execute(self):
        user_id = self.filters.get("user_id")

        # SELECT
        if self.mode == "select":
            # Pull rows matching user_id
            rows = [r for r in self.store if r["user_id"] == user_id]
            rows.sort(key=lambda r: r["created_at"], reverse=self._order_desc)
            # Apply limit if any
            if self._limit:
                rows = rows[: self._limit]
            return FakeResponse(rows)

        # INSERT
        if self.mode == "insert":
            new_id = len(self.store) + 1
            row = {
                "id": new_id,
                "created_at": new_id,  # simple increasing timestamp
                **self.payload,
            }
            self.store.append(row)
            return FakeResponse([row])

        # UPDATE
        if self.mode == "update":
            settings_id = self.filters.get("id")

            # If update is filtering by id, which matches how we do it in the router
            if settings_id is not None:
                rows = [r for r in self.store if r["id"] == settings_id]
            else:
                # Otherwise update by user_id
                rows = [r for r in self.store if r["user_id"] == user_id]

            if not rows:
                return FakeResponse([])

            # Only one row should match
            row = rows[0]
            row.update(self.payload)
            return FakeResponse([row])


# FakeSupabase to mimic supabase client
class FakeSupabase:
    def __init__(self, store):
        self.store = store

    def table(self, _name):
        return FakeQuery(self.store)


# Replaces the supabase client in the settings router with our fake
@pytest.fixture
def fake_client(monkeypatch):
    """
    Update the settings router to utilize our FakeSupabase instead of the actual one.
    """
    fake_store = []

    from app.routers import settings as settings_router
    monkeypatch.setattr(settings_router, "supabase", FakeSupabase(fake_store))

    return TestClient(app), fake_store



def test_default_settings_created(fake_client):
    client, store = fake_client

    # Verify the database is empty to start
    assert len(store) == 0

    # GET settings, should create default row
    r = client.get("/api/settings/")
    assert r.status_code == 200
    data = r.json()

    # Defaults should match expected values
    assert data["theme"] == "light"
    assert data["font_size"] == "normal"
    assert data["notifications_enabled"] is True

    # Only one row should exist now
    assert len(store) == 1


def test_settings_save_updates_existing_row(fake_client):
    client, store = fake_client

    # Create default first
    client.get("/api/settings/")
    assert len(store) == 1

    # Change settings
    payload = {
        "notifications_enabled": False,
        "theme": "dark",
        "font_size": "large",
    }

    r = client.post("/api/settings/", json=payload)
    assert r.status_code == 200

    updated = r.json()["settings"]

    # Verify the changes were applied and saved
    assert updated["theme"] == "dark"
    assert updated["font_size"] == "large"
    assert updated["notifications_enabled"] is False

    # Still only one row should exist 
    assert len(store) == 1


def test_settings_loads_saved_preferences(fake_client):
    client, store = fake_client

    # Create default first
    client.get("/api/settings/")

    # Update settings to non-defaults
    client.post("/api/settings/", json={
        "notifications_enabled": True,
        "theme": "dark",
        "font_size": "xlarge"
    })

    # GET to verify we load the updated settings
    r = client.get("/api/settings/")
    assert r.status_code == 200
    data = r.json()

    # verify everything matches what we saved
    assert data["theme"] == "dark"
    assert data["font_size"] == "xlarge"
    assert data["notifications_enabled"] is True
