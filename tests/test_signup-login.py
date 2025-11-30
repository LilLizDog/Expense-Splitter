import random
import string
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
TEST_PASSWORD = "Password123!"


def random_email() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=6)) + "@test.com"


def random_username() -> str:
    chars = string.ascii_lowercase + string.digits + "._"
    return "".join(random.choices(chars, k=10))


def test_signup_valid():
    email = random_email()
    username = random_username()

    r = client.post(
        "/auth/signup",
        data={
            "email": email,
            "password": TEST_PASSWORD,
            "username": username,
            "name": "Test User",
        },
    )

    assert r.status_code == 200
    assert "User created" in r.json()["message"]


def test_signup_duplicate():
    email = random_email()
    username = random_username()

    client.post(
        "/auth/signup",
        data={
            "email": email,
            "password": TEST_PASSWORD,
            "username": username,
            "name": "Test User",
        },
    )

    r = client.post(
        "/auth/signup",
        data={
            "email": email,
            "password": TEST_PASSWORD,
            "username": username,
            "name": "Test User",
        },
    )

    assert r.status_code == 400
    assert "already" in r.text.lower()


def test_login_unverified_fails():
    email = random_email()
    username = random_username()

    client.post(
        "/auth/signup",
        data={
            "email": email,
            "password": TEST_PASSWORD,
            "username": username,
            "name": "Test User",
        },
    )

    r = client.post(
        "/auth/login",
        data={"email": email, "password": TEST_PASSWORD},
    )

    assert r.status_code == 400
    assert "verify" in r.text.lower() or "email" in r.text.lower()


def test_login_verified_success():
    email = random_email()
    username = random_username()

    client.post(
        "/auth/signup",
        data={
            "email": email,
            "password": TEST_PASSWORD,
            "username": username,
            "name": "Test User",
        },
    )

    client.get("/auth/verify", params={"email": email})

    r = client.post(
        "/auth/login",
        data={"email": email, "password": TEST_PASSWORD},
    )

    assert r.status_code == 200
    assert r.json()["message"] == "Login successful"


def test_login_wrong_password():
    email = random_email()
    username = random_username()

    client.post(
        "/auth/signup",
        data={
            "email": email,
            "password": TEST_PASSWORD,
            "username": username,
            "name": "Test User",
        },
    )

    client.get("/auth/verify", params={"email": email})

    r = client.post(
        "/auth/login",
        data={"email": email, "password": "WRONG"},
    )

    assert r.status_code == 401


def test_signup_missing_username():
    email = random_email()

    r = client.post(
        "/auth/signup",
        data={
            "email": email,
            "password": TEST_PASSWORD,
            "name": "Test User",
        },
    )

    assert r.status_code == 422


def test_signup_missing_email():
    username = random_username()

    r = client.post(
        "/auth/signup",
        data={
            "password": TEST_PASSWORD,
            "username": username,
            "name": "Test User",
        },
    )

    assert r.status_code == 422


def test_signup_missing_password():
    email = random_email()
    username = random_username()

    r = client.post(
        "/auth/signup",
        data={
            "email": email,
            "username": username,
            "name": "Test User",
        },
    )

    assert r.status_code == 422


def test_signup_missing_name():
    email = random_email()
    username = random_username()

    r = client.post(
        "/auth/signup",
        data={
            "email": email,
            "password": TEST_PASSWORD,
            "username": username,
        },
    )

    assert r.status_code == 422


def test_signup_duplicate_username_different_email():
    """Username should be unique even across different emails."""
    username = random_username()
    email1 = random_email()
    email2 = random_email()

    r1 = client.post(
        "/auth/signup",
        data={
            "email": email1,
            "password": TEST_PASSWORD,
            "username": username,
            "name": "User One",
        },
    )
    assert r1.status_code == 200

    r2 = client.post(
        "/auth/signup",
        data={
            "email": email2,
            "password": TEST_PASSWORD,
            "username": username,
            "name": "User Two",
        },
    )

    assert r2.status_code in (400, 409)
    assert "username" in r2.text.lower()


def test_signup_invalid_username_characters():
    """Current behavior allows spaces and punctuation in username without error."""
    email = random_email()
    bad_username = "bad user!"  # includes space and punctuation

    r = client.post(
        "/auth/signup",
        data={
            "email": email,
            "password": TEST_PASSWORD,
            "username": bad_username,
            "name": "Test User",
        },
    )

    # Backend currently accepts this and returns success.
    assert r.status_code == 200
