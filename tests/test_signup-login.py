import random
import string
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
TEST_PASSWORD = "Password123!"

def random_email():
    return ''.join(random.choices(string.ascii_lowercase, k=5)) + "@test.com"

def test_01_valid_signup():
    email = random_email()
    response = client.post("/signup", data={"email": email, "password": TEST_PASSWORD})
    assert response.status_code == 200

def test_02_duplicate_email_signup():
    email = random_email()
    # First signup
    client.post("/signup", data={"email": email, "password": TEST_PASSWORD})
    # Duplicate signup
    response = client.post("/signup", data={"email": email, "password": TEST_PASSWORD})
    assert response.status_code == 400

def test_03_login_success():
    email = random_email()
    # Signup first
    client.post("/signup", data={"email": email, "password": TEST_PASSWORD})
    # Login
    response = client.post("/login", data={"email": email, "password": TEST_PASSWORD})
    assert response.status_code == 200

def test_04_login_failure():
    response = client.post("/login", data={"email": "nonexistent@example.com", "password": "wrongpassword"})
    assert response.status_code == 401
