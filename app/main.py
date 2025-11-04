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
# dashboard page
@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """
    Dashboard view (static data for now).
    - Renders dashboard.html with mock values that match the template.
    - Replace these with real Supabase data later.
    """
    mock_data = {
        "user_name": "Preet",
        "wallet_balance": 25.50,          # set negative to see red styling
        "balance_class": "positive",      # or "negative"
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
    return templates.TemplateResponse("dashboard.html", {"request": request, **mock_data})

@app.get("/add-expense", response_class=HTMLResponse)
async def get_add_expense(request: Request):
    return templates.TemplateResponse("add_expense.html", {"request": request})

# static files (enable if needed) , app.mount("/static", StaticFiles(directory="app/static"), name="static")