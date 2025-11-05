# FILE: app/main.py
# Main FastAPI entry point. Wires routes, templates, and health checks.

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
# from fastapi.staticfiles import StaticFiles
from .core.supabase_client import supabase

# import router modules; use module.router below
from .routers import groups, expenses, balances, auth

app = FastAPI(title="Expense Splitter API")

from app.routers import inbox
app.include_router(inbox.router)


# template engine (expects HTML files under app/templates)
templates = Jinja2Templates(directory="app/templates")

# ------------------------
# HEALTH + BASIC CHECKS
# ------------------------

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/supabase-health")
def supabase_health():
    # placeholder; replace with a real ping later
    return {"connected": True}

@app.get("/test-supabase")
def test_supabase_connection():
    try:
        data = supabase.table("expenses").select("*").limit(1).execute()
        return {"connected": True, "data_preview": data.data}
    except Exception as e:
        return {"connected": False, "error": str(e)}

# ------------------------
# API ROUTERS
# ------------------------

app.include_router(groups.router)
app.include_router(expenses.router)
app.include_router(balances.router)
app.include_router(auth.router)

# ------------------------
# FRONTEND HTML ROUTES
# ----------------------

# Welcome page
@app.get("/", response_class=HTMLResponse)
async def get_welcome(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request})

@app.get("/welcome", response_class=HTMLResponse)
async def get_welcome(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request})

@app.get("/welcome.html", response_class=HTMLResponse)
async def get_welcome_html(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request})

# login page
@app.get("/login", response_class=HTMLResponse)
async def get_login_alias(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/login.html", response_class=HTMLResponse)
async def get_login_html(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# signup page
@app.get("/signup", response_class=HTMLResponse)
async def get_signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/signup.html", response_class=HTMLResponse)
async def get_signup_html(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

# static files (enable if needed)

app.mount("/static", StaticFiles(directory="app/templates/js"), name="static")

# app.mount("/static", StaticFiles(directory="app/static"), name="static")
