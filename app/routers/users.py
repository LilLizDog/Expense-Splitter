# FILE: app/routers/users.py
# Minimal user lookup endpoints for the frontend.

from fastapi import APIRouter, HTTPException, Query

from ..core.supabase_client import supabase

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/by-username")
def get_user_by_username(
    username: str = Query(..., min_length=1),
):
    """Look up a single user profile by username (case insensitive)."""
    uname = username.strip()
    if not uname:
        raise HTTPException(status_code=400, detail="Username is required")

    resp = (
        supabase.table("users")
        .select("id, name, email, username")
        .ilike("username", uname)
        .execute()
    )
    rows = resp.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="No user found with that username")

    # usernames are unique, so the first row is the correct one.
    return rows[0]
