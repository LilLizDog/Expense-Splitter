import os
import sys
import warnings
import pytest
from fastapi.testclient import TestClient

# Ensure tests run in a testing environment
os.environ.setdefault("TESTING", "1")

# Ensure project root is importable
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Suppress noisy deprecation warnings
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=".*The 'timeout' parameter is deprecated.*",
)
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=".*The 'verify' parameter is deprecated.*",
)

from app.main import app
from app.routers.auth import get_current_user


def override_get_current_user():
    """
    Return a fake user that works with both dict and attribute access.
    """
    class TestUser(dict):
        def __init__(self, user_id: str, email: str):
            # Store values in dict so user["id"] works
            super().__init__(id=user_id, email=email)
            # Also expose attributes so user.id works
            self.id = user_id
            self.email = email

    return TestUser("test-user", "test@example.com")


@pytest.fixture
def client():
    """
    Basic client with a test user override applied.
    """
    app.dependency_overrides[get_current_user] = override_get_current_user
    return TestClient(app)


@pytest.fixture
def auth_client():
    """
    Authenticated client that signs up, verifies, and logs in a test user.
    """
    app.dependency_overrides[get_current_user] = override_get_current_user
    c = TestClient(app)

    email = "authtest@example.com"
    password = "Password123!"

    # Sign up and verify test user
    c.post("/auth/signup", data={"email": email, "password": password})
    c.get("/auth/verify", params={"email": email})
    resp = c.post("/auth/login", data={"email": email, "password": password})

    assert resp.status_code == 200
    return c
