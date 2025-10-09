# FILE: app/main.py
# This is the main entry point for our FastAPI app.
# It connects everything — routes, Supabase setup, and basic health checks.

from fastapi import FastAPI, Request          # main FastAPI class + request object
from fastapi.responses import HTMLResponse  # used to return HTML pages
from fastapi.templating import Jinja2Templates  # for rendering HTML templates
# from fastapi.staticfiles import StaticFiles  # to serve static files like CSS/JS  (might not need this)
from .core.supabase_client import supabase  # connects our app to Supabase (database)
from .routers import groups, expenses,balances, auth       # brings in the /groups, /expenses and /balances route files we made

# create the main app object
app = FastAPI(title="Expense Splitter API")  # title just shows up on the docs page

#setup teplate rendering for HTML pages (app/templates folder)
templates = Jinja2Templates(directory="app/templates")

# static folder if we add CSS or JS file later(keep in mind to uncomment the import as well)
# app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ------------------------
# BASIC TEST ROUTES
# ------------------------

# simple root route to test if app is running
@app.get("/")
def read_root():
    # returns a basic test message
    return {"message": "Hello, Debugging Divas!"}

# another quick route to check app health
@app.get("/health")
def health():
    # if this shows "ok", the app is working fine
    return {"status": "ok"}

# route to test if Supabase connection works (just a placeholder for now)
@app.get("/supabase-health")
def supabase_health():
    # later, we’ll actually check connection status here
    return {"connected": True}

# ------------------------
# CONNECT OTHER ROUTES
# ------------------------

# add the /groups routes from the groups.py file
app.include_router(groups.router)     # links all /groups endpoints into our main app

# add the /expenses routes from the expenses.py file
app.include_router(expenses.router)   # links all /expenses endpoints into our main app

# add the /balances routes from the balances.py file
app.include_router(balances.router)   # links all /balances endpoints into our main app

# add the /auth routes from the auth.py file
app.include_router(auth.router)       # links all /auth endpoints into our main app

# ------------------------
# FRONTEND HTML ROUTES
# ------------------------

# main login page
@app.get("/", response_class=HTMLResponse)
async def get_login(request: Request):
    # displays login page
    return templates.TemplateResponse("login.html", {"request": request})

# alternate login routes
@app.get("/login", response_class=HTMLResponse)
async def get_login_alias(request: Request):
    # serves same login page at /login
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/login.html", response_class=HTMLResponse)
async def get_login_html(request: Request):
    # handles direct reference to login.html
    return templates.TemplateResponse("login.html", {"request": request})

# signup page
@app.get("/signup", response_class=HTMLResponse)
async def get_signup(request: Request):
    # displays signup page
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/signup.html", response_class=HTMLResponse)
async def get_signup_html(request: Request):
    # handles direct reference to signup.html
    return templates.TemplateResponse("signup.html", {"request": request})
