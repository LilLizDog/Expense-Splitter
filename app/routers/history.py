# FILE: app/routers/history.py
# History API that builds per-user expense history using expenses
# and expense_participants. Each row is a single user's view of an
# expense with a signed amount.

from typing import Optional, Dict, Any, List, Set

from fastapi import APIRouter, Query, HTTPException, Depends

from ..core.supabase_client import supabase
from .auth import get_current_user

router = APIRouter(prefix="/api/history", tags=["History"])


def _get_user_id(current_user: Any) -> str:
    """Return the authenticated user's id as a string."""
    if isinstance(current_user, dict):
        return str(current_user.get("id"))
    return str(getattr(current_user, "id", ""))


@router.get("/")
def get_history(
    group: Optional[str] = Query(None),
    person: Optional[str] = Query(None),
    entry_type: Optional[str] = Query(None, alias="type"),
    current_user=Depends(get_current_user),
):
    """
    Build history entries for the current user.

    Semantics for signed amounts (from this user's perspective):
      - If user created the expense:
          amount = sum of all participant shares for this expense (>= 0)
      - If user is only a participant:
          amount = - share for this user on that expense (<= 0)

    Response shape is kept compatible with the existing frontend:
      - "paid"     = expenses you created (amount >= 0)
      - "received" = expenses you were added to (amount <= 0)
    """
    user_id = _get_user_id(current_user)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # ----- 1. Expenses created by this user -----
    creator_resp = (
        supabase.table("expenses")
        .select(
            "id, user_id, group_id, amount, description, "
            "expense_date, created_at"
        )
        .eq("user_id", user_id)
        .execute()
    )
    if creator_resp.data is None:
        raise HTTPException(status_code=500, detail="Error fetching created expenses")
    creator_expenses: List[Dict[str, Any]] = creator_resp.data or []

    creator_expense_ids: List[str] = []
    group_ids: Set[str] = set()
    creator_ids: Set[str] = set()

    for e in creator_expenses:
        eid = e.get("id")
        if not eid:
            continue
        creator_expense_ids.append(eid)
        group_id = e.get("group_id")
        if group_id:
            group_ids.add(group_id)
        creator_ids.add(e.get("user_id"))

    # ----- 2. Expenses where this user is a participant -----
    parts_resp = (
        supabase.table("expense_participants")
        .select("expense_id, share")
        .eq("member_id", user_id)
        .execute()
    )
    if parts_resp.data is None:
        raise HTTPException(
            status_code=500, detail="Error fetching participant rows"
        )
    participant_rows: List[Dict[str, Any]] = parts_resp.data or []

    # Map expense_id -> total share for this user (in case of duplicates)
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
        if part_exp_resp.data is None:
            raise HTTPException(
                status_code=500,
                detail="Error fetching participant expenses",
            )
        participant_expenses = part_exp_resp.data or []
        for e in participant_expenses:
            group_id = e.get("group_id")
            if group_id:
                group_ids.add(group_id)
            creator_ids.add(e.get("user_id"))

    # ----- 3. Look up group names -----
    group_name_by_id: Dict[str, str] = {}
    if group_ids:
        group_resp = (
            supabase.table("groups")
            .select("id, name")
            .in_("id", list(group_ids))
            .execute()
        )
        if group_resp.data is None:
            raise HTTPException(status_code=500, detail="Error fetching groups")
        for g in group_resp.data or []:
            gid = g.get("id")
            if gid:
                group_name_by_id[gid] = g.get("name") or ""

    # ----- 4. Look up creator names for participant entries -----
    user_name_by_id: Dict[str, str] = {}
    if creator_ids:
        users_resp = (
            supabase.table("users")
            .select("id, name")
            .in_("id", list(creator_ids))
            .execute()
        )
        if users_resp.data is None:
            raise HTTPException(status_code=500, detail="Error fetching users")
        for u in users_resp.data or []:
            uid = u.get("id")
            if uid:
                user_name_by_id[uid] = u.get("name") or ""

    # ----- 5. For creator expenses, compute how much others owe me -----
    net_owed_to_me_by_expense: Dict[str, float] = {}
    if creator_expense_ids:
        shares_resp = (
            supabase.table("expense_participants")
            .select("expense_id, share")
            .in_("expense_id", creator_expense_ids)
            .execute()
        )
        if shares_resp.data is None:
            raise HTTPException(
                status_code=500,
                detail="Error fetching participant shares for created expenses",
            )
        for row in shares_resp.data or []:
            eid = row.get("expense_id")
            if not eid:
                continue
            share = float(row.get("share") or 0)
            net_owed_to_me_by_expense[eid] = (
                net_owed_to_me_by_expense.get(eid, 0.0) + share
            )

    # ----- 6. Build "paid" entries: expenses you created -----
    paid_entries: List[Dict[str, Any]] = []
    for e in creator_expenses:
        eid = e.get("id")
        if not eid:
            continue

        # Positive amount: what others owe you on this expense
        amount_val = net_owed_to_me_by_expense.get(eid, 0.0)

        group_name = group_name_by_id.get(e.get("group_id"), "")
        date_val = e.get("expense_date") or e.get("created_at") or ""

        paid_entries.append(
            {
                "id": eid,
                "date": date_val,
                "amount": amount_val,
                "group": group_name,
                "description": e.get("description") or "",
                "creator_name": user_name_by_id.get(user_id, ""),
            }
        )

    # ----- 7. Build "received" entries: expenses you are in as participant -----
    creator_expense_ids_set = {e.get("id") for e in creator_expenses if e.get("id")}
    received_entries: List[Dict[str, Any]] = []

    for e in participant_expenses:
        eid = e.get("id")
        if not eid:
            continue

        # If you also created this expense, treat it as a creator row only
        if eid in creator_expense_ids_set:
            continue

        group_name = group_name_by_id.get(e.get("group_id"), "")
        date_val = e.get("expense_date") or e.get("created_at") or ""

        # Negative amount: what you owe to the creator on this expense
        my_share = share_by_expense_for_me.get(eid, 0.0)
        amount_val = -float(my_share)

        creator_name = user_name_by_id.get(e.get("user_id"), "")

        received_entries.append(
            {
                "id": eid,
                "date": date_val,
                "amount": amount_val,
                "group": group_name,
                "description": e.get("description") or "",
                "creator_name": creator_name,
            }
        )

    # ----- 8. Optional filters -----

    # Group filter
    if group:
        g = group.lower()
        paid_entries = [
            row for row in paid_entries if g in (row.get("group") or "").lower()
        ]
        received_entries = [
            row for row in received_entries if g in (row.get("group") or "").lower()
        ]

    # Person filter: for now only makes sense on "received" where we know creator
    if person:
        p = person.lower()
        received_entries = [
            row
            for row in received_entries
            if p in (row.get("creator_name") or "").lower()
        ]

    # Type filter
    if entry_type == "received":
        paid_entries = []
    elif entry_type == "paid":
        received_entries = []

    return {
        "received": received_entries,
        "paid": paid_entries,
    }


