# FILE: app/routers/settings.py
# Handles getting/saving user settings (mock for now)
# Manages backend API routes related to user settings.

from fastapi import APIRouter
from pydantic import BaseModel

# Creates a router for the "Settings" feature.
# All routes will be prefixed with /api/settings.
router = APIRouter(prefix="/api/settings", tags=["Settings"])

# Mock data store for user settings
# Acts as an in-memory database for user settings.
# Will be replaced with Supabase to save/load real user settings later.
mock_settings = {
    "notifications_enabled": True,
    "theme": "light",
    "font_size": "normal",
}

# Model defining the structure of settings data when updating settings.
class SettingsIn(BaseModel):
    notifications_enabled: bool
    theme: str
    font_size: str

# GET /api/settings/
# Retrieves the current user settings (from mock data for now).
@router.get("/")
def get_settings():
    # Returns the mock settings as the current user settings.
    return mock_settings

# POST /api/settings/
# Updates the user settings (updates mock data for now).
@router.post("/")
def update_settings(settings: SettingsIn):
    # Updates the mock settings with the provided values.
    mock_settings["notifications_enabled"] = settings.notifications_enabled
    mock_settings["theme"] = settings.theme
    mock_settings["font_size"] = settings.font_size

    # Returns a confirmation message with the updated settings.
    return {"message": "settings updated", "settings": mock_settings}
