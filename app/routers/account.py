# app/routers/account.py

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .auth import get_current_user
from ..core.supabase_client import supabase
from ..main import templates

router = APIRouter(tags=["account"])


class AccountUpdate(BaseModel):
    full_name: str
    username: str
    phone_number: str | None = None
    display_currency: str


def _load_user_row(user_id: str) -> dict:
    # Reads from public.users table
    resp = (
        supabase
        .table("users")
        .select("id,name,email,username,phone_number,display_currency")
        .eq("id", user_id)
        .single()
        .execute()
    )

    row = resp.data
    if not row:
        raise HTTPException(status_code=404, detail="User not found in public.users")

    return {
        "id": row["id"],
        "email": row.get("email") or "",
        "full_name": row.get("name") or "",
        "username": row.get("username") or "",
        "phone_number": row.get("phone_number") or "",
        "display_currency": row.get("display_currency") or "USD",
    }


@router.get("/account", response_class=HTMLResponse)
async def account_page(
    request: Request,
    current_user=Depends(get_current_user),
):
    """
    Render the Account page.
    Data comes from public.users.
    """
    user_id = current_user["id"]
    user = _load_user_row(user_id)

    context = {
        "request": request,
        "user": user,
    }
    return templates.TemplateResponse("account.html", context)


@router.get("/api/account")
async def get_account(current_user=Depends(get_current_user)):
    """
    JSON endpoint for the logged-in user's account info.
    """
    user_id = current_user["id"]
    user = _load_user_row(user_id)
    return {"user": user}


@router.put("/api/account")
async def update_account(
    payload: AccountUpdate,
    current_user=Depends(get_current_user),
):
    """
    Update the logged-in user's info in public.users.
    """
    user_id = current_user["id"]

    update_data = {
        "name": payload.full_name,
        "username": payload.username,
        "phone_number": payload.phone_number or "",
        "display_currency": payload.display_currency,
    }

    try:
        resp = (
            supabase
            .table("users")
            .update(update_data)
            .eq("id", user_id)
            .execute()
        )
        
        # Check if update was successful
        if not resp.data:
            raise HTTPException(status_code=400, detail="Failed to update user")
            
    except Exception as e:
        print(f"Error updating account: {e}")
        raise HTTPException(status_code=400, detail=f"Update failed: {str(e)}")

    user = _load_user_row(user_id)
    return {"user": user}
