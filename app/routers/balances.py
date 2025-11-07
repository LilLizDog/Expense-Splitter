# FILE: app/routers/balances.py
# Test routes for "balances" so we can wire things up. No DB yet.

from fastapi import APIRouter  # helps us group related routes
from ..core.supabase_client import supabase

router = APIRouter(prefix = "/balances", tags = ["balances"])

@router.get("/ping-db")
def balances_ping_db():
    try:
        supabase.functions
        return{"ok" : True}
    except Exception as e:
        return {"ok" : False, "error" : str(e)}
    

# all routes here start with /balances
router = APIRouter(
    prefix="/balances",
    tags=["balances"]  # shows as a section in /docs
)

# GET /balances  → list all balances (placeholder)
@router.get("/", summary="List balances (test)")
def list_balances():
    """
    Sends back a simple JSON so we can confirm routing works.
    TODO: LATER, CALCULATE REAL BALANCES FROM EXPENSES.
    """
    return {
        "ok": True,
        "resource": "balances",
        "data": []  # empty for now
    }

# GET /balances/{group_id} → balances for one group (placeholder)
@router.get("/{group_id}", summary="Get balances for a group (test)")
def get_group_balances(group_id: int):
    """
    Echoes the group_id so we can see the path param working.
    TODO: LATER, QUERY SUPABASE FOR THIS GROUP AND COMPUTE NETS.
    """
    return {
        "ok": True,
        "resource": "balances",
        "group_id": group_id,
        "data": []  # will be per-person balances later
    }
# 