# FILE: app/routers/dashboard.py

from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, Depends
from .auth import get_current_user
from ..core.supabase_client import supabase

router = APIRouter(prefix="/api", tags=["dashboard"])


def _extract_user_info(current_user: Any) -> Tuple[str, Dict[str, Any], str]:
    """
    Extract user id, user metadata, and email from the auth object.
    Handles both dict and object shapes.
    """
    if isinstance(current_user, dict):
        user_id = str(current_user.get("id"))
        user_meta = current_user.get("user_metadata") or {}
        email = current_user.get("email") or ""
    else:
        user_id = str(getattr(current_user, "id", ""))
        user_meta = getattr(current_user, "user_metadata", {}) or {}
        email = getattr(current_user, "email", "") or ""

    return user_id, user_meta, email


def _resolve_first_name(user_id: str, user_meta: Dict[str, Any], email: str) -> str:
    """
    Resolve a friendly first name for the welcome heading.
    Prefers the users table, then metadata, then email local part.
    """
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

    if user_full_name:
        base = user_full_name.split(" ")[0].strip()
        return base if base else "Friend"

    raw_name = (
        user_meta.get("name")
        or user_meta.get("full_name")
        or user_meta.get("username")
        or ""
    )
    raw_name = (raw_name or "").strip()

    if raw_name:
        if "." in raw_name and " " not in raw_name:
            base = raw_name.split(".")[0]
        else:
        # real names like "Preetinder Kaur" take the first word
            base = raw_name.split(" ")[0]
        base = base.strip()
        return base.capitalize() if base else "Friend"

    local_part = email.split("@")[0] if email else ""
    return local_part.capitalize() if local_part else "Friend"


