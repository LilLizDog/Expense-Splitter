from fastapi import FastAPI
from .core.supabase_client import supabase

app = FastAPI(title="Expense Splitter API")

@app.get("/")
def read_root():
    return {"message": "Hello, Debugging Divas!"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/supabase-health")
def supabase_health():
    return {"connected": True}
