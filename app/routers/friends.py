# This file handles friends-related API endpoints using Supabase.
# It connects to our FastAPI app and uses the shared Supabase client.

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..core.supabase_client import supabase  # Import shared client with Supabase

# Sets up the router for friends-related routes with prefix /api/friends
router = APIRouter(prefix="/api/friends", tags=["Friends"])

# This model defines the expected input shape when adding a friend.
# Name is optional, but email + group are required on the frontend.
class FriendIn(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    group: str  # This maps to group_name in Supabase

# TODO: replace with real logged-in user once auth is wired in
def get_current_user_id() -> str:
    # For now I'm just using a hard-coded user id so I can test the page.
    return "demo-user-1"

# GET /api/friends/ → list of friends, with optional search + group filters
@router.get("/")
def list_friends(
    q: Optional[str] = Query(None),      # Optional search filter (name or email)
    group: Optional[str] = Query(None),  # Optional filter by group
):
    user_id = get_current_user_id()

    # Pull all this user's friends from Supabase.
    # (Filtering by user_id happens in Supabase.)
    resp = (
        supabase
        .table("friends")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )

    rows = resp.data or []

    # Apply local filters for the search query and group filter.
    # q should match either name OR email.
    if q:
        q_lower = q.lower()
        rows = [
            r for r in rows
            if q_lower in (r.get("name") or "").lower()
            or q_lower in (r.get("email") or "").lower()
        ]

    if group:
        rows = [
            r for r in rows
            if group.lower() in (r.get("group_name") or "").lower()
        ]

    # Return the list of friends in the format the frontend expects.
    return {
        "friends": [
            {
                "id": r["id"],
                "name": r.get("name") or "",
                "email": r.get("email") or "",
                "group": r.get("group_name") or "",
            }
            for r in rows
        ]
    }

# POST /api/friends/ → add a new friend for the current user
@router.post("/")
def add_friend(friend: FriendIn):
    user_id = get_current_user_id()

    if not friend.name and not friend.email:
        raise HTTPException(
            status_code=400,
            detail="Name or email must be provided"
        )

    # Insert the new friend into Supabase. This assumes the "friends" table
    # has columns: user_id, name, email, group_name.
    resp = (
        supabase
        .table("friends")
        .insert(
            {
                "user_id": user_id,
                "name": friend.name,
                "email": friend.email,
                "group_name": friend.group,
            }
        )
        .execute()
    )

    
    rows = resp.data or []

    if not rows:
        # We didn't get anything back, so tell the frontend.
        raise HTTPException(status_code=500, detail="Insert failed (no data returned)")

    # Return the newly created friend back to the frontend
    row = rows[0]
    return {
        "message": "Friend added",
        "friend": {
            "id": row["id"],
            "name": row.get("name") or "",
            "email": row.get("email") or "",
            "group": row.get("group_name") or "",
        },
    }

# GET /api/friends/groups → list of unique groups from this user's friends
@router.get("/groups")
def list_groups():
    user_id = get_current_user_id()

    # Select only the group_name column for this user
    resp = (
        supabase
        .table("friends")
        .select("group_name")
        .eq("user_id", user_id)
        .execute()
    )


    rows = resp.data or []

    # Use a set to get unique group names, then sort them alphabetically
    groups = sorted({row["group_name"] for row in rows if row.get("group_name")})
    return {"groups": groups}
