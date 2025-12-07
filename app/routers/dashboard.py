from fastapi import APIRouter, Depends
from .auth import get_current_user
from ..core.supabase_client import supabase

router = APIRouter(prefix="/api", tags=["dashboard"])

@router.get("/dashboard")
async def get_dashboard(current_user = Depends(get_current_user)):
    user_id = str(current_user.id)

    # groups where user appears in members[]
    groups_resp = supabase.table("groups") \
        .select("id,name") \
        .contains("members", [user_id]) \
        .execute()
    groups = groups_resp.data or []

    # wallet numbers from history tables
    recv_resp = supabase.table("history_received") \
        .select("amount") \
        .eq("user_id", user_id) \
        .execute()
    paid_resp = supabase.table("history_paid") \
        .select("amount") \
        .eq("user_id", user_id) \
        .execute()

    total_owed = sum([float(r["amount"]) for r in (recv_resp.data or [])])
    total_owing = sum([float(r["amount"]) for r in (paid_resp.data or [])])

    # compute's the overall net balance
    net_balance = total_owed - total_owing

    # determines the balance class for UI purposes
    if net_balance > 0:
        balance_class = "positive"
    elif net_balance < 0:
        balance_class = "negative"
    else:
        balance_class = "zero"

    # recent transactions – tweak this to your schema
    tx_resp = supabase.table("history_paid") \
        .select("amount, created_at, group_name") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .limit(5) \
        .execute()

    recent_tx = []
    for r in tx_resp.data or []:
        recent_tx.append({
            "name": r.get("group_name") or "Payment",
            "amount": float(r["amount"]),
            "sign": "-",  # because user paid
            "date": r["created_at"][:10],
            "group_name": r.get("group_name") or ""
        })

    return {
        "user_name": current_user.user_metadata.get("full_name") or "Friend",
        "wallet": {
            "owed": total_owed, 
            "owing": total_owing
        },
        "wallet_balance": net_balance,
        "balance_class": balance_class,
        "groups": groups,
        "recent_transactions": recent_tx,
    }
