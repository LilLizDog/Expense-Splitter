# app/routers/payments.py

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.core.supabase_client import supabase
from .auth import get_current_user

router = APIRouter(prefix="/api/payments", tags=["payments"])


# --------- helpers ---------

def get_current_user_id(current_user=Depends(get_current_user)) -> str:
    """
    Use the authenticated Supabase user.
    Raises 401 if not logged in (handled by get_current_user).
    """
    return str(current_user["id"])


def _attach_expense_names(payment_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Given a list of raw payment rows (each may have expense_id),
    fetch matching expenses and attach `expense_name` from expenses.description.
    """
    if not payment_rows:
        return []
    
    expense_ids = {
        row["expense_id"]
        for row in payment_rows
        if row.get("expense_id") is not None
    }

    if not expense_ids:
        # No expense IDs, just add None for expense_name
        for row in payment_rows:
            row["expense_name"] = None
        return payment_rows

    try:
        exp_resp = (
            supabase.table("expenses")
            .select("id, description")
            .in_("id", list(expense_ids))
            .execute()
        )

        if hasattr(exp_resp, "error") and exp_resp.error:
            print(f"Error fetching expense descriptions: {exp_resp.error}")
            # Continue without expense names rather than failing
            for row in payment_rows:
                row["expense_name"] = None
            return payment_rows

        exp_rows = exp_resp.data or []
        desc_by_id: Dict[str, Optional[str]] = {
            row["id"]: row.get("description") for row in exp_rows
        }

        for row in payment_rows:
            eid = row.get("expense_id")
            row["expense_name"] = desc_by_id.get(eid) if eid in desc_by_id else None

        return payment_rows
    except Exception as e:
        print(f"Exception in _attach_expense_names: {e}")
        # Continue without expense names rather than failing
        for row in payment_rows:
            row["expense_name"] = None
        return payment_rows


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
    # pulled from expenses.description
    expense_name: Optional[str] = None


class BalanceSummary(BaseModel):
    user_id: str
    amount_owed_by_user: float        # user still needs to pay (to_user_id = user, status='requested')
    amount_owed_to_user: float        # others still owe user (from_user_id = user, status='requested')


class MarkPaidRequest(BaseModel):
    paid_via: Optional[str] = None


class MarkPaidResponse(BaseModel):
    success: bool
    payment: Optional[Payment] = None


# --------- endpoints ---------

@router.get("/summary", response_model=BalanceSummary)
def get_balance_summary(user_id: str = Depends(get_current_user_id)):
    """
    Compute outstanding balances for this user from the payments table.
    """
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
def get_past_payments(user_id: str = Depends(get_current_user_id)):
    """
    Fetch *paid* payments involving this user (either side of the transaction).
    """
    print(f"Fetching past payments for user_id: {user_id}")
    
    try:
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
            print(f"Supabase error: {resp.error}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error fetching past payments: {resp.error.message}",
            )

        print(f"Found {len(resp.data or [])} past payments")
        rows = _attach_expense_names(resp.data or [])

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
                expense_name=row.get("expense_name"),
            )
            for row in rows
        ]
    except HTTPException:
        raise
    except Exception as e:
        print(f"Exception in get_past_payments: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching past payments: {str(e)}"
        )


@router.get("/outstanding", response_model=List[Payment])
def get_outstanding_payments(user_id: str = Depends(get_current_user_id)):
    """
    Fetch *requested* payments that this user still owes.
    """
    print(f"Fetching outstanding payments for user_id: {user_id}")
    
    try:
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
            print(f"Supabase error: {resp.error}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error fetching outstanding payments: {resp.error.message}",
            )

        print(f"Found {len(resp.data or [])} outstanding payments")
        
        rows = _attach_expense_names(resp.data or [])

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
                expense_name=row.get("expense_name"),
            )
            for row in rows
        ]
    except HTTPException:
        raise
    except Exception as e:
        print(f"Exception in get_outstanding_payments: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching outstanding payments: {str(e)}"
        )


@router.get("", response_model=List[Payment])
def get_all_payments(user_id: str = Depends(get_current_user_id)):
    """
    Fetch ALL payments involving this user (requested + paid).
    Mainly for debugging / future use.
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

    rows = _attach_expense_names(resp.data or [])

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
            expense_name=row.get("expense_name"),
        )
        for row in rows
    ]


@router.post("/{payment_id}/pay", response_model=MarkPaidResponse)
def mark_payment_as_paid(
    payment_id: str,
    body: MarkPaidRequest,
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

    if row["to_user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot pay for someone else's payment.",
        )

    if row["status"] != "requested":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment is not in a payable state.",
        )

    now_iso = datetime.now(timezone.utc).isoformat()

    update_payload = {
        "status": "paid",
        "paid_at": now_iso,
    }
    if body.paid_via:
        update_payload["paid_via"] = body.paid_via

    print(f"Updating payment {payment_id} with payload: {update_payload}")

    update_resp = (
        supabase.table("payments")
        .update(update_payload)
        .eq("id", payment_id)
        .execute()
    )

    if hasattr(update_resp, "error") and update_resp.error:
        print(f"Update error: {update_resp.error}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error updating payment: {update_resp.error.message}",
        )

    print(f"Payment {payment_id} updated successfully. Updated data: {update_resp.data}")

    # Fetch the updated payment
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

    updated = _attach_expense_names([fetch_resp.data])[0]

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
        expense_name=updated.get("expense_name"),
    )

    return MarkPaidResponse(success=True, payment=payment)
