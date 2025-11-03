# FILE: app/routers/groups.py
# This file sets up a test route for groups so we can check that routing works.

from fastapi import APIRouter  # helps us create separate sections of routes
from ..core.supabase_client import supabase  # lets us talk to Supabase



# All routes in this file will start with /groups
router = APIRouter(prefix="/groups", tags=["groups"])  # this just adds a "groups" label on the docs page

@router.get("/ping-db")
def groups_ping_db():
    try:
        _ = supabase.postgrest
        return {"ok" : True}
    except Exception as e:
        return {"ok" : False, "error" : str(e)}

# This creates a GET route (basically means we’re just reading or viewing data)
@router.get("/", summary="Get all groups (test route)")
def list_groups():
    """
    When someone visits /groups, this function runs.
    For now, it just sends back a simple JSON so we can test everything.
    """
    return {
        "ok": True,              # request worked
        "resource": "groups",
        "data": [
            {"id": 1, "name": "Roommates"},
            {"id": 2, "name": "Trip to Chicago"},
        ]
    }

@router.get("/{group_id}/members", summary="Get members of a group (mock)")
def get_group_members(group_id: int):
    """
    Returns mock members for a group.
    Read-only to support Add Expense form.
    """
    members_by_group = {
        1: [
            {"id": 10, "name": "Preet"},
            {"id": 11, "name": "Grace"},
            {"id": 12, "name": "Liz"},
        ],
        2: [
            {"id": 20, "name": "Preet"},
            {"id": 21, "name": "Olivia"},
        ],
    }
    return {
        "ok": True,
        "resource": "group_members",
        "data": members_by_group.get(group_id, [])
    }
