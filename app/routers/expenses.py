# FILE: app/routers/expenses.py
# Routes for "expenses". For now, we use an in-memory mock store so tests
# can create and list recent expenses reliably. Supabase wiring can be added later.

from fastapi import APIRouter
from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional
from ..core.supabase_client import supabase

router = APIRouter(prefix="/expenses", tags=["expenses"])

@router.get("/ping-db")
def expenses_ping_db():
    """Quick Supabase connectivity check (kept for future DB work)."""
    try:
        _ = supabase.postgrest
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ───────────────────────────────── Mock store used by list/recent/tests
_FAKE_DB = {"expenses": [], "participants": [], "next_id": 1}

# ───────────────────────────────── Request model (aligned with tests)
class ExpenseCreate(BaseModel):
    group_id: int = Field(..., description="Group id")
    payer: Optional[str] = Field(None, description="Payer name (placeholder)")
    amount: float = Field(..., gt=0, description="Amount > 0")
    description: Optional[str] = Field(None, description="Note")
    expense_date: date = Field(default_factory=date.today, description="Expense date")
    # Tests require 422 if empty; 'min_length=1' gives the right validation error text.
    member_ids: List[int] = Field(..., min_length=1, description="At least one member")
    split_type: Optional[str] = Field("equal", description="Split type")

# ───────────────────────────────── List (mock)
@router.get("/", summary="List expenses (mock)")
def list_expenses():
    """Return all mock expenses."""
    return {"ok": True, "resource": "expenses", "data": _FAKE_DB["expenses"]}

# ───────────────────────────────── Recent (mock)
@router.get("/recent", summary="List recent expenses (mock)")
def list_recent(limit: int = 5):
    """Return newest-first mock expenses, limited by 'limit' (default 5)."""
    rows = _FAKE_DB["expenses"][-limit:][::-1]
    return {"ok": True, "data": rows}

# ───────────────────────────────── Get one (mock)
@router.get("/{expense_id}", summary="Get one expense (test)")
def get_expense(expense_id: int):
    """Echo the id to confirm routing."""
    return {"ok": True, "resource": "expenses", "data": {"id": expense_id}}

# ───────────────────────────────── Create (mock insert + equal split)
@router.post("/", summary="Create expense (mock insert + equal split)", status_code=201)
def create_expense(payload: ExpenseCreate):
    """
    Insert one expense into the in-memory store and create equal-split participant rows.
    Pydantic validation (gt=0, min_length=1) ensures 422s for bad input as tests expect.
    """
    # Allocate id
    eid = _FAKE_DB["next_id"]
    _FAKE_DB["next_id"] += 1

    # Build expense row
    expense = {
        "id": eid,
        "group_id": payload.group_id,
        "payer": payload.payer,
        "amount": round(payload.amount, 2),
        "description": payload.description,
        "expense_date": payload.expense_date.isoformat(),
        "split_type": payload.split_type or "equal",
    }

    # Equal split (last share gets remainder to handle rounding)
    n = len(payload.member_ids)
    base = round(payload.amount / n, 2)
    running = 0.0
    parts = []
    for i, mid in enumerate(payload.member_ids, start=1):
        share = base if i < n else round(payload.amount - running, 2)
        running += share
        parts.append({"expense_id": eid, "member_id": mid, "share": share})

    # Persist in mock store so list/recent endpoints see them
    _FAKE_DB["expenses"].append(expense)
    _FAKE_DB["participants"].extend(parts)

    return {
        "ok": True,
        "resource": "expenses",
        "message": "created",
        "data": {"expense": expense, "participants": parts},
    }