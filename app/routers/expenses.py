# FILE: app/routers/expenses.py
# Routes for "expenses".
# For now this uses an in-memory store (no database yet).

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional
from ..core.supabase_client import supabase

# All routes in this file start with /expenses
router = APIRouter(prefix="/expenses", tags=["expenses"])

@router.get("/ping-db")
def expenses_ping_db():
    """Simple connectivity check to the Supabase client."""
    try:
        _ = supabase.postgrest
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ----------------------------------
# In-memory mock storage (module-level)
# ----------------------------------
# This lets list/gets work even before any POST happens.
_FAKE_DB = {"expenses": [], "participants": [], "next_id": 1}

# ----------------------------------
# Request model for creating expenses
# ----------------------------------
class ExpenseCreate(BaseModel):
    group_id: int = Field(..., description="Group that this expense belongs to")
    payer: str = Field(..., min_length=1, description="Name of the person who paid")
    amount: float = Field(..., gt=0, description="Amount paid (must be > 0)")
    description: Optional[str] = Field(None, description="Short note about the expense")
    expense_date: date = Field(default_factory=date.today, description="Date of the expense")
    member_ids: List[int] = Field(..., min_items=1, description="Member IDs sharing this expense")
    split_type: Optional[str] = Field("equal", description="Split type (equal/custom)")

# ----------------------------------
# List all expenses (mock)
# ----------------------------------
@router.get("/", summary="List expenses (mock)")
def list_expenses():
    """Returns all expenses currently in the in-memory store."""
    return {
        "ok": True,
        "resource": "expenses",
        "data": _FAKE_DB["expenses"],
    }

# ----------------------------------
# List recent expenses (mock)
# ----------------------------------
@router.get("/recent", summary="List recent expenses (mock)")
def list_recent(limit: int = 5):
    """Returns the most recent 'limit' expenses (newest first)."""
    rows = _FAKE_DB["expenses"][-limit:][::-1]
    return {"ok": True, "data": rows}

# ----------------------------------
# Get one expense by id (mock)
# ----------------------------------
@router.get("/{expense_id}", summary="Get one expense (test)")
def get_expense(expense_id: int):
    """Echoes the id to confirm routing works."""
    return {
        "ok": True,
        "resource": "expenses",
        "data": {"id": expense_id},
    }

# ----------------------------------
# Create an expense (mock)
# ----------------------------------
@router.post("/", summary="Create expense (accepts JSON)", status_code=201)
def create_expense(payload: ExpenseCreate):
    """
    Validates and stores an expense in the in-memory store.
    Splits amount equally across selected members (cent-accurate).
    """
    # Extra validation beyond Pydantic
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be > 0.")
    if not payload.member_ids:
        raise HTTPException(status_code=400, detail="Select at least one member.")

    # Create the expense
    expense_id = _FAKE_DB["next_id"]
    _FAKE_DB["next_id"] += 1

    exp_row = {
        "id": expense_id,
        "group_id": payload.group_id,
        "payer": payload.payer,
        "amount": payload.amount,
        "description": payload.description,
        "expense_date": str(payload.expense_date),
        "split_type": payload.split_type or "equal",
    }
    _FAKE_DB["expenses"].append(exp_row)

    # Equal split with cent-accurate adjustment for the last member
    n = len(payload.member_ids)
    base = round(payload.amount / n, 2)

    parts = []
    running = 0.0
    for i, mid in enumerate(payload.member_ids, start=1):
        if i < n:
            share = base
            running += share
        else:
            # Last member gets the remainder so totals match the amount exactly
            share = round(payload.amount - running, 2)
        item = {"expense_id": expense_id, "member_id": mid, "share": share}
        _FAKE_DB["participants"].append(item)
        parts.append(item)

    return {
        "ok": True,
        "resource": "expenses",
        "message": "created (mock)",
        "data": {"expense": exp_row, "participants": parts},
    }
