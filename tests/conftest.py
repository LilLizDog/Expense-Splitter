# tests/conftest.py
# Sets up a shared test client for all API tests.


import os
import sys
import pytest
from fastapi.testclient import TestClient

# --- Set environment variables early ---
os.environ["SUPABASE_URL"] = "http://fake-url"
os.environ["SUPABASE_KEY"] = "fake-key"
os.environ["TESTING"] = "1"

# Make sure the project root (where app/ lives) is importable
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ROOT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --- Import the FastAPI app AFTER env vars are set ---
from app.main import app

@pytest.fixture
def client():
    """Provides a reusable test client for the FastAPI app."""
    return TestClient(app)