def _build_wallet_and_recent(user_id: str) -> Dict[str, Any]:
    """
    Build wallet totals and recent transactions for the dashboard by
    reusing the same semantics as the history page.

    Semantics from this user's perspective:
      - Creator entries (paid): amount >= 0 means others owe you (green).
      - Participant entries (received): amount <= 0 means you owe others (red).
    """
    # 1. Expenses created by this user
    creator_resp = (
        supabase.table("expenses")
        .select(
            "id, user_id, group_id, amount, description, "
            "expense_date, created_at"
        )
        .eq("user_id", user_id)
        .execute()
    )
    creator_expenses = creator_resp.data or []

    creator_expense_ids: List[str] = []
    group_ids = set()

    for e in creator_expenses:
        eid = e.get("id")
        if not eid:
            continue
        creator_expense_ids.append(eid)
        group_id = e.get("group_id")
        if group_id:
            group_ids.add(group_id)

    # 2. Expenses where this user is a participant
    parts_resp = (
        supabase.table("expense_participants")
        .select("expense_id, share")
        .eq("member_id", user_id)
        .execute()
    )
    participant_rows = parts_resp.data or []

    share_by_expense_for_me: Dict[str, float] = {}
    participant_expense_ids: List[str] = []

    for row in participant_rows:
        eid = row.get("expense_id")
        if not eid:
            continue
        share = float(row.get("share") or 0)
        share_by_expense_for_me[eid] = share_by_expense_for_me.get(eid, 0.0) + share
        participant_expense_ids.append(eid)

    participant_expenses: List[Dict[str, Any]] = []
    if participant_expense_ids:
        part_exp_resp = (
            supabase.table("expenses")
            .select(
                "id, user_id, group_id, amount, description, "
                "expense_date, created_at"
            )
            .in_("id", participant_expense_ids)
            .execute()
        )
        participant_expenses = part_exp_resp.data or []
        for e in participant_expenses:
            group_id = e.get("group_id")
            if group_id:
                group_ids.add(group_id)

    # 3. Group names
    group_name_by_id: Dict[str, str] = {}
    if group_ids:
        group_resp = (
            supabase.table("groups")
            .select("id, name")
            .in_("id", list(group_ids))
            .execute()
        )
        for g in group_resp.data or []:
            gid = g.get("id")
            if gid:
                group_name_by_id[gid] = g.get("name") or ""

    # 4. For creator expenses, compute how much others owe me
    net_owed_to_me_by_expense: Dict[str, float] = {}
    if creator_expense_ids:
        shares_resp = (
            supabase.table("expense_participants")
            .select("expense_id, share")
            .in_("expense_id", creator_expense_ids)
            .execute()
        )
        for row in shares_resp.data or []:
            eid = row.get("expense_id")
            if not eid:
                continue
            share = float(row.get("share") or 0)
            net_owed_to_me_by_expense[eid] = (
                net_owed_to_me_by_expense.get(eid, 0.0) + share
            )

    # 5. Build creator entries (green on history)
    entries: List[Dict[str, Any]] = []

    for e in creator_expenses:
        eid = e.get("id")
        if not eid:
            continue

        amount_val = net_owed_to_me_by_expense.get(eid, 0.0)
        if amount_val == 0:
            continue

        group_name = group_name_by_id.get(e.get("group_id"), "")
        date_val = e.get("expense_date") or e.get("created_at") or ""

        entries.append(
            {
                "kind": "paid",  # you created it, others owe you
                "amount": float(amount_val),
                "date": date_val,
                "group_name": group_name,
                "description": e.get("description") or "",
            }
        )

    # 6. Build participant entries (red on history)
    creator_expense_ids_set = {e.get("id") for e in creator_expenses if e.get("id")}

    for e in participant_expenses:
        eid = e.get("id")
        if not eid:
            continue

        if eid in creator_expense_ids_set:
            continue

        date_val = e.get("expense_date") or e.get("created_at") or ""
        group_name = group_name_by_id.get(e.get("group_id"), "")

        my_share = share_by_expense_for_me.get(eid, 0.0)
        amount_val = -float(my_share)  # negative means you owe

        if amount_val == 0:
            continue

        entries.append(
            {
                "kind": "received",  # from history view, you are participant
                "amount": float(amount_val),
                "date": date_val,
                "group_name": group_name,
                "description": e.get("description") or "",
            }
        )

    # 7. Wallet totals
    total_owed = sum(e["amount"] for e in entries if e["amount"] > 0)
    total_owing = sum(-e["amount"] for e in entries if e["amount"] < 0)

    net_balance = total_owed - total_owing
    if net_balance > 0:
        balance_class = "positive"
    elif net_balance < 0:
        balance_class = "negative"
    else:
        balance_class = "zero"

    # 8. Recent transactions, top 5 by date (same rows as history)
    # Sort by date descending. Expense dates are ISO strings, so string sort works.
    entries_sorted = sorted(
        entries,
        key=lambda r: r.get("date") or "",
        reverse=True,
    )
    top5 = entries_sorted[:5]

    recent_transactions: List[Dict[str, Any]] = []
    for row in top5:
        amt = float(row["amount"])
        sign = "+" if amt > 0 else "-"
        recent_transactions.append(
            {
                "name": row["description"] or "Expense",
                "amount": abs(amt),
                "sign": sign,
                "date": (row.get("date") or "")[:10],
                "group_name": row.get("group_name") or "",
            }
        )

    return {
        "total_owed": total_owed,
        "total_owing": total_owing,
        "net_balance": net_balance,
        "balance_class": balance_class,
        "recent_transactions": recent_transactions,
    }


@router.get("/dashboard")
async def get_dashboard(current_user=Depends(get_current_user)):
    user_id, user_meta, email = _extract_user_info(current_user)
    first_name = _resolve_first_name(user_id, user_meta, email)

    # Groups where this user is in the members array
    groups_resp = (
        supabase.table("groups")
        .select("id,name")
        .contains("members", [user_id])
        .execute()
    )
    groups = groups_resp.data or []

    # Wallet and recent transactions based on history style logic
    wallet_info = _build_wallet_and_recent(user_id)

    return {
        "user_name": first_name,
        "wallet": {
            "owed": wallet_info["total_owed"],
            "owing": wallet_info["total_owing"],
        },
        "wallet_balance": wallet_info["net_balance"],
        "balance_class": wallet_info["balance_class"],
        "groups": groups,
        "recent_transactions": wallet_info["recent_transactions"],
    }
