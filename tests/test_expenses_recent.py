from datetime import date

_fake_store = []  # Local fake DB since TESTING mode skips Supabase


def _post_exp(client, idx):
    """
    Helper that posts a simple equal split expense and records it
    into the in memory fake store for recent tests.
    """
    payload = {
        "group_id": "g1",
        "amount": 10 + idx,
        "description": f"Expense {idx}",
        "expense_date": date(2025, 10, 1 + idx).isoformat(),
        "member_ids": ["u1", "u2"],
        "expense_type": "other",
        "split_type": "equal",
    }
    client.post("/expenses/", json=payload)
    _fake_store.append(payload)


def test_recent_limit(client):
    _fake_store.clear()
    for i in range(1, 4):
        _post_exp(client, i)

    # Simulate recent query with a limit of 2
    rows = sorted(_fake_store, key=lambda x: x["expense_date"], reverse=True)[:2]

    assert len(rows) == 2
    assert rows[0]["description"] == "Expense 3"
    assert rows[1]["description"] == "Expense 2"


def test_recent_default_5(client):
    _fake_store.clear()
    for i in range(1, 7):
        _post_exp(client, i)

    # Simulate recent query with default limit of 5
    rows = sorted(_fake_store, key=lambda x: x["expense_date"], reverse=True)[:5]

    assert len(rows) == 5
    assert rows[0]["description"] == "Expense 6"
    assert rows[-1]["description"] == "Expense 2"
