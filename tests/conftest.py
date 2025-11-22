# tests/conftest.py
import os
import sys
from dotenv import load_dotenv
import pytest
from fastapi.testclient import TestClient

# Load .env for local development
load_dotenv()

# Make project root importable
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ROOT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import FastAPI app
from app.main import app

@pytest.fixture
def client():
    """Reusable test client for FastAPI."""
    return TestClient(app)
