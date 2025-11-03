# FILE: tests/test_balances_basic.py
# Basic tests for /balances mock routes.

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_balances_list_ok():
    # GET /balances should return a simple ok payload
    r = client.get("/balances/")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["resource"] == "balances"
    assert isinstance(body["data"], list)

def test_group_balances_ok_and_zero_sum():
    # GET /balances/{group_id} should echo group_id and return balances
    gid = 123
    r = client.get(f"/balances/{gid}")
    assert r.status_code == 200
    body = r.json()

    assert body["ok"] is True
    assert body["resource"] == "balances"
    assert body["group_id"] == gid
    assert isinstance(body["data"], list)
    assert len(body["data"]) >= 1

    # balances should be ints and sum to zero (netting out within a group)
    total = 0
    for row in body["data"]:
        assert "member" in row
        assert "balance_cents" in row
        assert isinstance(row["balance_cents"], int)
        total += row["balance_cents"]
    assert total == 0

def test_balances_ping_db_route():
    # /balances/ping-db should respond with ok=True/False (no exception)
    r = client.get("/balances/ping-db")
    assert r.status_code == 200
    body = r.json()
    assert "ok" in body
