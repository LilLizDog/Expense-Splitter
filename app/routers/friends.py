# FILE: app/routers/friends.py
# Friends API endpoints backing the Friends pages.
# Uses Supabase and the friend_links table.

from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from app.routers.auth import get_current_user
from ..core.supabase_client import supabase

router = APIRouter(prefix="/api/friends", tags=["Friends"])


class FriendCreate(BaseModel):
  """Input model for creating a friend link."""
  username: str
  note: Optional[str] = None


class FriendRecord(BaseModel):
  """Output model for a single friend on the Friends page."""
  id: int
  name: str
  username: str
  email: Optional[str] = None
  note: Optional[str] = None
  group: str = ""  # Kept for frontend compatibility


def _get_friend_profiles(friend_ids: List[str]):
  """
  Fetch profile rows for the given list of user ids.
  Returns a dict keyed by user id.
  """
  if not friend_ids:
    return {}

  resp = (
    supabase
    .table("users")
    .select("id, name, username, email")
    .in_("id", friend_ids)
    .execute()
  )
  rows = getattr(resp, "data", None) or []
  return {row["id"]: row for row in rows}


@router.get("/")
def list_friends(
  request: Request,
  q: Optional[str] = Query(None),
  group: Optional[str] = Query(None),
):
  """
  List current user's friends.
  Uses friend_links as the source of truth and joins to public.users.
  Optional filters:
    - q matches name, username, or email
    - group matches note (acts as a simple tag filter)
  """
  user = get_current_user(request)
  owner_id = user["id"]

  # Load all friend links for this owner.
  links_resp = (
    supabase
    .table("friend_links")
    .select("id, friend_id, note, created_at")
    .eq("owner_id", owner_id)
    .execute()
  )
  links = getattr(links_resp, "data", None) or []

  if not links:
    return {"friends": []}

  friend_ids = [link["friend_id"] for link in links]
  profiles_by_id = _get_friend_profiles(friend_ids)

  records: List[FriendRecord] = []

  for link in links:
    friend_id = link["friend_id"]
    profile = profiles_by_id.get(friend_id)
    if not profile:
      # If profile is missing, skip this link.
      continue

    record = FriendRecord(
      id=link["id"],
      name=profile.get("name") or "",
      username=profile.get("username") or "",
      email=profile.get("email") or "",
      note=link.get("note"),
      group="",  # No group field in friend_links; kept for UI shape
    )
    records.append(record)

  # Apply search filter q on name, username, and email.
  if q:
    q_lower = q.lower()
    filtered: List[FriendRecord] = []
    for rec in records:
      if (
        q_lower in (rec.name or "").lower()
        or q_lower in (rec.username or "").lower()
        or q_lower in (rec.email or "").lower()
      ):
        filtered.append(rec)
    records = filtered

  # Apply group filter using the note as a simple tag field.
  if group:
    g_lower = group.lower()
    filtered = []
    for rec in records:
      if g_lower in (rec.note or "").lower():
        filtered.append(rec)
    records = filtered

  # Sort by name for stable display.
  records.sort(key=lambda r: (r.name or "").lower())

  return {
    "friends": [
      {
        "id": r.id,
        "name": r.name,
        "username": r.username,
        "email": r.email or "",
        "note": r.note or "",
        "group": r.group,  # still present for current frontend
      }
      for r in records
    ]
  }


@router.post("/")
def add_friend(request: Request, payload: FriendCreate):
  """
  Add a new friend link for the current user.
  Input:
    - username (of the friend)
    - note (optional)
  Steps:
    1. Get current user from auth.
    2. Look up the friend by username in public.users.
    3. Prevent self friend links.
    4. Prevent duplicate links.
    5. Insert into friend_links.
  """
  user = get_current_user(request)
  owner_id = user["id"]

  username = (payload.username or "").strip()
  if not username:
    raise HTTPException(status_code=400, detail="Username is required")

  # Look up friend profile by username (case insensitive).
  prof_resp = (
    supabase
    .table("users")
    .select("id, name, username, email")
    .ilike("username", username)
    .limit(1)
    .execute()
  )
  profiles = getattr(prof_resp, "data", None) or []

  if not profiles:
    raise HTTPException(status_code=404, detail="User not found")

  friend = profiles[0]
  friend_id = friend["id"]

  # Prevent adding yourself as a friend.
  if friend_id == owner_id:
    raise HTTPException(status_code=400, detail="You cannot add yourself as a friend")

  # Prevent duplicate friend links.
  existing_resp = (
    supabase
    .table("friend_links")
    .select("id")
    .eq("owner_id", owner_id)
    .eq("friend_id", friend_id)
    .limit(1)
    .execute()
  )
  existing = getattr(existing_resp, "data", None) or []
  if existing:
    raise HTTPException(status_code=400, detail="This user is already in your friends list")

  # Insert the friend link.
  insert_resp = (
    supabase
    .table("friend_links")
    .insert(
      {
        "owner_id": owner_id,
        "friend_id": friend_id,
        "note": payload.note or None,
      }
    )
    .execute()
  )
  inserted = getattr(insert_resp, "data", None) or []
  if not inserted:
    raise HTTPException(status_code=500, detail="Insert failed")

  link_row = inserted[0]

  # Build response in the same shape used by list_friends.
  friend_record = {
    "id": link_row["id"],
    "name": friend.get("name") or "",
    "username": friend.get("username") or "",
    "email": friend.get("email") or "",
    "note": payload.note or "",
    "group": "",
  }

  return {
    "message": "Friend added",
    "friend": friend_record,
  }


@router.get("/groups")
def list_groups(request: Request):
  """
  Group filter support.
  Current design does not store group names on friend links.
  Return an empty list so the frontend filter stays simple.
  """
  # Ensure the user is authenticated even though we do not use the id here.
  get_current_user(request)
  return {"groups": []}
