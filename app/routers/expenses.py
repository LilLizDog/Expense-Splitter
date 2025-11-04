# FILE: app/routers/expenses.py
# Routes for "expenses". DB insert for expense; splits later.

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional
from ..core.supabase_client import supabase

router = APIRouter(prefix="/expenses", tags=["expenses"])

@router.get("/ping-db")
def expenses_ping_db():
    """Quick Supabase connectivity check."""
    try:
        _ = supabase.postgrest
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ───────────────────────────────── Mock store (kept for list/gets)
_FAKE_DB = {"expenses": [], "participants": [], "next_id": 1}

# ───────────────────────────────── Request model
class ExpenseCreate(BaseModel):
    # Supabase uses UUIDs → accept as strings
    group_id: str = Field(..., description="Group UUID")
    payer: Optional[str] = Field(None, description="Payer name (ignored; use user_id later)")
    amount: float = Field(..., gt=0, description="Amount > 0")
    description: Optional[str] = Field(None, description="Note")
    expense_date: date = Field(default_factory=date.today, description="Expense date")
    # Kept for future splits; not used in Step 1
    member_ids: List[str] = Field(default_factory=list, description="Member UUIDs")
    split_type: Optional[str] = Field("equal", description="Split type")

# ───────────────────────────────── List (mock)
@router.get("/", summary="List expenses (mock)")
def list_expenses():
    """Returns mock expenses for now."""
    return {"ok": True, "resource": "expenses", "data": _FAKE_DB["expenses"]}

# ───────────────────────────────── Recent (mock)
@router.get("/recent", summary="List recent expenses (mock)")
def list_recent(limit: int = 5):
    """Returns most recent mock expenses."""
    rows = _FAKE_DB["expenses"][-limit:][::-1]
    return {"ok": True, "data": rows}

# ───────────────────────────────── Get one (mock)
@router.get("/{expense_id}", summary="Get one expense (test)")
def get_expense(expense_id: int):
    """Echoes the id to confirm routing."""
    return {"ok": True, "resource": "expenses", "data": {"id": expense_id}}

# ───────────────────────────────── Create (DB insert only)
@router.post("/", summary="Create expense (DB only)", status_code=201)
def create_expense(payload: ExpenseCreate):
    """
    Inserts a single expense row into Supabase.
    Splits/participants will be added in the next step.
    """
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be > 0.")
    if not payload.group_id:
        raise HTTPException(status_code=400, detail="Group is required.")

    try:
        # user_id left None until auth is wired
        res = (
            supabase.table("expenses")
            .insert({
                "group_id": payload.group_id,
                "user_id": None,
                "amount": str(round(payload.amount, 2)),  # money as string
                "description": payload.description,
                "expense_date": str(payload.expense_date),
                "split_type": payload.split_type or "equal",
            })
            .select("*")
            .single()
            .execute()
        )
        return {
            "ok": True,
            "resource": "expenses",
            "message": "created",
            "data": {"expense": res.data, "participants": []},
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
