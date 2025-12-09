# app/routers/payments.py

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.core.supabase_client import supabase

router = APIRouter(prefix="/api/payments", tags=["payments"])


# --------- helpers ---------

def get_current_user_id(request: Request) -> str:
    """
    Very light "auth":
    - First try X-User-Id header
    - Then ?user_id= query param
    - Fallback to a mock user so the page still works in dev
    """
    user_id = request.headers.get("X-User-Id") or request.query_params.get("user_id")
    if user_id:
        return str(user_id)

    # fallback mock for local dev
    return "user_mock_1"


# --------- Pydantic models (what we send back to JS) ---------

class Payment(BaseModel):
    id: str
    group_id: Optional[str]
    expense_id: Optional[str]
    from_user_id: str
    to_user_id: str
    amount: float
    status: str
    created_at: Optional[str]
    paid_at: Optional[str] = None
    paid_via: Optional[str] = None
    # optional - frontend currently uses expense_name only in mock mode
    expense_name: Optional[str] = None


class BalanceSummary(BaseModel):
    user_id: str
    amount_owed_by_user: float        # things user still needs to pay (to_user_id = user, status='requested')
    amount_owed_to_user: float        # things others still owe them (from_user_id = user, status='requested')


class MarkPaidRequest(BaseModel):
    paid_via: Optional[str] = None


class MarkPaidResponse(BaseModel):
    success: bool
    payment: Optional[Payment] = None


# --------- endpoints ---------

@router.get("/summary", response_model=BalanceSummary)
def get_balance_summary(request: Request, user_id: str = Depends(get_current_user_id)):
    """
    Compute outstanding balances for this user from the payments table.
    - amount_owed_by_user: sum of pending payments WHERE to_user_id = user AND status='requested'
    - amount_owed_to_user: sum of pending payments WHERE from_user_id = user AND status='requested'
    """

    # "user still owes others"
    owed_by_resp = (
        supabase.table("payments")
        .select("amount")
        .eq("to_user_id", user_id)
        .eq("status", "requested")
        .execute()
    )
    if hasattr(owed_by_resp, "error") and owed_by_resp.error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error fetching owed_by_user: {owed_by_resp.error.message}",
        )

    # "others still owe user"
    owed_to_resp = (
        supabase.table("payments")
        .select("amount")
        .eq("from_user_id", user_id)
        .eq("status", "requested")
        .execute()
    )
    if hasattr(owed_to_resp, "error") and owed_to_resp.error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error fetching owed_to_user: {owed_to_resp.error.message}",
        )

    owed_by_list = owed_by_resp.data or []
    owed_to_list = owed_to_resp.data or []

    amount_owed_by_user = float(sum(row.get("amount", 0) for row in owed_by_list))
    amount_owed_to_user = float(sum(row.get("amount", 0) for row in owed_to_list))

    return BalanceSummary(
        user_id=user_id,
        amount_owed_by_user=amount_owed_by_user,
        amount_owed_to_user=amount_owed_to_user,
    )


@router.get("/past", response_model=List[Payment])
def get_past_payments(request: Request, user_id: str = Depends(get_current_user_id)):
    """
    Fetch *paid* payments involving this user (either side of the transaction).
    This feeds the 'Past Payments' column on the page.
    """
    resp = (
        supabase.table("payments")
        .select(
            "id, group_id, expense_id, from_user_id, to_user_id, amount, "
            "status, created_at, paid_at, paid_via"
        )
        .eq("status", "paid")
        .or_(f"from_user_id.eq.{user_id},to_user_id.eq.{user_id}")
        .order("created_at", desc=True)
        .execute()
    )

    if hasattr(resp, "error") and resp.error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error fetching past payments: {resp.error.message}",
        )

    rows = resp.data or []
    return [
        Payment(
            id=str(row["id"]),
            group_id=str(row["group_id"]) if row.get("group_id") is not None else None,
            expense_id=str(row["expense_id"]) if row.get("expense_id") is not None else None,
            from_user_id=row["from_user_id"],
            to_user_id=row["to_user_id"],
            amount=float(row["amount"]),
            status=row["status"],
            created_at=row.get("created_at"),
            paid_at=row.get("paid_at"),
            paid_via=row.get("paid_via"),
        )
        for row in rows
    ]


