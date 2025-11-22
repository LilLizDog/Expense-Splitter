import os
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import JSONResponse
import requests

router = APIRouter()
TEST_MODE = os.getenv("TESTING", "0") == "1"

# =========================================================
# ===============  TEST MODE AUTH (FAKE)  =================
# =========================================================
if TEST_MODE:
    fake_users = {}

    @router.post("/signup")
    def signup(email: str = Form(...), password: str = Form(...)):
        if email in fake_users:
            raise HTTPException(400, "Email already exists")

        fake_users[email] = {
            "password": password,
            "verified": False,
        }
        return {"message": "User created. Please verify your email."}

    @router.get("/verify")
    def verify(email: str):
        if email in fake_users:
            fake_users[email]["verified"] = True
            return {"message": "Email verified."}
        raise HTTPException(404, "User not found")

    @router.post("/login")
    def login(email: str = Form(...), password: str = Form(...)):
        if email not in fake_users:
            raise HTTPException(401, "Invalid email or password")

        user = fake_users[email]

        # Match story: block unverified
        if not user["verified"]:
            raise HTTPException(400, "Please verify your email first.")

        if user["password"] != password:
            raise HTTPException(401, "Invalid email or password")

        res = JSONResponse({"message": "Login successful"}, status_code=200)
        res.set_cookie("sb-access-token", "fake-token")
        return res

    def get_current_user(request: Request):
        token = request.cookies.get("sb-access-token")
        if token != "fake-token":
            raise HTTPException(401, "Not authenticated")

        # fake id/email for tests
        return {"id": "fakeuser", "email": "test@example.com"}


# =========================================================
# ===============  REAL SUPABASE MODE  ====================
# =========================================================
else:
    from app.core.supabase_client import SUPABASE_URL, SUPABASE_KEY

    AUTH_URL = f"{SUPABASE_URL}/auth/v1"

    @router.post("/signup")
    def signup(email: str = Form(...), password: str = Form(...)):
        """
        Real Supabase signup.
        """
        response = requests.post(
            f"{AUTH_URL}/signup",
            headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},
            json={"email": email, "password": password},
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Signup failed. " + response.text,
            )

        return JSONResponse(
            {"message": "User created. Please check your email to verify your account."},
            status_code=200,
        )

    @router.post("/login")
    def login(email: str = Form(...), password: str = Form(...)):
        """
        Real Supabase login.
        """
        response = requests.post(
            f"{AUTH_URL}/token?grant_type=password",
            headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},
            json={"email": email, "password": password},
        )

        if response.status_code != 200:
            raise HTTPException(401, "Invalid email or password.")

        data = response.json()
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")

        if not access_token:
            raise HTTPException(401, "Login failed.")

        # Extra safety: fetch user and enforce email verification
        user_resp = requests.get(
            f"{AUTH_URL}/user",
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {access_token}"},
        )

        if user_resp.status_code != 200:
            raise HTTPException(401, "Login failed.")

        user = user_resp.json().get("user") or {}
        email_confirmed = user.get("email_confirmed_at") or user.get("confirmed_at")

        if not email_confirmed:
            # Do NOT give them access if not verified
            raise HTTPException(400, "Please verify your email first.")

        res = JSONResponse({"message": "Login successful"}, status_code=200)
        res.set_cookie(
            "sb-access-token",
            access_token,
            httponly=True,
            secure=True,
            samesite="lax",
        )
        res.set_cookie(
            "sb-refresh-token",
            refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
        )

        return res

    @router.get("/verify")
    def verify():
        """
        Supabase sends the actual email; frontend just needs a friendly message.
        """
        return {"message": "Check your email and click the verification link to activate your account."}

    def get_current_user(request: Request):
        """
        Real user fetch from Supabase, enforcing email verification.
        """
        token = request.cookies.get("sb-access-token")

        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "").strip()

        if not token:
            raise HTTPException(401, "Not authenticated")

        response = requests.get(
            f"{AUTH_URL}/user",
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {token}"},
        )

        if response.status_code != 200:
            raise HTTPException(401, "Invalid or expired token")

        user = response.json().get("user")
        if not user:
            raise HTTPException(401, "Not authenticated")

        email_confirmed = user.get("email_confirmed_at") or user.get("confirmed_at")
        if not email_confirmed:
            # Block dashboard / protected pages for unverified users
            raise HTTPException(400, "Please verify your email first.")

        return {"id": user["id"], "email": user["email"]}
