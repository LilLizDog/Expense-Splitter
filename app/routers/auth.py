from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

# Simple in-memory user store for testing
users_db = {}  # { email: {"password": "...", "verified": False} }

@router.post("/signup")
def signup(email: str = Form(...), password: str = Form(...)):
    """
    Signup POST endpoint for tests.
    """
    if email in users_db:
        raise HTTPException(status_code=400, detail="Email already exists")
   
    # User starts as unverified
    users_db[email] = {
        "password": password,
        "verified": False,
        }
    # In real app Supabase sends the email link
    return JSONResponse(content={"message": "User created. Verification email sent."}, status_code=200)

@router.post("/login")
def login(email: str = Form(...), password: str = Form(...)):
    """
    Login POST endpoint for tests.
    """
    if email not in users_db:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = users_db[email]

    if user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user["verified"]:
        raise HTTPException(status_code=403, detail="Please verify your email before logging in.")

    return JSONResponse(content={"message": "Login successful"}, status_code=200)

@router.get("/verify")
def verify(email: str):
    """
    Simple test endpoint to mark a user as verified.
    In real life, Supabase handles this with a token.
    """
    if email not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    users_db[email]["verified"] = True
    return {"message": "Email verified successfully"}
