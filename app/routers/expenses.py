# FILE: app/routers/expenses.py
# This file has the test routes for "expenses".
# Nothing connects to the database yet — just basic setup for now.

from fastapi import APIRouter  # lets us make small route sections
from pydantic import BaseModel, Field #lets us define and validate input shapes
from datetime import date  # lets us store just the data (no time)

# ALL ROUTES IN THIS FILE WILL START WITH /expenses
router = APIRouter(
    prefix="/expenses",
    tags=["expenses"]  # this will show as "expenses" in the docs
)

# ----------------------------
# MODEL - STRUCTURE FOR EXPENSE DATA
# ----------------------------
class ExpenseCreate(BaseModel):
    group_id: int = Field(..., description = "which group this expense belongs to")
    payer: str = Field(..., min_length =1, description = "name of the person who paid")
    amount: float = Field(..., gt = 0, description = "how much was paid (must be >0)")
    description: str | None = Field(None, description = "short note about the expense")
    expense_date: date = Field(default_factory=date.today, description = "the date when the expense was made") # This would assign today's date as default if none is provided
    
    
    #Note: For now, I kept these fields simple, we can add more fields later (like currency or split type)

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
@router.post("/", summary="Create expense (accepts JSON)")
def create_expense(payload: ExpenseCreate):
    """
    When someone sends JSON to /expenses, FastAPI checks if it matches
    the ExpenseCreate model above. If it's valid, this function runs.
    For now, it just returns the same data back.
    TODO: Later, insert this data into supabase and return the saved record.
    """
    data = payload.model_dump() #turn the model into a simple dict
    
    return {
        "ok": True,
        "resource": "expenses",
        "message": "created (test only)",
        "data": data
    }
