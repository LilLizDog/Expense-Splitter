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

    # Resolve friendly first name for welcome message
    full_name = (user_meta.get("full_name") or "").strip()
    if full_name:
        first_name = full_name.split(" ")[0]
    else:
        first_name = email.split("@")[0] if email else "Friend"

    # Get all group_ids from the join table for this user
    member_resp = (
        supabase.table("group_members")
        .select("group_id")
        .eq("user_id", user_id)
        .execute()
    )

    group_ids = [row["group_id"] for row in (member_resp.data or [])]
    groups = []

    # If user is in any groups, load their id and name from groups table
    if group_ids:
        groups_resp = (
            supabase.table("groups")
            .select("id,name")
            .in_("id", group_ids)
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
