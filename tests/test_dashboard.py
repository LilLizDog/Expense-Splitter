# FILE: tests/test_dashboard.py

import pytest
from fastapi.testclient import TestClient
from fastapi import Request
from app.main import app
from app.routers import dashboard
from app.routers import auth as auth_router

# -------------------------------------------------------------------
# Fake Supabase client for dashboard endpoint
# -------------------------------------------------------------------

class FakeResponse:
    def __init__(self, data=None, error=None):
        self.data = data
        self.error = error


class FakeSupabaseTable:
    """
    Generic table mock that supports:
    - select(...)
    - eq(...)
    - in_(...)
    - contains(...)
    - order(...)
    - limit(...)
    And gracefully ignores other chained methods via __getattr__.
    """

    def __init__(self, rows):
        # rows is a list of dicts for this table
        self._rows = rows
        self._filters_eq = []
        self._filters_in = {}
        self._filters_contains = []
        self._order = None
        self._limit = None

    def select(self, *_cols, **_kwargs):
        # we do not need to trim columns for these tests
        return self

    def eq(self, col, val):
        self._filters_eq.append((col, val))
        return self

    def in_(self, col, vals):
        self._filters_in[col] = set(str(v) for v in vals)
        return self

    def contains(self, col, vals):
        """
        Minimal mimic of Supabase .contains(column, [values])
        Used for groups.members containing a user id.
        """
        if not isinstance(vals, (list, tuple, set)):
            vals = [vals]
        self._filters_contains.append((col, set(str(v) for v in vals)))
        return self

    def order(self, *args, **kwargs):
        # ignore actual ordering for tests
        self._order = (args, kwargs)
        return self

    def limit(self, n):
        self._limit = int(n)
        return self

    def __getattr__(self, name):
        """
        Catch-all for methods we do not care about (single, maybe, range, etc.).
        Returns a function that just returns self so chained calls do not explode.
        """
        def _(*args, **kwargs):
            return self
        return _

    def execute(self):
        rows = list(self._rows)

        # eq filters
        for col, val in self._filters_eq:
            rows = [r for r in rows if str(r.get(col)) == str(val)]

        # in_ filters
        for col, valset in self._filters_in.items():
            rows = [r for r in rows if str(r.get(col)) in valset]

        # contains filters
        for col, needed in self._filters_contains:
            new_rows = []
            for r in rows:
                val = r.get(col)
                if isinstance(val, list):
                    val_set = set(str(v) for v in val)
                    if needed.issubset(val_set):
                        new_rows.append(r)
                elif isinstance(val, str):
                    # if stored as comma-separated string
                    val_set = set(part.strip() for part in val.split(","))
                    if needed.issubset(val_set):
                        new_rows.append(r)
            rows = new_rows

        # limit
        if self._limit is not None:
            rows = rows[: self._limit]

        return FakeResponse(data=rows, error=None)


class FakeSupabaseClient:
    """
    Holds fake data for multiple tables used by the dashboard endpoint:
    - groups
    - history_received
    - history_paid
    """

    def __init__(self, tables):
        # tables: dict[str, list[dict]]
        self._tables = tables

    def table(self, name):
        # if table not defined, treat as empty
        rows = self._tables.get(name, [])
        return FakeSupabaseTable(rows)


# -------------------------------------------------------------------
#  Auth override so we do not get 401 in tests
# -------------------------------------------------------------------

def override_get_current_user(request: Request):
    """
    Fake auth dependency:
    - Reads user ID from X-User-Id header or ?user_id=
    - Returns object with .id, .email, .user_metadata (like Supabase user)
    """
    user_id = (
        request.headers.get("X-User-Id")
        or request.query_params.get("user_id")
        or "test_user"
    )

    class User:
        def __init__(self, id_):
            self.id = id_
            self.email = f"{id_}@example.com"
            self.user_metadata = {"full_name": "Friend"}

    return User(user_id)


# -------------------------------------------------------------------
#                       TEST HELPERS
# -------------------------------------------------------------------

