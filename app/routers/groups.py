from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from ..core.supabase_client import supabase

router = APIRouter(prefix="/groups", tags=["groups"])

# ---------------------------
# Validation Models
# ---------------------------
class CreateGroup(BaseModel):
    name: str
    description: Optional[str] = None
    members: List[str]  # user UUIDs

# ---------------------------
# Create Group
# ---------------------------
@router.post("/", summary="Create a new group")
def create_group(payload: CreateGroup):
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Group name cannot be empty")

    insert_data = {
        "name": payload.name,
        "description": payload.description,
        "members": payload.members,
    }

    res = supabase.table("groups").insert(insert_data).execute()

    if res.error:
        raise HTTPException(status_code=500, detail=str(res.error))

    return {"ok": True, "group": res.data[0]}

# ---------------------------
# Get all groups for current user
# ---------------------------
@router.get("/user/{user_id}", summary="Get groups for a user")
def get_user_groups(user_id: str):

    res = (
        supabase.table("groups")
        .select("*")
        .contains("members", [user_id])  # user must be a member
        .order("created_at", desc=True)
        .execute()
    )

    if res.error:
        raise HTTPException(status_code=500, detail=str(res.error))

    return {"ok": True, "groups": res.data}

# ---------------------------
# Get group by ID
# ---------------------------
@router.get("/{group_id}", summary="Get group details")
def get_group(group_id: str):
    res = (
        supabase.table("groups")
        .select("*")
        .eq("id", group_id)
        .single()
        .execute()
    )

    if res.error:
        raise HTTPException(status_code=404, detail="Group not found")

    return res.data

# ---------------------------
# Get group members
# ---------------------------
@router.get("/{group_id}/members", summary="Get members of a group")
def get_group_members(group_id: str):

    # 1. get group record so we can read its members[] array
    group = (
        supabase.table("groups")
        .select("members")
        .eq("id", group_id)
        .single()
        .execute()
    )

    if group.error or not group.data:
        raise HTTPException(status_code=404, detail="Group not found")

    member_ids = group.data["members"]

    if not member_ids:
        return {"ok": True, "members": []}

    # 2. fetch user records
    res = (
        supabase.table("users")
        .select("id, name, email")
        .in_("id", member_ids)
        .execute()
    )

    if res.error:
        raise HTTPException(status_code=500, detail=str(res.error))

    return {"ok": True, "members": res.data}
