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


@pytest.fixture
def client():
    # Basic unauthenticated client
    return TestClient(app)


@pytest.fixture
def auth_client():
    # Creates a fully signed up, verified, and logged in client
    c = TestClient(app)

    email = "authtest@example.com"
    password = "Password123!"

    c.post("/auth/signup", data={"email": email, "password": password})
    c.get("/auth/verify", params={"email": email})
    resp = c.post("/auth/login", data={"email": email, "password": password})

    assert resp.status_code == 200
    return c