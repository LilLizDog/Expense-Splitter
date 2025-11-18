# FILE: app/routers/balances.py
# Mock routes for "balances" to confirm routing and structure before DB setup.

from fastapi import APIRouter  # groups related routes
from ..core.supabase_client import supabase  # will be used later for real data

router = APIRouter(prefix="/balances", tags=["balances"])

@router.get("/ping-db")
def balances_ping_db():
    """Checks if Supabase client is accessible."""
    try:
        _ = supabase.functions
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@router.get("/", summary="List all balances (mock)")
def list_balances():
    """Returns mock data to confirm the route works."""
    return {
        "ok": True,
        "resource": "balances",
        "data": []
    }

@router.get("/{group_id}", summary="Get balances for a group (mock)")
def get_group_balances(group_id: int):
    """Returns mock balances for a given group ID."""
    return {
        "ok": True,
        "resource": "balances",
        "group_id": group_id,
        "data": [
            {"member": "Preet", "balance_cents": 2500},
            {"member": "Chris", "balance_cents": -2500}
        ]
    }
# 