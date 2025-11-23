from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from app.core.supabase_client import supabase
from app.routers.auth import get_current_user  # this uses real login

router = APIRouter()

# ------------------------
# Inbox page
# ------------------------
@router.get("/inbox", response_class=HTMLResponse)
async def inbox_page(request: Request, current_user=Depends(get_current_user)):
    """
    Render inbox.html page for the logged-in user.
    """
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")

    return templates.TemplateResponse(
        "inbox.html",
        {"request": request, "user": current_user}
    )

# ------------------------
# Messages data
# ------------------------
@router.get("/inbox/data")
async def inbox_data(current_user=Depends(get_current_user)):
    """
    Return all messages for the logged-in user, grouped by group_id.
    """
    try:
        result = supabase.table("Messages") \
            .select("*") \
            .eq("user_id", current_user["id"]) \
            .order("created_at", desc=True) \
            .execute()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

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
    Return notifications for the logged-in user.
    """
    try:
        result = supabase.table("notifications") \
            .select("*") \
            .eq("to_user", current_user["id"]) \
            .eq("status", "pending") \
            .execute()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

    return result.data
