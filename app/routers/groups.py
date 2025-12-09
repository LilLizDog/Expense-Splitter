# FILE: app/routers/groups.py
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from postgrest.exceptions import APIError

from ..core.supabase_client import supabase
from .auth import get_current_user

router = APIRouter(prefix="/api/groups", tags=["groups"])


class CreateGroup(BaseModel):
    """Payload for creating a group from the add group form."""
    name: str
    description: Optional[str] = None
    # Friend link row ids selected in the form (do not include current user here)
    member_ids: List[str] = []


class UpdateGroup(BaseModel):
    """Payload for updating group name and description."""
    name: Optional[str] = None
    description: Optional[str] = None


class AddMemberPayload(BaseModel):
    """Payload for adding a member from a friend link."""
    friend_link_id: int


@router.post("/", summary="Create a new group")
def create_group(payload: CreateGroup, user=Depends(get_current_user)):
    """Create a group and include the current user as a member and owner."""
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Group name cannot be empty")

    # Convert friend_links row ids into real friend UUIDs
    friend_uuids: List[str] = []
    for row_id in payload.member_ids:
        try:
            res = (
                supabase.table("friend_links")
                .select("friend_id")
                .eq("id", row_id)
                .single()
                .execute()
            )
        except APIError:
            raise HTTPException(
                status_code=400,
                detail=f"Friend id {row_id} not found",
            )

        data = res.data or {}
        friend_id = data.get("friend_id")
        if not friend_id:
            raise HTTPException(
                status_code=400,
                detail=f"Friend id {row_id} not found",
            )
        friend_uuids.append(str(friend_id))

    uid = str(user["id"])

    # Build final members list with current user and selected friends
    all_members = [uid, *friend_uuids]
    members_unique = list({m for m in all_members if m})

    insert_data = {
        "name": name,
        "description": payload.description,
        "members": members_unique,
        "owner_id": uid,
    }

    try:
        res = supabase.table("groups").insert(insert_data).execute()
    except APIError as e:
        raise HTTPException(status_code=500, detail=str(e))

    data = res.data
    if isinstance(data, list):
        if not data:
            raise HTTPException(
                status_code=500,
                detail="Group insert returned no data",
            )
        group_row = data[0]
    else:
        group_row = data

    return {"ok": True, "group": group_row}


@router.get("/", summary="List groups for current user")
def get_groups_for_current_user(user=Depends(get_current_user)):
    """Return all groups where the current user is a member."""
    uid = str(user["id"])
    try:
        res = (
            supabase.table("groups")
            .select("*")
            .contains("members", [uid])
            .order("created_at", desc=True)
            .execute()
        )
    except APIError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return res.data or []


@router.get("/user/{user_id}", summary="Get groups for a given user id")
def get_user_groups(user_id: str):
    """Return all groups where the given user id is a member."""
    try:
        res = (
            supabase.table("groups")
            .select("*")
            .contains("members", [str(user_id)])
            .order("created_at", desc=True)
            .execute()
        )
    except APIError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"ok": True, "groups": res.data or []}


@router.get("/{group_id}", summary="Get group details")
def get_group(group_id: str):
    """Return a single group record by id."""
    try:
        res = (
            supabase.table("groups")
            .select("*")
            .eq("id", group_id)
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="Group not found")

    if not res.data:
        raise HTTPException(status_code=404, detail="Group not found")

    return res.data


@router.get("/{group_id}/members", summary="Get members of a group")
def get_group_members(group_id: str):
    """Return user records for all members in a group."""
    try:
        group_res = (
            supabase.table("groups")
            .select("members")
            .eq("id", group_id)
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="Group not found")

    group_data = group_res.data or {}
    member_ids = group_data.get("members") or []
    if not member_ids:
        return {"ok": True, "members": []}

    try:
        res = (
            supabase.table("users")
            .select("id, name, username, email")  # full_name removed
            .in_("id", member_ids)
            .execute()
        )
    except APIError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"ok": True, "members": res.data or []}


@router.delete("/{group_id}", summary="Delete a group")
def delete_group(group_id: str, user=Depends(get_current_user)):
    """Delete a group if the current user is the owner."""
    uid = str(user["id"])
    try:
        res = (
            supabase.table("groups")
            .select("id, owner_id")
            .eq("id", group_id)
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="Group not found")

    group_row = res.data or {}
    if not group_row:
        raise HTTPException(status_code=404, detail="Group not found")

    if group_row.get("owner_id") != uid:
        raise HTTPException(
            status_code=403,
            detail="Only the owner can delete this group",
        )

    try:
        supabase.table("groups").delete().eq("id", group_id).execute()
    except APIError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"ok": True}


