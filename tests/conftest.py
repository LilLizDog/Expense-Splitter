# tests/conftest.py
# Sets up a shared test client for all API tests.

import os, sys
import pytest
from fastapi.testclient import TestClient

# Make sure the project root (where app/ lives) is importable
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ROOT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.main import app  # Import the FastAPI app from app/main.py

@pytest.fixture
def client():
    """Provides a reusable test client for the FastAPI app."""
    return TestClient(app)
