from fastapi import APIRouter, Request, Depends, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.core.supabase_client import supabase
from app.routers.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# ------------------------
# Inbox page
# ------------------------
@router.get("/inbox", response_class=HTMLResponse)
async def inbox_page(request: Request):
    return templates.TemplateResponse(
        "inbox.html",
        {"request": request}
    )


# ------------------------
# Messages data
# ------------------------
@router.get("/inbox/data")
async def inbox_data(current_user=Depends(get_current_user)):
    """
    Fetch messages for the logged-in user, grouped by group_id.
    """
    try:
        # Fetch messages and include sender username
        result = (
            supabase.table("Messages")
            .select("*, sender:Users(id, username)")
            .or_(f"sender_id.eq.{current_user['id']},reciever_id.eq.{current_user['id']}")
            .order("created_at", desc=True)
            .execute()
        )
    except Exception as e:
        print("Error fetching messages:", e)
        return []

    if not result.data:
        return []

    threads = {}
    for row in result.data:
        sender_name = row.get("sender", {}).get("username", "Unknown")
        threads[row["group_id"]] = {
            "thread_id": row["group_id"],
            "name": sender_name,
            "last_message": row.get("content", "")
        }

    return list(threads.values())


# ------------------------
# Notifications data
# ------------------------
@router.get("/inbox/notifications")
async def inbox_notifications(current_user=Depends(get_current_user)):
    """
    Fetch pending notifications for the logged-in user with friendly names.
    """
    try:
        result = (
            supabase.table("notifications")
            .select("*, from_user:Users(id, username), group:Groups(id, name)")
            .eq("to_user", current_user["id"])
            .eq("status", "pending")
            .execute()
        )
    except Exception as e:
        print("Error fetching notifications:", e)
        return []

    if not result.data:
        return []

    notifications = []
    for n in result.data:
        notif = {
            "id": n["id"],
            "type": n["type"],
            "from_user": n.get("from_user", {}).get("username", "Unknown"),
            "group_name": n.get("group", {}).get("name") if n.get("type") == "Group Invite" else None
        }
        notifications.append(notif)

    return notifications


# ------------------------
# Handle Accept/Decline
# ------------------------
@router.post("/inbox/notifications/{notif_id}")
async def handle_notification(notif_id: int, payload: dict = Body(...), current_user=Depends(get_current_user)):
    action = payload.get("action")
    try:
        notif_res = supabase.table("notifications").select("*").eq("id", notif_id).execute()
        if not notif_res.data:
            return JSONResponse({"success": False, "error": "Notification not found"})

        notif = notif_res.data[0]

        if notif["to_user"] != current_user["id"]:
            return JSONResponse({"success": False, "error": "Unauthorized"})

        # Handle friend request
        if notif["type"] == "Friend Request" and action == "accept":
            supabase.table("friends").insert({
                "user_id": current_user["id"],
                "friend_id": notif["from_user"]
            }).execute()
        # Handle group invite
        elif notif["type"] == "Group Invite" and action == "accept":
            supabase.table("group_members").insert({
                "group_id": notif["group_id"],
                "user_id": current_user["id"]
            }).execute()

        # Update notification status
        supabase.table("notifications").update({"status": action}).eq("id", notif_id).execute()

        return {"success": True}

    except Exception as e:
        print("Error handling notification:", e)
        return {"success": False, "error": str(e)}
