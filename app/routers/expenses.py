# FILE: app/routers/expenses.py
# Routes for "expenses". For now, we use an in-memory mock store so tests
# can create and list recent expenses reliably. Supabase wiring can be added later.

from fastapi import APIRouter, HTTPException
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
    member_ids: List[int] = Field(..., min_length=1, description="At least one member")
    # equal / amount / percentage
    split_type: Optional[str] = Field(
        "equal", 
        description="Split type: equal, amount, percentage",
    )

    # Required ONLY when split_type == 'amount'
    custom_amounts: Optional[List[float]] = Field(
        None,
        description="Per-member amounts for 'amount' split type (same order as member_ids)",
    )
    
    # Required ONLY when split_type == 'percentage'
    custom_percentages: Optional[List[float]] = Field(
        None,
        description="Per-member percentages for 'percentage' split type (same order as member_ids, must sum to 100)",
    )
    
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

@router.post("/", summary="Create expense (mock insert with flexible splits)", status_code=201)
def create_expense(payload: ExpenseCreate):
    """
    Insert one expense into the in-memory store and create participant rows according
    to split_type: equal, amount, or percentage. Pydantic validation (gt=0, min_length=1)
    ensures 422s for basic bad input; we add 400s for invalid split details.
    """
    split_type = (payload.split_type or "equal").lower()
    if split_type not in {"equal", "amount", "percentage"}:
        raise HTTPException(
            status_code=400,
            detail="Invalid split_type. Must be 'equal', 'amount', or 'percentage'.",
        )

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
        "split_type": split_type,
    }

    parts = []
    n = len(payload.member_ids)
    total_amount = round(payload.amount, 2)

    if split_type == "equal":
        # Equal split (last share gets remainder to handle rounding)
        base = round(total_amount / n, 2)
        running = 0.0
        for i, mid in enumerate(payload.member_ids, start=1):
            if i < n:
                share = base
                running += share
            else:
                share = round(total_amount - running, 2)
            parts.append({"expense_id": eid, "member_id": mid, "share": share})

    elif split_type == "amount":
        if not payload.custom_amounts:
            raise HTTPException(
                status_code=400,
                detail="custom_amounts is required when split_type='amount'.",
            )
        if len(payload.custom_amounts) != n:
            raise HTTPException(
                status_code=400,
                detail="custom_amounts length must match member_ids length.",
            )

        # Validate sum of amounts
        custom_rounded = [round(a, 2) for a in payload.custom_amounts]
        sum_custom = round(sum(custom_rounded), 2)
        if abs(sum_custom - total_amount) > 0.01:
            raise HTTPException(
                status_code=400,
                detail="Custom amounts must sum to the total amount.",
            )

        for mid, share in zip(payload.member_ids, custom_rounded):
            parts.append({"expense_id": eid, "member_id": mid, "share": share})

    elif split_type == "percentage":
        if not payload.custom_percentages:
            raise HTTPException(
                status_code=400,
                detail="custom_percentages is required when split_type='percentage'.",
            )
        if len(payload.custom_percentages) != n:
            raise HTTPException(
                status_code=400,
                detail="custom_percentages length must match member_ids length.",
            )

        # Validate sum of percentages
        perc_rounded = [round(p, 4) for p in payload.custom_percentages]
        sum_perc = round(sum(perc_rounded), 4)
        if abs(sum_perc - 100.0) > 0.01:
            raise HTTPException(
                status_code=400,
                detail="Percentages must sum to 100.",
            )

        running = 0.0
        for i, (mid, pct) in enumerate(zip(payload.member_ids, perc_rounded), start=1):
            if i < n:
                share = round(total_amount * pct / 100.0, 2)
                running += share
            else:
                # Last one gets the remainder to ensure exact total
                share = round(total_amount - running, 2)
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
