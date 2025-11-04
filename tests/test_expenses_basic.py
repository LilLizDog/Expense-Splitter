# tests/test_expenses_basic.py
# Basic test cases for the /expenses routes.

def test_create_expense_happy_path(client):
    """Valid expense should create successfully and split equally among members."""
    payload = {
        "group_id": 1,
        "payer": "Preet",
        "amount": 30.00,
        "description": "Groceries",
        "expense_date": "2025-10-22",
        "member_ids": [10, 11, 12],
        "split_type": "equal"
    }

    response = client.post("/expenses/", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["ok"] is True
    assert data["data"]["expense"]["amount"] == 30.00

    shares = sorted(p["share"] for p in data["data"]["participants"])
    assert shares == [10.0, 10.0, 10.0]


def test_create_expense_invalid_amount(client):
    """Expense with amount <= 0 should be rejected with 422."""
    payload = {
        "group_id": 1,
        "payer": "Preet",
        "amount": 0,
        "description": "Invalid test",
        "expense_date": "2025-10-22",
        "member_ids": [10, 11],
        "split_type": "equal"
    }

    response = client.post("/expenses/", json=payload)
    assert response.status_code == 422

    detail = response.json().get("detail", [])
    assert any(
        "amount" in "/".join(err.get("loc", [])) and "greater than 0" in err.get("msg", "").lower()
        for err in detail
    )


def test_create_expense_missing_members(client):
    """Expense with an empty member list should be rejected with 422."""
    payload = {
        "group_id": 1,
        "payer": "Preet",
        "amount": 50.00,
        "description": "No members",
        "expense_date": "2025-10-22",
        "member_ids": [],
        "split_type": "equal"
    }

    response = client.post("/expenses/", json=payload)
    assert response.status_code == 422

    detail = response.json().get("detail", [])
    assert any(
        "member_ids" in "/".join(err.get("loc", [])) and "at least" in err.get("msg", "").lower()
        for err in detail
    )
