from fastapi import APIRouter, Depends
from .auth import get_current_user
from ..core.supabase_client import supabase

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard")
async def get_dashboard(current_user=Depends(get_current_user)):
    # Get user id in a way that works for dict or object
    if isinstance(current_user, dict):
        user_id = str(current_user.get("id"))
        user_meta = current_user.get("user_metadata") or {}
        email = current_user.get("email") or ""
    else:
        user_id = str(current_user.id)
        user_meta = getattr(current_user, "user_metadata", {}) or {}
        email = getattr(current_user, "email", "") or ""

    # Try to resolve display name from users table
    user_full_name = ""
    try:
        user_resp = (
            supabase.table("users")
            .select("name")
            .eq("id", user_id)
            .single()
            .execute()
        )
        if getattr(user_resp, "data", None):
            user_full_name = (user_resp.data.get("name") or "").strip()
    except Exception:
        user_full_name = ""

    # Resolve friendly first name for welcome message
    if user_full_name:
        base = user_full_name.split(" ")[0].strip()
        first_name = base if base else "Friend"
    else:
        raw_name = (
            user_meta.get("name")
            or user_meta.get("full_name")
            or user_meta.get("username")
            or ""
        )
        raw_name = (raw_name or "").strip()

        if raw_name:
            # Handle usernames like "preet.2022.inder" by using the part before the first dot
            if "." in raw_name and " " not in raw_name:
                base = raw_name.split(".")[0]
            else:
                # For real names like "Preetinder Kaur" take the first word
                base = raw_name.split(" ")[0]
            base = base.strip()
            first_name = base.capitalize() if base else "Friend"
        else:
            # Fallback to email local part
            local_part = email.split("@")[0] if email else ""
            first_name = local_part.capitalize() if local_part else "Friend"

    # Load groups where this user is in the members array
    groups_resp = (
        supabase.table("groups")
        .select("id,name")
        .contains("members", [user_id])
        .execute()
    )
    groups = groups_resp.data or []

    # Wallet numbers from history tables
    recv_resp = (
        supabase.table("history_received")
        .select("amount")
        .eq("user_id", user_id)
        .execute()
    )
    paid_resp = (
        supabase.table("history_paid")
        .select("amount")
        .eq("user_id", user_id)
        .execute()
    )

    total_owed = sum(float(r["amount"]) for r in (recv_resp.data or []))
    total_owing = sum(float(r["amount"]) for r in (paid_resp.data or []))

    # Compute net balance
    net_balance = total_owed - total_owing

    # Choose CSS balance class
    if net_balance > 0:
        balance_class = "positive"
    elif net_balance < 0:
        balance_class = "negative"
    else:
        balance_class = "zero"

    # Recent transactions from history_paid
    tx_resp = (
        supabase.table("history_paid")
        .select("amount, created_at, group_name")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(5)
        .execute()
    )

    recent_tx = []
    for r in tx_resp.data or []:
        recent_tx.append(
            {
                "name": r.get("group_name") or "Payment",
                "amount": float(r["amount"]),
                "sign": "-",  # user paid
                "date": r["created_at"][:10],
                "group_name": r.get("group_name") or "",
            }
        )

    return {
        "user_name": first_name,
        "wallet": {
            "owed": total_owed,
            "owing": total_owing,
        },
        "wallet_balance": net_balance,
        "balance_class": balance_class,
        "groups": groups,
        "recent_transactions": recent_tx,
    }