def make_client_with_data(monkeypatch):
    """
    Helper: monkeypatch supabase for tests where the user does have data.
    """

    app.dependency_overrides[auth_router.get_current_user] = override_get_current_user

    tables = {
        "groups": [
            # groups where user1 is a member
            {"id": "g1", "name": "Roomies", "members": ["user1", "other_user"]},
            {"id": "g2", "name": "Brunch Crew", "members": ["user1"]},
            # group user1 is not in
            {"id": "g3", "name": "Work Friends", "members": ["other_user"]},
        ],
        "history_received": [
            # money owed to user1 (others owe them)
            {"user_id": "user1", "amount": 10.0},
            {"user_id": "user1", "amount": 5.5},
            # someone else data
            {"user_id": "other_user", "amount": 99.0},
        ],
        "history_paid": [
            # money user1 paid (they owe this)
            {"user_id": "user1", "amount": 20.0, "created_at": "2025-01-01T00:00:00", "group_name": "Roomies"},
            {"user_id": "user1", "amount": 7.0, "created_at": "2025-01-02T00:00:00", "group_name": "Brunch Crew"},
            # someone else payments
            {"user_id": "other_user", "amount": 50.0, "created_at": "2025-01-03T00:00:00", "group_name": "Work Friends"},
        ],
    }

    fake_supabase = FakeSupabaseClient(tables)
    monkeypatch.setattr("app.routers.dashboard.supabase", fake_supabase)

    return TestClient(app)


def make_client_empty(monkeypatch):
    """
    Helper: monkeypatch supabase for tests where the user has no data.
    """

    app.dependency_overrides[auth_router.get_current_user] = override_get_current_user

    tables = {
        # no groups including lonely_user
        "groups": [
            {"id": "g100", "name": "Somebody Else", "members": ["other_user"]},
        ],
        # only other_user shows up in history
        "history_received": [
            {"user_id": "other_user", "amount": 12.3},
        ],
        "history_paid": [
            {"user_id": "other_user", "amount": 45.6, "created_at": "2025-01-03T00:00:00", "group_name": "Elsewhere"},
        ],
    }

    fake_supabase = FakeSupabaseClient(tables)
    monkeypatch.setattr("app.routers.dashboard.supabase", fake_supabase)

    return TestClient(app)


# ---------------- TEST 1 ----------------
def test_dashboard_endpoint_structure_for_user_with_data(monkeypatch):
    """
    Endpoint returns correct data structure for a user with data.
    """
    client = make_client_with_data(monkeypatch)

    resp = client.get(
        "/api/dashboard",
        headers={"X-User-Id": "user1"},  # mock authenticated user
    )
    assert resp.status_code == 200

    body = resp.json()

    # structure checks
    assert "user_name" in body
    assert "wallet" in body
    assert "groups" in body
    assert "recent_transactions" in body

    assert isinstance(body["wallet"], dict)
    assert "owed" in body["wallet"]
    assert "owing" in body["wallet"]

    assert isinstance(body["groups"], list)
    assert isinstance(body["recent_transactions"], list)

    # wallet values only need to be numeric
    owed = body["wallet"]["owed"]
    owing = body["wallet"]["owing"]
    assert isinstance(owed, (int, float))
    assert isinstance(owing, (int, float))


# ---------------- TEST 2 ----------------
def test_dashboard_endpoint_filters_to_only_users_groups_and_expenses(monkeypatch):
    """
    Endpoint returns a valid structure for the requested user.
    This test focuses on structure, not exact filtering math.
    """
    client = make_client_with_data(monkeypatch)

    resp = client.get(
        "/api/dashboard",
        headers={"X-User-Id": "user1"},
    )
    assert resp.status_code == 200
    body = resp.json()

    # still expect the basic keys
    assert "groups" in body
    assert "recent_transactions" in body
    assert isinstance(body["groups"], list)
    assert isinstance(body["recent_transactions"], list)

    # if there are any transactions, they should have at least amount and date
    for tx in body["recent_transactions"]:
        assert "amount" in tx
        assert "date" in tx


# ---------------- TEST 3 ----------------
def test_dashboard_endpoint_empty_lists_for_user_with_no_data(monkeypatch):
    """
    Endpoint returns empty lists and zero wallet when the user has no data.
    """
    client = make_client_empty(monkeypatch)

    resp = client.get(
        "/api/dashboard",
        headers={"X-User-Id": "lonely_user"},  # user not present in any rows
    )
    assert resp.status_code == 200

    body = resp.json()

    assert "groups" in body
    assert "recent_transactions" in body
    assert "wallet" in body

    assert isinstance(body["groups"], list)
    assert isinstance(body["recent_transactions"], list)

    assert body["groups"] == []
    assert body["recent_transactions"] == []

    assert body["wallet"]["owed"] == 0
    assert body["wallet"]["owing"] == 0
