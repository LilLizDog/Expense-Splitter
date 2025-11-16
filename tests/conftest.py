# tests/conftest.py

import os, sys
os.environ.setdefault("TESTING", "1")
import pytest
from fastapi.testclient import TestClient

# Ensure project root is importable
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.main import app


@pytest.fixture
def client():
    """Unauthenticated client."""
    return TestClient(app)


@pytest.fixture
def auth_client():
    """
    Creates a fully verified + logged-in test user.
    Returns a TestClient that already has auth cookies.
    """
    c = TestClient(app)

    email = "authtest@example.com"
    password = "Password123!"

    # 1) Signup
    c.post("/auth/signup", data={"email": email, "password": password})

    # 2) Verify
    c.get("/auth/verify", params={"email": email})

    # 3) Login (sets session cookies inside TestClient)
    resp = c.post("/auth/login", data={"email": email, "password": password})
    assert resp.status_code == 200

    return c
