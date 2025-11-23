from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from app.core.supabase_client import supabase
from app.routers.auth import get_current_user

router = APIRouter()

# --- Inbox page ---
@router.get("/inbox", response_class=HTMLResponse)
async def inbox_page(request: Request):
    return request.app.state.templates.TemplateResponse(
        "inbox.html",
        {"request": request}
    )

# --- Messages data ---
@router.get("/inbox/data")
async def inbox_data():
    result = supabase.table("messages").select("thread_id, sender_name, message").order("created_at", desc=True).execute()

    threads = {}
    for row in result.data:
        threads[row["thread_id"]] = {
            "thread_id": row["thread_id"],
            "name": row["sender_name"],
            "last_message": row["message"]
        }

    return list(threads.values())

# --- Notifications data ---
@router.get("/inbox/notifications")
async def inbox_notifications(current_user=Depends(get_current_user)):
    user_id = current_user["id"]

    result = supabase.table("notifications") \
        .select("*") \
        .eq("to_user", user_id) \
        .eq("status", "pending") \
        .execute()

    return result.data

# --- Accept / Decline action ---
@router.post("/inbox/notifications/action")
async def handle_notification_action(payload: dict, current_user=Depends(get_current_user)):
    user_id = current_user["id"]
    notification_id = payload.get("notification_id")
    action = payload.get("action")

    if action not in ["accept", "decline"]:
        return JSONResponse({"error": "Invalid action"}, status_code=400)

    # Update notification status
    status = "accepted" if action == "accept" else "declined"
    supabase.table("notifications").update({"status": status}).eq("id", notification_id).execute()

    # Handle friend request acceptance
    notif_res = supabase.table("notifications").select("*").eq("id", notification_id).single().execute()
    notif = notif_res.data

    if notif and notif.get("type") == "friend_request" and action == "accept":
        supabase.table("friends").insert({
            "user1": notif["from_user"],
            "user2": notif["to_user"]
        }).execute()

    return {"success": True}
