from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.supabase_client import supabase
from app.routers.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# Inbox page
@router.get("/inbox", response_class=HTMLResponse)
async def inbox_page(request: Request):
    """Render the inbox page shell."""
    return templates.TemplateResponse(
        "inbox.html",
        {"request": request},
    )


# Notifications helper
def _build_notifications(rows):
    """Attach usernames and group names to raw notification rows."""
    if not rows:
        return []

    from_user_ids = set()
    group_ids = set()

    for n in rows:
        fu = n.get("from_user")
        if fu:
            from_user_ids.add(fu)
        gid = n.get("group_id")
        if gid:
            group_ids.add(gid)

    user_map = {}
    if from_user_ids:
        try:
            ures = (
                supabase.table("users")
                .select("id, username")
                .in_("id", list(from_user_ids))
                .execute()
            )
            for u in ures.data or []:
                user_map[u["id"]] = u.get("username") or "Unknown"
        except Exception as e:
            print("Error fetching notification users:", e)

    group_map = {}
    if group_ids:
        try:
            gres = (
                supabase.table("groups")
                .select("id, name")
                .in_("id", list(group_ids))
                .execute()
            )
            for g in gres.data or []:
                group_map[g["id"]] = g.get("name") or None
        except Exception as e:
            print("Error fetching notification groups:", e)

    result = []
    for n in rows:
        result.append(
            {
                "id": n["id"],
                "type": n.get("type"),
                "from_user": user_map.get(n.get("from_user"), "Unknown"),
                "group_id": n.get("group_id"),
                "group_name": group_map.get(n.get("group_id")),
                "status": n.get("status"),
                "created_at": n.get("created_at"),
            }
        )

    return result


# Notifications endpoint
@router.get("/inbox/notifications")
async def inbox_notifications(current_user=Depends(get_current_user)):
    """
    Return all notifications for the logged in user (newest first).
    No message threads, only info notifications.
    """
    try:
        res = (
            supabase.table("notifications")
            .select("*")
            .eq("to_user", current_user["id"])
            .order("created_at", desc=True)
            .execute()
        )
    except Exception as e:
        print("Error fetching notifications:", e)
        return []

    rows = res.data or []
    return _build_notifications(rows)
