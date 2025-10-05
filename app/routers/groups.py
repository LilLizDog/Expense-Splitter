# FILE: app/routers/groups.py
# This file sets up a test route for groups so we can check that routing works.

from fastapi import APIRouter  # helps us create separate sections of routes

# All routes in this file will start with /groups
router = APIRouter(
    prefix="/groups",
    tags=["groups"]  # this just adds a "groups" label on the docs page
)

# This creates a GET route (basically means we’re just reading or viewing data)
@router.get("/", summary="Get all groups (test route)")
def list_groups():
    """
    When someone visits /groups, this function runs.
    For now, it just sends back a simple JSON so we can test everything.
    """
    return {
        "ok": True,              # shows the request worked fine
        "resource": "groups",    # just says what kind of data this is
        "data": []               # empty list for now (we’ll fill this later)
    }
# Later, we can add more routes here to handle creating, updating, or deleting groups.