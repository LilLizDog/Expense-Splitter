import os
import re
import base64
import json

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import JSONResponse
import requests

router = APIRouter()

TEST_MODE = os.getenv("TESTING", "0") == "1"
# In dev leave COOKIE_SECURE unset or set it to "0" so cookies work on http.
# In prod set COOKIE_SECURE="1" so cookies are Secure.
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "0") == "1"

# =========================================================
# ===============  TEST MODE AUTH (FAKE)  =================
# =========================================================
if TEST_MODE:
    # Stores fake auth users keyed by email
    fake_users = {}
    # Stores fake profile info keyed by lowercase username
    fake_profiles = {}

    @router.post("/signup")
    def signup(
        email: str = Form(...),
        password: str = Form(...),
        name: str = Form(...),
        username: str = Form(...),
    ):
        """
        Fake signup for tests.
        Enforces unique email and unique username.
        """
        ukey = username.lower()

        if ukey in fake_profiles:
            raise HTTPException(400, "Username already taken")

        if email in fake_users:
            raise HTTPException(400, "Email already exists")

        fake_users[email] = {
            "password": password,
            "verified": False,
        }

        fake_profiles[ukey] = {
            "email": email,
            "name": name,
            "username": username,
        }

        return {"message": "User created. Please verify your email."}

    @router.get("/check-username")
    def check_username(username: str):
        """
        Check username availability in test mode.
        """
        ukey = username.lower()
        available = ukey not in fake_profiles
        return {"available": available}

    @router.get("/verify")
    def verify(email: str):
        """
        Mark a fake user as verified.
        """
        if email in fake_users:
            fake_users[email]["verified"] = True
            return {"message": "Email verified."}
        raise HTTPException(404, "User not found")

    @router.post("/login")
    def login(email: str = Form(...), password: str = Form(...)):
        """
        Fake login for tests.
        """
        if email not in fake_users:
            raise HTTPException(401, "Invalid email or password")

        user = fake_users[email]

        if not user["verified"]:
            raise HTTPException(400, "Please verify your email first.")

        if user["password"] != password:
            raise HTTPException(401, "Invalid email or password")

        res = JSONResponse({"message": "Login successful"}, status_code=200)
        # Test mode uses a simple non secure cookie
        res.set_cookie("sb-access-token", "fake-token")
        return res

    def get_current_user(request: Request):
        """
        Test mode current user lookup based on cookie.
        """
        token = request.cookies.get("sb-access-token")
        if token != "fake-token":
            raise HTTPException(401, "Not authenticated")

        return {"id": "fakeuser", "email": "test@example.com"}


