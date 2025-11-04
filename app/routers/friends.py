# FILE: app/routers/friends.py
# This file manages all backend API routes related to the Friends page
# It allows users to view, search, filter, and add friends.
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, List

# Creates a router for the "Friends" feature. 
# All routes will be prefixed with /api/friends.
router = APIRouter(prefix="/api/friends", tags=["Friends"])

# ---- Mock data (replace with Supabase later) ----
friends_data = [
    {"id": 1, "name": "Olivia Hageman", "group": "Roommates"},
    {"id": 2, "name": "Preet Kaur", "group": "Debugging Divas"},
    {"id": 3, "name": "Elizabeth Dreste", "group": "Debugging Divas"},
    {"id": 4, "name": "Sophia Smith", "group": "Dance Crew"},
    {"id": 5, "name": "Liam Patel", "group": "CS Study Group"},
]

# This model defines the structure of a Friend when adding a new entry.
class FriendIn(BaseModel):
    name: str
    group: str

# GET /api/friends/
# Lists friends, with optional search (q) and group filtering.
@router.get("/")
def list_friends(q: Optional[str] = Query(None), group: Optional[str] = Query(None)):
    results = friends_data
    # If a search query (q) is provided, filter friends by name.
    if q:
        results = [f for f in results if q.lower() in f["name"].lower()]
    # If a group filter is provided, filter friends by group.
    if group:
        results = [f for f in results if group.lower() in f["group"].lower()]
    # This returns the filtered list of friends.
    return {"friends": results}

# POST /api/friends/
# Adds a new friend entry.
@router.post("/")
def add_friend(friend: FriendIn):
    # This automatically assigns a new ID that is one higher than the current max ID.
    new_id = max([f["id"] for f in friends_data] or [0]) + 1
    entry = {"id": new_id, "name": friend.name, "group": friend.group}
    # Appends the new friend to the mock data list.
    friends_data.append(entry)
    # Returns the newly added friend entry.
    return {"message": "Friend added", "friend": entry}

# GET /api/friends/groups
# Retrieves a list of unique groups from the friends data for filtering.
@router.get("/groups")
def list_groups():
    # Uses a set to get rid of duplicate group names, then sorts them.
    groups = sorted({f["group"] for f in friends_data})
    return {"groups": groups}