@router.patch("/{group_id}", summary="Update group name or description")
def update_group(group_id: str, payload: UpdateGroup, user=Depends(get_current_user)):
    """Update group name or description for groups owned by the current user."""
    uid = str(user["id"])
    try:
        res = (
            supabase.table("groups")
            .select("id, owner_id, name, description")
            .eq("id", group_id)
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="Group not found")

    group_row = res.data or {}
    if not group_row:
        raise HTTPException(status_code=404, detail="Group not found")

    if group_row.get("owner_id") != uid:
        raise HTTPException(
            status_code=403,
            detail="Only the owner can edit this group",
        )

    update_data = {}

    if payload.name is not None:
        new_name = payload.name.strip()
        if not new_name:
            raise HTTPException(status_code=400, detail="Group name cannot be empty")
        update_data["name"] = new_name

    if payload.description is not None:
        update_data["description"] = payload.description

    if not update_data:
        return {"ok": True, "group": group_row}

    try:
        update_res = (
            supabase.table("groups")
            .update(update_data)
            .eq("id", group_id)
            .execute()
        )
    except APIError as e:
        raise HTTPException(status_code=500, detail=str(e))

    data = update_res.data
    if isinstance(data, list) and data:
        updated = data[0]
    elif isinstance(data, dict) and data:
        updated = data
    else:
        updated = {**group_row, **update_data}

    return {"ok": True, "group": updated}


@router.post("/{group_id}/members", summary="Add member to group from friend link")
def add_group_member(
    group_id: str,
    payload: AddMemberPayload,
    user=Depends(get_current_user),
):
    """Add a member to a group based on a friend_links row for the current user."""
    uid = str(user["id"])

    # Load group and verify current user is a member
    try:
        group_res = (
            supabase.table("groups")
            .select("id, members, owner_id")
            .eq("id", group_id)
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="Group not found")

    group_row = group_res.data or {}
    if not group_row:
        raise HTTPException(status_code=404, detail="Group not found")

    members = group_row.get("members") or []
    if uid not in members:
        raise HTTPException(
            status_code=403,
            detail="You must be a member to modify this group",
        )

    # Look up friend link that belongs to current user
    try:
        friend_res = (
            supabase.table("friend_links")
            .select("friend_id")
            .eq("id", payload.friend_link_id)
            .eq("owner_id", uid)
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="Friend link not found")

    friend_row = friend_res.data or {}
    friend_id = friend_row.get("friend_id")
    if not friend_id:
        raise HTTPException(status_code=404, detail="Friend link not found")

    # Append friend id if not already present
    if friend_id in members:
        return {"ok": True, "group": group_row}

    new_members = list({*members, friend_id})

    try:
        update_res = (
            supabase.table("groups")
            .update({"members": new_members})
            .eq("id", group_id)
            .execute()
        )
    except APIError as e:
        raise HTTPException(status_code=500, detail=str(e))

    data = update_res.data
    if isinstance(data, list) and data:
        updated = data[0]
    elif isinstance(data, dict) and data:
        updated = data
    else:
        updated = {**group_row, "members": new_members}

    return {"ok": True, "group": updated}


@router.post("/{group_id}/leave", summary="Leave the group")
def leave_group(group_id: str, user=Depends(get_current_user)):
    """Remove the current user from the group's members list."""
    uid = str(user["id"])

    try:
        res = (
            supabase.table("groups")
            .select("id, members, owner_id")
            .eq("id", group_id)
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="Group not found")

    group = res.data or {}

    members = group.get("members") or []

    if uid not in members:
        return {"ok": True, "message": "Already not a member"}

    # Owners cannot leave their own group
    if group.get("owner_id") == uid:
        raise HTTPException(
            status_code=403,
            detail="Owner cannot leave their own group",
        )

    new_members = [m for m in members if m != uid]

    try:
        supabase.table("groups").update({"members": new_members}).eq("id", group_id).execute()
    except APIError:
        raise HTTPException(status_code=500, detail="Could not update group")

    return {"ok": True}
