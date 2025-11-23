# FILE: app/main.py
# Main FastAPI entry point. Wires routes, templates, static, and health checks.

import os
from pathlib import Path

from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from .core.supabase_client import supabase

# ------------------------
# APP + PATHS
# ------------------------
app = FastAPI(title="Expense Splitter API")

BASE_DIR = Path(__file__).parent            # app/
STATIC_DIR = BASE_DIR / "static"            # app/static
TEMPLATES_DIR = BASE_DIR / "templates"      # app/templates

# Mount static assets (JS/CSS/images)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Template engine
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ------------------------
# ROUTERS
# ------------------------
from .routers import groups, expenses, balances, auth
from .routers import friends, history, settings, payments, dashboard
from .routers.auth import get_current_user
from app.routers import inbox

app.include_router(groups.router)
app.include_router(expenses.router)
app.include_router(balances.router)
app.include_router(auth.router, prefix= "/auth")
app.include_router(friends.router)
app.include_router(history.router)
app.include_router(settings.router)
app.include_router(inbox.router)
app.include_router(payments.router, prefix="/api/payments")
app.include_router(dashboard.router, prefix="/api/dashboard")

# ------------------------
# HEALTH + BASIC CHECKS
# ------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/supabase-health")
def supabase_health():
    return {"connected": True}

@app.get("/test-supabase")
def test_supabase_connection():
    try:
        data = supabase.table("expenses").select("*").limit(1).execute()
        return {"connected": True, "data_preview": data.data}
    except Exception as e:
        return {"connected": False, "error": str(e)}


# ------------------------
# FRONTEND HTML ROUTES
# ------------------------
@app.get("/", response_class=HTMLResponse)
@app.get("/welcome", response_class=HTMLResponse)
@app.get("/welcome.html", response_class=HTMLResponse)
async def get_welcome(request: Request):
    return templates.TemplateResponse(request, "welcome.html", {})

@app.get("/login", response_class=HTMLResponse)
@app.get("/login.html", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse(request, "login.html", {})

@app.get("/signup", response_class=HTMLResponse)
@app.get("/signup.html", response_class=HTMLResponse)
async def get_signup(request: Request):
    return templates.TemplateResponse(request, "signup.html", {})

@app.get("/account", response_class=HTMLResponse)
@app.get("/account.html", response_class=HTMLResponse)
async def get_account(request: Request):
    mock_user = {
        "id": "user-123",
        "email": "liz@example.com",
        "full_name": "Liz",
        "username": "liz_b",
        "phone": "314-555-1234",
        "display_currency": "USD",
    }
    return templates.TemplateResponse(request, "account.html", {"mock_mode": True, "mock_user": mock_user})

@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    mock_data = {
        "user_name": "Preet",
        "wallet_balance": 25.50,
        "balance_class": "positive",
        "recent_tx": [
            {"name": "Pizza Night", "amount": 18.25, "sign": "-", "date": "2025-10-29", "group": "Roommates"},
            {"name": "Uber to AWM", "amount": 9.60,  "sign": "-", "date": "2025-10-28", "group": "AWM"},
            {"name": "Reimbursement from Liz", "amount": 12.40, "sign": "+", "date": "2025-10-27", "group": "CS3300"},
        ],
        "notifications": [
            "Grace added an expense in Roommates",
            "Liz requested settlement ($12.40)",
            "Invite: Join Group 'CS3300 Team'",
        ],
    }
    return templates.TemplateResponse(request, "dashboard.html", mock_data)

@app.get("/add-expense", response_class=HTMLResponse)
async def get_add_expense(
    request: Request,
    user=Depends(get_current_user),  # current authenticated user
):
    """
    Render the Add Expense page with the current user's id
    injected into the template as `current_user_id`.
    """
    return templates.TemplateResponse(
        request,
        "add_expense.html",
        {"current_user_id": str(user["id"])},
    )

@app.get("/friends", response_class=HTMLResponse)
@app.get("/friends.html", response_class=HTMLResponse)
async def get_friends(request: Request):
    return templates.TemplateResponse(request, "friends.html", {})

@app.get("/history", response_class=HTMLResponse)
@app.get("/history.html", response_class=HTMLResponse)
async def get_history(request: Request):
    return templates.TemplateResponse(request, "history.html", {})

@app.get("/settings", response_class=HTMLResponse)
@app.get("/settings.html", response_class=HTMLResponse)
async def get_settings(request: Request):
    return templates.TemplateResponse(request, "settings.html", {})

@app.get("/payments", response_class=HTMLResponse)
@app.get("/payments.html", response_class=HTMLResponse)
async def get_payments(request: Request):
    return templates.TemplateResponse(request, "payments.html", {})
