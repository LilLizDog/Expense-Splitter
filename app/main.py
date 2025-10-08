# FILE: app/main.py
# This is the main entry point for our FastAPI app.
# It connects everything — routes, Supabase setup, and basic health checks.

from fastapi import FastAPI                 # main FastAPI class to make our app
from .core.supabase_client import supabase  # connects our app to Supabase (database)
from .routers import groups, expenses,balances, auth       # brings in the /groups, /expenses and /balances route files we made

# create the main app object
app = FastAPI(title="Expense Splitter API")  # title just shows up on the docs page

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