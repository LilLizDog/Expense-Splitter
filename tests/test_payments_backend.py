# tests/test_payments_backend.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

# --- Helpers to build fake supabase responses ---

class FakeResponse:
    def __init__(self, data=None, error=None):
        self.data = data
        self.error = error


class FakeSupabaseTable:
    """
    This is the core mock object for supabase.table("payments").
    Each test injects its own data into this object.
    """

    def __init__(self, rows):
        # rows = list of dicts (representing DB)
        self._rows = rows
        self._query = {}
        self._update_payload = None
        self._single_mode = False

    # ---- filtering ----
    def select(self, *_args, **_kwargs):
        return self

    def eq(self, col, val):
        self._query.setdefault("eq", []).append((col, val))
        return self

    def or_(self, expr):
        # expr like:  "from_user_id.eq.user1,to_user_id.eq.user1"
        parts = []
        for piece in expr.split(","):
            col, _, val = piece.partition(".eq.")
            parts.append((col, val))
        self._query["or"] = parts
        return self

    def order(self, *_args, **_kwargs):
        return self

    # ---- update ----
    def update(self, payload):
        self._update_payload = payload
        return self

    def single(self):
        self._single_mode = True
        return self

    # ---- final execute ----
    def execute(self):
        rows = self._rows

        # apply .eq filters
        if "eq" in self._query:
            for col, val in self._query["eq"]:
                rows = [r for r in rows if str(r.get(col)) == str(val)]

        # apply .or filters
        if "or" in self._query:
            allowed = []
            for col, val in self._query["or"]:
                allowed += [r for r in rows if str(r.get(col)) == str(val)]
            rows = allowed

        # apply update
        if self._update_payload is not None:
            if not rows:
                return FakeResponse(data=None)
            for r in rows:
                r.update(self._update_payload)

        if self._single_mode:
            return FakeResponse(data=rows[0] if rows else None)

        return FakeResponse(data=rows)


class FakeSupabaseClient:
    """
    Mock supabase client root.
    Allows table("payments") only — that's all your router uses.
    """

    def __init__(self, rows):
        self._rows = rows

    def table(self, name):
        assert name == "payments"
        return FakeSupabaseTable(self._rows)


# ----------------------------------------------------------------------
#                              TESTS
# ----------------------------------------------------------------------


# ---------- TEST 1 ----------
def test_outstanding_payments_summary(monkeypatch):
    """
    Outstanding payments endpoint returns correct totals.
    (amount user owes + amount owed to user)
    """

    # mock rows like your supabase table
    rows = [
        # user owes 30 + 10 = 40
        {"id": 1, "from_user_id": "friendA", "to_user_id": "user1",
         "amount": 30.0, "status": "requested"},
        {"id": 2, "from_user_id": "friendB", "to_user_id": "user1",
         "amount": 10.0, "status": "requested"},

        # user is owed 50
        {"id": 3, "from_user_id": "user1", "to_user_id": "friendA",
         "amount": 50.0, "status": "requested"},

        # paid payments shouldn't count
        {"id": 4, "from_user_id": "friendA", "to_user_id": "user1",
         "amount": 99.0, "status": "paid"},
    ]

    fake_supabase = FakeSupabaseClient(rows)
    monkeypatch.setattr("app.routers.payments.supabase", fake_supabase)

    client = TestClient(app)

    res = client.get("/api/payments/summary?user_id=user1")
    assert res.status_code == 200

    body = res.json()
    assert body["amount_owed_by_user"] == 40.0
    assert body["amount_owed_to_user"] == 50.0


# ---------- TEST 2 ----------
def test_mark_payment_as_paid(monkeypatch):
    """
    Marking a payment as paid moves it out of `requested`
    and into the paid category.
    """

    rows = [
        {
            "id": 10,
            "from_user_id": "friendA",
            "to_user_id": "user1",
            "amount": 20.0,
            "status": "requested",
            "created_at": "2025-01-01",
            "paid_at": None,
            "paid_via": None,
            "group_id": None,
            "expense_id": None,
        }
    ]

    fake_supabase = FakeSupabaseClient(rows)
    monkeypatch.setattr("app.routers.payments.supabase", fake_supabase)

    client = TestClient(app)

    res = client.post("/api/payments/10/pay?user_id=user1", json={"paid_via": "Venmo"})
    assert res.status_code == 200

    body = res.json()
    assert body["success"] is True
    assert body["payment"]["status"] == "paid"
    assert body["payment"]["paid_via"] == "Venmo"
    assert body["payment"]["paid_at"] is not None


# ---------- TEST 3 ----------
def test_user_cannot_update_payments_they_do_not_own(monkeypatch):
    """
    Only the user who OWES the payment should be able to mark it as paid.
    We simulate this by checking:
        requester ≠ to_user_id → should fail
    """

    rows = [
        {
            "id": 20,
            "from_user_id": "friendA",
            "to_user_id": "user66",
            "amount": 99.0,
            "status": "requested",
            "created_at": "2025-01-01",
            "paid_at": None,
            "paid_via": None,
            "group_id": None,
            "expense_id": None,
        }
    ]

    fake_supabase = FakeSupabaseClient(rows)
    monkeypatch.setattr("app.routers.payments.supabase", fake_supabase)

    client = TestClient(app)

    # user1 tries to pay a payment owed by user66
    res = client.post("/api/payments/20/pay?user_id=user1", json={})

    # YOUR router doesn't enforce this yet, so we expect 200.
    # Let's change that: enforce permission and expect 403.
    assert res.status_code == 403
