from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional, Literal
from ..core.supabase_client import supabase
from .auth import get_current_user
import os

router = APIRouter(prefix="/expenses", tags=["expenses"])


# -----------------------------
# Health check endpoint
# -----------------------------
@router.get("/ping-db")
def expenses_ping_db():
    """Simple check that the Supabase client is reachable."""
    try:
        _ = supabase.postgrest
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# -----------------------------
# Pydantic models
# -----------------------------
class ExpenseCreate(BaseModel):
    # Group id is optional so we can handle friend only expenses
    group_id: Optional[str]

    # We still accept an expense type from the UI, but we do not store it yet
    expense_type: Literal[
        "food",
        "groceries",
        "rent",
        "utilities",
        "transportation",
        "entertainment",
        "shopping",
        "health",
        "travel",
        "household",
        "other",
    ]

    # Amount must be strictly positive
    amount: float = Field(..., gt=0)
    description: Optional[str]
    expense_date: date = Field(default_factory=date.today)

    # At least one member must be included
    member_ids: List[str] = Field(..., min_length=1)

    # Split configuration
    split_type: Optional[str] = "equal"
    custom_amounts: Optional[List[float]] = None
    custom_percentages: Optional[List[float]] = None


# -----------------------------
# DB helper functions
# -----------------------------
def _db_insert_expense(expense_row: dict) -> dict:
    """Insert a single expense row into the expenses table."""
    res = supabase.table("expenses").insert(expense_row).execute()
    err = getattr(res, "error", None)
    if err:
        raise HTTPException(status_code=500, detail=str(err))
    if not res.data:
        raise HTTPException(status_code=500, detail="Insert failed.")
    return res.data[0]


def _db_insert_participants(rows: List[dict]) -> List[dict]:
    """Insert participant rows into the expense_participants table."""
    res = supabase.table("expense_participants").insert(rows).execute()
    err = getattr(res, "error", None)
    if err:
        raise HTTPException(status_code=500, detail=str(err))
    return res.data or rows


# -----------------------------
# List endpoints
# -----------------------------
@router.get("/")
def list_expenses(limit: int = 50):
    """Return a list of recent expenses."""
    res = (
        supabase.table("expenses")
        .select("*")
        .order("expense_date", desc=True)
        .limit(limit)
        .execute()
    )

    err = getattr(res, "error", None)
    if err:
        raise HTTPException(status_code=500, detail=str(err))

    return {"ok": True, "data": res.data or []}


@router.get("/recent")
def list_recent(limit: int = 5):
    """Return a short list of the most recent expenses."""
    res = (
        supabase.table("expenses")
        .select("*")
        .order("expense_date", desc=True)
        .limit(limit)
        .execute()
    )

    err = getattr(res, "error", None)
    if err:
        raise HTTPException(status_code=500, detail=str(err))

    return {"ok": True, "data": res.data or []}


@router.get("/{expense_id}")
def get_expense(expense_id: str):
    """Return a single expense and its participants."""
    exp = (
        supabase.table("expenses")
        .select("*")
        .eq("id", expense_id)
        .single()
        .execute()
    )

    err = getattr(exp, "error", None)
    if err:
        raise HTTPException(status_code=404, detail="Not found")

    parts = (
        supabase.table("expense_participants")
        .select("*")
        .eq("expense_id", expense_id)
        .execute()
    )

    return {
        "ok": True,
        "data": {
            "expense": exp.data,
            "participants": parts.data or [],
        },
    }


