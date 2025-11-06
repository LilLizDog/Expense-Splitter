# This file handles friends-related API endpoints using Supabase
# It connects to our FastAPI app and uses the shared Supabase client

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..core.supabase_client import supabase # Import shared client with Supabase

# Sets up the router for friends-related routes with prefix /api/friends
router = APIRouter(prefix="/api/friends", tags=["Friends"])

# This model defines the expected input shape when adding a friend
class FriendIn(BaseModel):
    name: str
    group: str  # This maps to group_name in Supabase

# TODO: replace with real logged-in user
def get_current_user_id() -> str:
    return "demo-user-1"

# GET list of friends, with optional filters
@router.get("/")
def list_friends(
    q: Optional[str] = Query(None), # Optional search filter
    group: Optional[str] = Query(None), #Optional filter by group
):
    user_id = get_current_user_id()

    # Pull all this user's friends from Supabase that belong to the user
    resp = (
        supabase
        .table("friends")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )

    rows = resp.data or []  # Stores the response data in a safe way

    # Apply local filters for the search query and group filter
    if q:
        rows = [r for r in rows if q.lower() in (r.get("name") or "").lower()]
    if group:
        rows = [r for r in rows if group.lower() in (r.get("group_name") or "").lower()]

    # Returns the list of friends in the expected format
    return {
        "friends": [
            {
                "id": r["id"],
                "name": r["name"],
                "group": r.get("group_name") or "",
            }
            for r in rows
        ]
    }

# POST adds a new friend
@router.post("/")
def add_friend(friend: FriendIn):
    user_id = get_current_user_id()

    # Insert the new friend into Supabase
    resp = (
        supabase
        .table("friends")
        .insert(
            {
                "user_id": user_id,
                "name": friend.name,
                "group_name": friend.group,
            }
        )
        .execute()
    )

    # Make sure the insert succeeded and return the new row of friend data
    rows = resp.data
    if not rows:
        # we didn't get anything back, so tell the frontend
        raise HTTPException(status_code=500, detail="Insert failed (no data returned)")

    # Return the newly created friend back to the frontend
    row = rows[0]
    return {
        "message": "Friend added",
        "friend": {
            "id": row["id"],
            "name": row["name"],
            "group": row.get("group_name") or "",
        },
    }

# GET list of unique groups from this user's friends
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
