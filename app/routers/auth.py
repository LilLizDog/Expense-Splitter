from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

# Simple in-memory user store for testing
users_db = {}

@router.post("/signup")
def signup(email: str = Form(...), password: str = Form(...)):
    """
    Signup POST endpoint for tests.
    """
    if email in users_db:
        raise HTTPException(status_code=400, detail="Email already exists")
    users_db[email] = password
    return JSONResponse(content={"message": "User created"}, status_code=200)

@router.post("/login")
def login(email: str = Form(...), password: str = Form(...)):
    """
    Login POST endpoint for tests.
    """
    if email not in users_db or users_db[email] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return JSONResponse(content={"message": "Login successful"}, status_code=200)