@router.get("/outstanding", response_model=List[Payment])
def get_outstanding_payments(request: Request, user_id: str = Depends(get_current_user_id)):
    """
    Fetch *requested* payments that this user still owes.
    This feeds the 'Outstanding Payments' column on the page.
    """
    resp = (
        supabase.table("payments")
        .select(
            "id, group_id, expense_id, from_user_id, to_user_id, amount, "
            "status, created_at, paid_at, paid_via"
        )
        .eq("status", "requested")
        .eq("to_user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    if hasattr(resp, "error") and resp.error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error fetching outstanding payments: {resp.error.message}",
        )

    rows = resp.data or []
    return [
        Payment(
            id=str(row["id"]),
            group_id=str(row["group_id"]) if row.get("group_id") is not None else None,
            expense_id=str(row["expense_id"]) if row.get("expense_id") is not None else None,
            from_user_id=row["from_user_id"],
            to_user_id=row["to_user_id"],
            amount=float(row["amount"]),
            status=row["status"],
            created_at=row.get("created_at"),
            paid_at=row.get("paid_at"),
            paid_via=row.get("paid_via"),
        )
        for row in rows
    ]


@router.get("", response_model=List[Payment])
def get_all_payments(request: Request, user_id: str = Depends(get_current_user_id)):
    """
    Fetch ALL payments involving this user (requested + paid).
    Frontend can split into 'Requested' and 'Past', but the page is
    now using /outstanding and /past for clarity.
    """
    resp = (
        supabase.table("payments")
        .select(
            "id, group_id, expense_id, from_user_id, to_user_id, amount, "
            "status, created_at, paid_at, paid_via"
        )
        .or_(f"from_user_id.eq.{user_id},to_user_id.eq.{user_id}")
        .order("created_at", desc=True)
        .execute()
    )

    if hasattr(resp, "error") and resp.error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error fetching payments: {resp.error.message}",
        )

    rows = resp.data or []
    return [
        Payment(
            id=str(row["id"]),
            group_id=str(row["group_id"]) if row.get("group_id") is not None else None,
            expense_id=str(row["expense_id"]) if row.get("expense_id") is not None else None,
            from_user_id=row["from_user_id"],
            to_user_id=row["to_user_id"],
            amount=float(row["amount"]),
            status=row["status"],
            created_at=row.get("created_at"),
            paid_at=row.get("paid_at"),
            paid_via=row.get("paid_via"),
        )
        for row in rows
    ]


@router.post("/{payment_id}/pay", response_model=MarkPaidResponse)
def mark_payment_as_paid(
    payment_id: str,
    body: MarkPaidRequest,
    request: Request,
    user_id: str = Depends(get_current_user_id),
):
    """
    Mark a payment as paid in Supabase.
    - Only the user in to_user_id can mark it paid
    - Only allowed when status='requested'
    - sets status='paid'
    - sets paid_at=now (UTC)
    - optionally stores paid_via
    """

    # 1) Fetch the payment first
    fetch_resp = (
        supabase.table("payments")
        .select(
            "id, group_id, expense_id, from_user_id, to_user_id, amount, "
            "status, created_at, paid_at, paid_via"
        )
        .eq("id", payment_id)
        .single()
        .execute()
    )

    if hasattr(fetch_resp, "error") and fetch_resp.error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error fetching payment: {fetch_resp.error.message}",
        )

    row = fetch_resp.data
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    # 2) Security: verify user is allowed to pay
    if row["to_user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot pay for someone else's payment.",
        )

    # 3) Only allow transition from requested -> paid
    if row["status"] != "requested":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment is not in a payable state.",
        )

    # 4) Perform the update
    now_iso = datetime.now(timezone.utc).isoformat()

    update_payload = {
        "status": "paid",
        "paid_at": now_iso,
    }
    if body.paid_via:
        update_payload["paid_via"] = body.paid_via

    update_resp = (
        supabase.table("payments")
        .update(update_payload)
        .eq("id", payment_id)
        .select(
            "id, group_id, expense_id, from_user_id, to_user_id, amount, "
            "status, created_at, paid_at, paid_via"
        )
        .single()
        .execute()
    )

    if hasattr(update_resp, "error") and update_resp.error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error updating payment: {update_resp.error.message}",
        )
<<<<<<< HEAD

    updated = update_resp.data
=======
>>>>>>> 74ab3c988b6b3b1fb1f5cbbab4002d27fc3d3606
    payment = Payment(
        id=str(updated["id"]),
        group_id=str(updated["group_id"]) if updated.get("group_id") is not None else None,
        expense_id=str(updated["expense_id"]) if updated.get("expense_id") is not None else None,
        from_user_id=updated["from_user_id"],
        to_user_id=updated["to_user_id"],
        amount=float(updated["amount"]),
        status=updated["status"],
        created_at=updated.get("created_at"),
        paid_at=updated.get("paid_at"),
        paid_via=updated.get("paid_via"),
    )

    # -----------------------------------------
    # Write history logs for paid transactions
    # -----------------------------------------

    # Load payer and receiver names
    payer_row = (
        supabase.table("users")
        .select("name")
        .eq("id", payment.from_user_id)
        .single()
        .execute()
    ).data or {}

    receiver_row = (
        supabase.table("users")
        .select("name")
        .eq("id", payment.to_user_id)
        .single()
        .execute()
    ).data or {}

    payer_name = payer_row.get("name") or "Unknown"
    receiver_name = receiver_row.get("name") or "Unknown"

    # Load expense title and group for logging
    expense_row = (
        supabase.table("expenses")
        .select("description, group_id")
        .eq("id", payment.expense_id)
        .single()
        .execute()
    ).data or {}

    expense_title = expense_row.get("description") or "Expense"
    # look up group name
    group_name = (
        supabase.table("groups")
        .select("name")
        .eq("id", expense_row.get("group_id"))
        .single()
        .execute()
    ).data.get("name") if expense_row.get("group_id") else "Unknown Group"

    # Insert paid history if current user is the payer
    if payment.from_user_id == user_id:
        supabase.table("history_paid").insert({
            "user_id": user_id,
            "to_name": receiver_name,
            "amount": payment.amount,
            "group_name": group_name,
            "expense_title": expense_title,
        }).execute()

    # Insert received history if current user is the receiver
    if payment.to_user_id == user_id:
        supabase.table("history_received").insert({
            "user_id": user_id,
            "from_name": payer_name,
            "amount": payment.amount,
            "group_name": group_name,
            "expense_title": expense_title,
        }).execute()

    return MarkPaidResponse(success=True, payment=payment)