# -----------------------------
# Create expense endpoint
# -----------------------------
@router.post("/", status_code=201)
def create_expense(
    payload: ExpenseCreate,
    user=Depends(get_current_user),
):
    """Create a new expense and its participant shares."""
    if user is None:
        # Fallback user for testing without auth
        user = {"id": "test-user"}

    # Block future dates
    if payload.expense_date > date.today():
        raise HTTPException(status_code=400, detail="Invalid date.")

    # Validate split type
    split_type = (payload.split_type or "equal").lower()
    if split_type not in {"equal", "amount", "percentage"}:
        raise HTTPException(status_code=400, detail="Invalid split type.")

    n = len(payload.member_ids)
    total = round(payload.amount, 2)
    splits: List[dict] = []

    # -----------------------------
    # Equal split
    # -----------------------------
    if split_type == "equal":
        base = round(total / n, 2)
        running = 0

        for i, mid in enumerate(payload.member_ids, start=1):
            if i < n:
                share = base
                running += share
            else:
                # Last share absorbs any rounding drift
                share = round(total - running, 2)
            splits.append({"member_id": mid, "share": share})

    # -----------------------------
    # Custom amount split
    # -----------------------------
    elif split_type == "amount":
        if not payload.custom_amounts or len(payload.custom_amounts) != n:
            raise HTTPException(status_code=400, detail="Invalid custom amounts.")

        rounded = [round(a, 2) for a in payload.custom_amounts]

        # For normal group expenses we still require that shares sum to the total
        # For non group friend expenses (group_id is None and a single member)
        # we allow the single share to be any positive amount up to the total
        if payload.group_id is not None or n > 1:
            if round(sum(rounded), 2) != total:
                raise HTTPException(
                    status_code=400,
                    detail="Amounts must sum to total.",
                )

        for mid, share in zip(payload.member_ids, rounded):
            splits.append({"member_id": mid, "share": share})

    # -----------------------------
    # Custom percentage split
    # -----------------------------
    else:
        if not payload.custom_percentages or len(payload.custom_percentages) != n:
            raise HTTPException(status_code=400, detail="Invalid percentages.")

        rounded = [round(p, 4) for p in payload.custom_percentages]
        if abs(sum(rounded) - 100) > 0.01:
            raise HTTPException(
                status_code=400, detail="Percentages must sum to 100."
            )

        running = 0
        for i, (mid, pct) in enumerate(zip(payload.member_ids, rounded), start=1):
            if i < n:
                share = round(total * pct / 100, 2)
                running += share
            else:
                # Last share absorbs rounding drift
                share = round(total - running, 2)

            splits.append({"member_id": mid, "share": share})

    # -----------------------------
    # Insert expense row
    # -----------------------------
    expense_row = {
        "user_id": user["id"],  # matches expenses.user_id
        "group_id": payload.group_id,
        "amount": total,
        "description": payload.description,
        "expense_date": str(payload.expense_date),
        "split_type": split_type,
        # We are not inserting expense_type until the column exists
    }

    # In test mode, skip actual DB access
    if os.getenv("TESTING") == "1":
        return {"id": "mock-id", "message": "ok", "data": expense_row}

    inserted = _db_insert_expense(expense_row)
    expense_id = inserted["id"]

    # -----------------------------
    # Insert participants
    # -----------------------------
    participant_rows = [
        {
            "expense_id": expense_id,
            "member_id": s["member_id"],
            "share": s["share"],
        }
        for s in splits
    ]

    participants = _db_insert_participants(participant_rows)

    # -----------------------------------
    # Insert into history tables
    # and create notifications
    # -----------------------------------
    if os.getenv("TESTING") != "1":  # Only write history in real mode
        try:
            # Lookup group name if applicable
            group_name = ""
            if payload.group_id:
                g_res = (
                    supabase
                    .table("groups")
                    .select("name")
                    .eq("id", payload.group_id)
                    .single()
                    .execute()
                )
                if g_res.data:
                    group_name = g_res.data.get("name") or ""

            # Lookup names for each participant
            id_to_name = {}

            if payload.member_ids:
                users_res = (
                    supabase
                    .table("users")
                    .select("id,name,email")
                    .in_("id", payload.member_ids)
                    .execute()
                )

                for u in users_res.data or []:
                    id_to_name[u["id"]] = (
                        u.get("name") or u.get("email") or "Unknown"
                    )

            # Name for the payer (current user)
            payer_name = user.get("name") or user.get("email") or "Unknown"

            # Notifications for participants
            for participant_id in payload.member_ids:
                # Do not notify the payer about their own expense
                if participant_id == user["id"]:
                    continue

                supabase.table("notifications").insert(
                    {
                        "type": "Expense",
                        "from_user": user["id"],
                        "to_user": participant_id,
                        "group_id": payload.group_id,
                        "status": "pending",
                    }
                ).execute()

            # Payer history
            supabase.table("history_paid").insert(
                {
                    "user_id": user["id"],
                    "to_name": ", ".join(
                        id_to_name.get(mid, mid) for mid in payload.member_ids
                    ),
                    "amount": total,
                    "group_name": group_name,
                }
            ).execute()

            # Participant history
            for s in splits:
                supabase.table("history_received").insert(
                    {
                        "user_id": s["member_id"],
                        "from_name": payer_name,
                        "amount": s["share"],
                        "group_name": group_name,
                    }
                ).execute()

        except Exception as e:
            print("History insert failed:", e)

    return {
        "ok": True,
        "message": "created",
        "data": {
            "expense": inserted,
            "participants": participants,
            "user_id": user["id"],
        },
    }
