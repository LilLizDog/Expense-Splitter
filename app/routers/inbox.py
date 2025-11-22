from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from app.core.supabase_client import supabase

router = APIRouter()

@router.get("/inbox", response_class=HTMLResponse)
async def inbox_page(request: Request):
    return request.app.state.templates.TemplateResponse(
    request,
    "inbox.html",
    {}
)

@router.get("/inbox/data")
async def inbox_data():
    # Example query - adjust to match your schema!
    result = supabase.table("messages").select("thread_id, sender_name, message").order("created_at", desc=True).execute()

    # Simplify and group mock-style
    threads = {}
    for row in result.data:
        threads[row["thread_id"]] = {
            "thread_id": row["thread_id"],
            "name": row["sender_name"],
            "last_message": row["message"]
        }

    return list(threads.values())
