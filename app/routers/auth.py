from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..core.supabase_client import supabase 

router = APIRouter(prefix = "/auth", tags=["auth"])

@router.get("/ping-db")
def auth_ping_db():
    try:
        supabase.auth.get_session()
        return{"ok" : True}
    except Exception as e:
        return {"ok" : False, "error" : str(e)}
    
# this sets up a router for authentificaation routes (signup and login)
router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

# data models for requests coming from the frontend
# each model shows what kind of info we are expecting
class SignUpRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str


# this is a signup route, but its just a placeholder for now
# later this will connec to supabase auth to actually create an account
@router.post("/signup", status_code=201)
def sign_up(request: SignUpRequest):
    #simple validation to check if email and password are provided
    if request.email == "" or request.password == "":
        raise HTTPException(status_code=400, detail="Email and password are required.")
    
    # TODO: Connect this with Supabase Auth (sign up user)
    # For now, just return a mock success message
    return {"message": f"{request.email} signed up successfully (placeholder)."}


# login route, which is also a placeholder for now
# later this will check the user's info in Supabase
@router.post("/login", status_code=200)
def login(request: LoginRequest):
    #simple validation to check if email and password are provided
    if request.email == "" or request.password == "":
        raise HTTPException(status_code=400, detail="Email and password are required.")
    
    # TODO: Connect this with Supabase Auth (login user)
    # For now, just return a mock token
    return {"message": f"{request.email} logged in successfully (placeholder)."}
