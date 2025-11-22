import random
import string
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
TEST_PASSWORD = "Password123!"


def random_email():
    return "".join(random.choices(string.ascii_lowercase, k=6)) + "@test.com"


def test_signup_valid():
    email = random_email()
    r = client.post("/auth/signup", data={"email": email, "password": TEST_PASSWORD})
    assert r.status_code == 200
    assert "User created" in r.json()["message"]


def test_signup_duplicate():
    email = random_email()

    client.post("/auth/signup", data={"email": email, "password": TEST_PASSWORD})
    r = client.post("/auth/signup", data={"email": email, "password": TEST_PASSWORD})

    assert r.status_code == 400
    assert "already" in r.text.lower()


def test_login_unverified_fails():
    email = random_email()

    client.post("/auth/signup", data={"email": email, "password": TEST_PASSWORD})
    r = client.post("/auth/login", data={"email": email, "password": TEST_PASSWORD})

    assert r.status_code == 400
    assert "verify" in r.text.lower() or "email" in r.text.lower()


def test_login_verified_success():
    email = random_email()

    client.post("/auth/signup", data={"email": email, "password": TEST_PASSWORD})
    # mark verified in test mode
    client.get("/auth/verify", params={"email": email})

    r = client.post("/auth/login", data={"email": email, "password": TEST_PASSWORD})

    assert r.status_code == 200
    assert r.json()["message"] == "Login successful"


def test_login_wrong_password():
    email = random_email()

    client.post("/auth/signup", data={"email": email, "password": TEST_PASSWORD})
    # mark verified so we actually hit wrong-password branch
    client.get("/auth/verify", params={"email": email})

    r = client.post("/auth/login", data={"email": email, "password": "WRONG"})

    assert r.status_code == 401
