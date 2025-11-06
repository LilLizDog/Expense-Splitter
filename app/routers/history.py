# This file handles history-related API endpoints using Supabase
# It pulls data from Supabase to show a user's recent activity history
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from ..core.supabase_client import supabase # Connect to our shared Supabase client

# Sets up the router for history-related routes with prefix /api/history
router = APIRouter(prefix="/api/history", tags=["History"])

# fTemporary function for a fake logged-in user
def get_current_user_id() -> str:
    return "demo-user-1"

# GET Retrieves the user's history of received payments and paid expenses
@router.get("/")
def get_history(
    group: Optional[str] = Query(None), # Optional group filter
    person: Optional[str] = Query(None), #Optional person filter
):
    user_id = get_current_user_id()

    # Get all the received payments for this user form the history_received table
    recv_resp = (
        supabase
        .table("history_received")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )
    if recv_resp.data is None:
        raise HTTPException(status_code=500, detail="Error fetching received history")
    received_rows = recv_resp.data  # this is a list

    # Get all the paid expenses for this user from the history_paid table
    paid_resp = (
        supabase
        .table("history_paid")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )
    if paid_resp.data is None:
        raise HTTPException(status_code=500, detail="Error fetching paid history")
    paid_rows = paid_resp.data

    # Apply optional filters so the frontent does not have to change
    # Group filter
    if group:
        g = group.lower()
        received_rows = [r for r in received_rows if g in (r.get("group_name") or "").lower()]
        paid_rows = [p for p in paid_rows if g in (p.get("group_name") or "").lower()]

    # Filter by person
    if person:
        p = person.lower()
        # For received, person  uses from_name
        received_rows = [r for r in received_rows if p in (r.get("from_name") or "").lower()]
        # For paid, person uses to_name
        paid_rows = [r for r in paid_rows if p in (r.get("to_name") or "").lower()]

    # Format and return the response in the expected shape
    return {
        "received": [
            {
                "id": r["id"],
                "from": r.get("from_name") or "",
                "amount": r.get("amount") or 0,
                "group": r.get("group_name") or "",
            }
            for r in received_rows
        ],
        "paid": [
            {
                "id": p["id"],
                "to": p.get("to_name") or "",
                "amount": p.get("amount") or 0,
                "group": p.get("group_name") or "",
            }
            for p in paid_rows
        ],
    }

# GET Retrieves all unique groups from both history tables for this user
@router.get("/groups")
def get_history_groups():
    user_id = get_current_user_id()

    # Grab all group names from both history tables
    recv_resp = (
        supabase
        .table("history_received")
        .select("group_name")
        .eq("user_id", user_id)
        .execute()
    )
    paid_resp = (
        supabase
        .table("history_paid")
        .select("group_name")
        .eq("user_id", user_id)
        .execute()
    )

    # Turn each result set into a set of group names to remove duplicates
    recv_groups = {r["group_name"] for r in (recv_resp.data or []) if r.get("group_name")}
    paid_groups = {p["group_name"] for p in (paid_resp.data or []) if p.get("group_name")}

    # Combine both sets and sort alphabetically
    all_groups = sorted(recv_groups | paid_groups)
    return {"groups": all_groups}