# =========================================================
# ===============  REAL SUPABASE MODE  ====================
# =========================================================
else:
    from app.core.supabase_client import SUPABASE_URL, SUPABASE_KEY, supabase

    AUTH_URL = f"{SUPABASE_URL}/auth/v1"

    def username_exists_ci(username: str) -> bool:
        """
        Return True if the username already exists, case insensitive.
        """
        resp = (
            supabase.table("users")
            .select("id")
            .ilike("username", username)
            .limit(1)
            .execute()
        )
        data = getattr(resp, "data", None) or []
        return len(data) > 0

    def generate_username_from_email(email: str) -> str:
        """
        Build a safe unique username from the email local part.
        """
        local = (email or "").split("@")[0]
        base = re.sub(r"[^A-Za-z0-9._]", "", local).lower()
        if not base:
            base = "user"

        candidate = base
        suffix = 1
        while username_exists_ci(candidate):
            suffix += 1
            candidate = f"{base}{suffix}"
        return candidate

    def ensure_profile_exists_for_auth_user(user_id: str, email: str):
        """
        Create a row in public.users if one does not exist yet.
        """
        if not user_id or not email:
            return

        resp = (
            supabase.table("users")
            .select("id")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        data = getattr(resp, "data", None) or []
        if data:
            return

        name = email.split("@")[0]
        username = generate_username_from_email(email)

        supabase.table("users").insert(
            {
                "id": user_id,
                "name": name,
                "email": email,
                "username": username,
            }
        ).execute()

    def decode_jwt_no_verify(token: str) -> dict:
        """
        Decode a JWT payload without verifying signature.
        Only used to read Supabase auth claims from our cookie.
        """
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return {}
            payload_b64 = parts[1]
            padding = "=" * (-len(payload_b64) % 4)
            payload_bytes = base64.urlsafe_b64decode(payload_b64 + padding)
            return json.loads(payload_bytes.decode("utf-8"))
        except Exception:
            return {}

    @router.get("/check-username")
    def check_username(username: str):
        """
        Check whether a username is available.
        """
        return {"available": not username_exists_ci(username)}

    @router.post("/signup")
    def signup(
        email: str = Form(...),
        password: str = Form(...),
        name: str = Form(...),
        username: str = Form(...),
    ):
        """
        Supabase signup.
        Creates the auth user and a profile row in public.users.
        """
        if username_exists_ci(username):
            raise HTTPException(400, "Username already taken")

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

        body = response.json()
        user = body.get("user") or {}
        auth_user_id = user.get("id")

        if not auth_user_id:
            raise HTTPException(
                status_code=500,
                detail="Signup succeeded but user id was missing.",
            )

        try:
            supabase.table("users").insert(
                {
                    "id": auth_user_id,
                    "name": name,
                    "email": email,
                    "username": username,
                }
            ).execute()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create user profile: {e}",
            )

        return JSONResponse(
            {
                "message": "User created. Please check your email to verify your account."
            },
            status_code=200,
        )

    @router.post("/login")
    def login(email: str = Form(...), password: str = Form(...)):
        """
        Supabase login.

        1. Call Supabase token endpoint to verify credentials.
        2. Decode JWT to get user id and email.
        3. Ensure a profile row exists in public.users.
        4. Set HttpOnly cookies (sb-access-token, sb-refresh-token).
        """
        response = requests.post(
            f"{AUTH_URL}/token?grant_type=password",
            headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},
            json={"email": email, "password": password},
        )

        if response.status_code != 200:
            try:
                detail = response.json().get("error_description") or response.text
            except Exception:
                detail = "Invalid email or password."
            raise HTTPException(401, detail)

        data = response.json()
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")

        if not access_token:
            raise HTTPException(401, "Login failed.")

        claims = decode_jwt_no_verify(access_token)
        user_id = claims.get("sub") or claims.get("user_id")
        email_val = claims.get("email") or email

        if not user_id:
            raise HTTPException(500, "Could not determine user id from token.")

        try:
            ensure_profile_exists_for_auth_user(user_id, email_val)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Could not create user profile: {e}",
            )

        res = JSONResponse({"message": "Login successful"}, status_code=200)

        res.set_cookie(
            "sb-access-token",
            access_token,
            httponly=True,
            secure=COOKIE_SECURE,
            samesite="lax",
            path="/",
        )
        res.set_cookie(
            "sb-refresh-token",
            refresh_token,
            httponly=True,
            secure=COOKIE_SECURE,
            samesite="lax",
            path="/",
        )

        return res

    @router.get("/verify")
    def verify():
        """
        Supabase sends the email.
        Frontend only needs a friendly message.
        """
        return {
            "message": "Check your email and click the verification link to activate your account."
        }

    def get_current_user(request: Request):
        """
        Get current user from sb-access-token cookie.

        - Decode JWT (no network call to Supabase).
        - Use user id to look up row in public.users.
        """
        token = request.cookies.get("sb-access-token")

        # Allow Authorization header as a fallback (JS clients).
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "").strip()

        if not token:
            raise HTTPException(401, "Not authenticated")

        claims = decode_jwt_no_verify(token)
        user_id = claims.get("sub") or claims.get("user_id")
        email_val = claims.get("email") or ""

        if not user_id:
            raise HTTPException(401, "Invalid or expired token")

        try:
            resp = (
                supabase.table("users")
                .select("id, email")
                .eq("id", user_id)
                .limit(1)
                .execute()
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Could not look up user profile: {e}",
            )

        rows = getattr(resp, "data", None) or []
        if not rows:
            # If somehow missing, create a basic profile on the fly.
            if email_val:
                supabase.table("users").insert(
                    {
                        "id": user_id,
                        "email": email_val,
                        "name": email_val.split("@")[0],
                        "username": generate_username_from_email(email_val),
                    }
                ).execute()
                return {"id": user_id, "email": email_val}

            raise HTTPException(401, "Not authenticated")

        row = rows[0]
        return {"id": row["id"], "email": row.get("email", "")}
