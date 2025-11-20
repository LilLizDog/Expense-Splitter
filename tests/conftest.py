# tests/conftest.py

import os, sys
<<<<<<< HEAD
os.environ.setdefault("TESTING", "1")
=======
import warnings
>>>>>>> 9080e0c (Fix deprecation warnings: update TemplateResponse usage and suppress supabase warnings in tests)
import pytest
from fastapi.testclient import TestClient

# Ensure project root is importable
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.main import app
# tests/conftest.py

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

# Suppress noisy deprecation warnings from third-party libraries (supabase/httpx)
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

from app.main import app  # Import the FastAPI app from app/main.py


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
