# Handles getting/saving user settings, now using Supabase
# Allows users to view and update their settings stored in Supabase

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..core.supabase_client import supabase  # Using shared Supabase client

# Sets up the router for settings-related routes with prefix /api/settings
router = APIRouter(prefix="/api/settings", tags=["Settings"])

# Defines the structure of settings data expected in requests
class SettingsIn(BaseModel):
    notifications_enabled: bool
    theme: str
    font_size: str

# Temporary function for a fake logged-in user
def get_current_user_id() -> str:
    return "demo-user-1"

# GET retrieves the current user's settings
@router.get("/")
def get_settings():
    user_id = get_current_user_id()

    # Try to fetch the user's settings from Supabase
    resp = (
        supabase
        .table("settings")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )

    rows = resp.data or []

    # If this user has no settings yet, create default row
    if not rows:
        # if user has no settings yet, create default row
        create_resp = (
            supabase
            .table("settings")
            .insert({
                "user_id": user_id,
                "notifications_enabled": True,
                "theme": "light",
                "font_size": "normal",
            })
            .execute()
        )
        row = (create_resp.data or [{}])[0]
    else:
        row = rows[0]

    # Return settings in expected format
    return {
        "notifications_enabled": row.get("notifications_enabled", True),
        "theme": row.get("theme", "light"),
        "font_size": row.get("font_size", "normal"),
    }

# POST Updates or creates the current user's settings
@router.post("/")
def update_settings(settings: SettingsIn):
    user_id = get_current_user_id()

    # First check if a settings row already exists for this user
    latest_resp = (
        supabase
        .table("settings")
        .select("id")
        .eq("user_id", user_id)
        .execute()
    )

    latest_rows = latest_resp.data or []

    # If a row exists, update it
    if latest_rows:
        settings_id = latest_rows[0]["id"]
        resp = (
            supabase
            .table("settings")
            .update(
                {
                    "notifications_enabled": settings.notifications_enabled,
                    "theme": settings.theme,
                    "font_size": settings.font_size,
                },
                returning="representation"       
            )
            .eq("id", settings_id)
            .execute()
        )
    else:
        # Otherwise, create the first settings row for this user
        resp = (
            supabase
            .table("settings")
            .insert(
                {
                    "user_id": user_id,
                    "notifications_enabled": settings.notifications_enabled,
                    "theme": settings.theme,
                    "font_size": settings.font_size,
                },
                returning="representation"  # Return the new row   
            )
            .execute()
        )

    # If Supabase didn't return data, something went wrong
    if not resp.data:
        raise HTTPException(status_code=500, detail="Could not save settings")

    return {"message": "settings updated", "settings": resp.data[0]}
