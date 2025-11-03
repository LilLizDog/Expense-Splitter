# tests/test_expenses_recent.py
# Purpose: Verify that /expenses/recent returns newest-first and honors the limit.

from datetime import date

def _post_expense(client, *, idx: int) -> None:
    """Helper: create a distinct expense quickly."""
    payload = {
        "group_id": 1,
        "payer": "Preet",
        "amount": 10.00 + idx,                  # unique amount per expense
        "description": f"Expense {idx}",
        "expense_date": date(2025, 10, 20 + idx).isoformat(),
        "member_ids": [101, 102],
        "split_type": "equal",
    }
    client.post("/expenses/", json=payload)


def test_recent_returns_newest_first_and_limited(client):
    """Should return newest-first and respect ?limit=2."""
    # Arrange: create three expenses in order 1, 2, 3
    for i in range(1, 4):
        _post_expense(client, idx=i)

    # Act: ask for the 2 most recent
    r = client.get("/expenses/recent?limit=2")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    rows = data["data"]

    # Assert: exactly 2 results, in newest-first order (3 then 2)
    assert len(rows) == 2
    assert rows[0]["description"] == "Expense 3"
    assert rows[1]["description"] == "Expense 2"


def test_recent_defaults_to_5(client):
    """Default limit is 5 when no query param is given."""
    # Arrange: create six expenses so default returns 5
    for i in range(1, 7):
        _post_expense(client, idx=i)

    # Act
    r = client.get("/expenses/recent")
    assert r.status_code == 200
    data = r.json()
    rows = data["data"]

    # Assert: default is 5, newest-first, starts at the latest (6)
    assert len(rows) == 5
    assert rows[0]["description"] == "Expense 6"
    assert rows[-1]["description"] == "Expense 2"
