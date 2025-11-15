import random
import string
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.routers.auth import users_db

client = TestClient(app)
TEST_PASSWORD = "Password123!"


def random_email():
    return "".join(random.choices(string.ascii_lowercase, k=5)) + "@test.com"


def test_01_valid_signup():
    users_db.clear()
    email = random_email()

    response = client.post("/signup", data={"email": email, "password": TEST_PASSWORD})

    assert response.status_code == 200
    assert email in users_db
    assert users_db[email]["verified"] is False  # new users are unverified


def test_02_duplicate_email_signup():
    users_db.clear()
    email = random_email()

    # First signup
    client.post("/signup", data={"email": email, "password": TEST_PASSWORD})
    # Duplicate signup
    response = client.post("/signup", data={"email": email, "password": TEST_PASSWORD})

    assert response.status_code == 400


def test_03_unverified_user_cannot_login():
    users_db.clear()
    email = random_email()

    # Signup (user is created as unverified)
    client.post("/signup", data={"email": email, "password": TEST_PASSWORD})

    # Try to login BEFORE verification
    response = client.post("/login", data={"email": email, "password": TEST_PASSWORD})

    assert response.status_code == 403
    assert response.json()["detail"] == "Please verify your email before logging in."


def test_04_login_failure_invalid_credentials():
    users_db.clear()

    response = client.post(
        "/login",
        data={"email": "nonexistent@example.com", "password": "wrongpassword"},
    )

    assert response.status_code == 401


def test_05_verified_user_can_login():
    users_db.clear()
    email = random_email()

    # Signup
    client.post("/signup", data={"email": email, "password": TEST_PASSWORD})

    # Simulate clicking verification link
    verify_resp = client.get("/verify", params={"email": email})
    assert verify_resp.status_code == 200
    assert users_db[email]["verified"] is True

    # Now login should succeed
    login_resp = client.post(
        "/login", data={"email": email, "password": TEST_PASSWORD}
    )

    assert login_resp.status_code == 200
    assert login_resp.json()["message"] == "Login successful"