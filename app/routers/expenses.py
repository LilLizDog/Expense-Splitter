# FILE: app/routers/expenses.py
# This file has the test routes for "expenses".
# Nothing connects to the database yet — just basic setup for now.

from fastapi import APIRouter  # lets us make small route sections

# ALL ROUTES IN THIS FILE WILL START WITH /expenses
router = APIRouter(
    prefix="/expenses",
    tags=["expenses"]  # this will show as "expenses" in the docs
)

# ----------------------------
# TEST ROUTE 1 – GET ALL EXPENSES
# ----------------------------
@router.get("/", summary="List expenses (test)")
def list_expenses():
    """
    WHEN SOMEONE VISITS /expenses → this function runs.
    RIGHT NOW, IT JUST SENDS BACK A SIMPLE JSON RESPONSE.
    LATER, WE WILL REPLACE THIS WITH REAL DATA FROM SUPABASE.
    """
    return {
        "ok": True,               # means the request worked fine
        "resource": "expenses",   # tells what type of data this is
        "data": []                # empty for now, will be filled later
    }


# ----------------------------
# TEST ROUTE 2 – GET ONE EXPENSE BY ID
# ----------------------------
@router.get("/{expense_id}", summary="Get one expense (test)")
def get_expense(expense_id: int):
    """
    WHEN SOMEONE VISITS /expenses/1 OR ANY NUMBER → THIS FUNCTION RUNS.
    RIGHT NOW, IT JUST SENDS BACK THE SAME ID TO CONFIRM ROUTING WORKS.
    """
    return {
        "ok": True,
        "resource": "expenses",
        "data": {"id": expense_id}  # shows which ID was sent
    }


# ----------------------------
# TEST ROUTE 3 – CREATE AN EXPENSE (POST)
# ----------------------------
@router.post("/", summary="Create expense (test)")
def create_expense():
    """
    WHEN SOMEONE SENDS A POST REQUEST TO /expenses → THIS RUNS.
    FOR NOW, IT DOESN’T SAVE ANYTHING — JUST RETURNS A TEST MESSAGE.
    TODO: LATER WE WILL ACCEPT JSON DATA AND ADD IT TO SUPABASE.
    """
    return {
        "ok": True,
        "resource": "expenses",
        "message": "created (test only)"
    }
