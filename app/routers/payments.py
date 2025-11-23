# app/routers/pages.py (or wherever you serve templates)
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.supabase_client import supabase

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()

@router.get("/payments", response_class=HTMLResponse)
def payments(request: Request):
    return templates.TemplateResponse(
    request,
    "payments.html",
    {}
)