@router.get("/groups")
def get_history_groups(current_user=Depends(get_current_user)):
    """Return all distinct group names that appear in this user's history."""
    user_id = _get_user_id(current_user)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Reuse the logic above to find all relevant expenses
    # 1) created by user
    creator_resp = (
        supabase.table("expenses")
        .select("id, group_id")
        .eq("user_id", user_id)
        .execute()
    )
    if creator_resp.data is None:
        raise HTTPException(status_code=500, detail="Error fetching created expenses")
    creator_expenses = creator_resp.data or []
    creator_expense_ids = [e.get("id") for e in creator_expenses if e.get("id")]

    # 2) participant expenses
    parts_resp = (
        supabase.table("expense_participants")
        .select("expense_id")
        .eq("member_id", user_id)
        .execute()
    )
    if parts_resp.data is None:
        raise HTTPException(status_code=500, detail="Error fetching participant rows")
    participant_ids = [
        row.get("expense_id") for row in (parts_resp.data or []) if row.get("expense_id")
    ]

    all_ids = list({*(creator_expense_ids or []), *(participant_ids or [])})
    if not all_ids:
        return {"groups": []}

    exp_resp = (
        supabase.table("expenses")
        .select("group_id")
        .in_("id", all_ids)
        .execute()
    )
    if exp_resp.data is None:
        raise HTTPException(status_code=500, detail="Error fetching expenses")

    group_ids = {
        e.get("group_id") for e in (exp_resp.data or []) if e.get("group_id")
    }
    if not group_ids:
        return {"groups": []}

    group_resp = (
        supabase.table("groups")
        .select("id, name")
        .in_("id", list(group_ids))
        .execute()
    )
    if group_resp.data is None:
        raise HTTPException(status_code=500, detail="Error fetching groups")

    names = []
    for g in group_resp.data or []:
        if g.get("name"):
            names.append(g.get("name"))

    return {"groups": sorted(set(names))}
