from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.core.supabase_client import supabase
from app.routers.auth import get_current_user

router = APIRouter()

# Templates engine
templates = Jinja2Templates(directory="app/templates")

# ------------------------
# Inbox page
# ------------------------
@router.get("/inbox", response_class=HTMLResponse)
async def inbox_page(request: Request):
    """
    Render inbox page. Requires logged-in user.
    """
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
    Returns empty list if no messages.
    """
    try:
        # Fetch messages where user is sender or receiver
        result = (
            supabase.table("Messages")
            .select("*")
            .or_(f"sender_id.eq.{current_user['id']},reciever_id.eq.{current_user['id']}")
            .order("created_at", desc=True)
            .execute()
        )
    except Exception as e:
        # Log error if needed
        print("Error fetching messages:", e)
        return []

    if not result.data:
        return []

    # Group messages by group_id
    threads = {}
    for row in result.data:
        threads[row["group_id"]] = {
            "thread_id": row["group_id"],
            "name": row.get("sender_id", "Unknown"),
            "last_message": row.get("content", "")
        }

    return list(threads.values())


# ------------------------
# Notifications data
# ------------------------
@router.get("/inbox/notifications")
async def inbox_notifications(current_user=Depends(get_current_user)):
    """
    Fetch pending notifications for the logged-in user.
    Returns empty list if none exist.
    """
    try:
        result = (
            supabase.table("notifications")
            .select("*")
            .eq("to_user", current_user["id"])
            .eq("status", "pending")
            .execute()
        )
    except Exception as e:
        print("Error fetching notifications:", e)
        return []

    if not result.data:
        return []

    return result.data
