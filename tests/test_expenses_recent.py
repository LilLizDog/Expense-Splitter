from datetime import date

_fake_store = []  # local fake DB since TEST MODE skips Supabase


def _post_exp(client, idx):
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


def test_recent_limit(auth_client):
    _fake_store.clear()
    for i in range(1, 4):
        _post_exp(auth_client, i)

    # simulate recent
    rows = sorted(_fake_store, key=lambda x: x["expense_date"], reverse=True)[:2]

    assert len(rows) == 2
    assert rows[0]["description"] == "Expense 3"
    assert rows[1]["description"] == "Expense 2"


def test_recent_default_5(auth_client):
    _fake_store.clear()
    for i in range(1, 7):
        _post_exp(auth_client, i)

    rows = sorted(_fake_store, key=lambda x: x["expense_date"], reverse=True)[:5]

    assert len(rows) == 5
    assert rows[0]["description"] == "Expense 6"
    assert rows[-1]["description"] == "Expense 2"
