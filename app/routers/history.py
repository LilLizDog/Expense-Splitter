# FILE: app/routers/history.py
# This file manages all backend API routes related to the History page
# Uses mock data for received payments and paid expenses
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List

# This creates a router for the "History" feature.
router = APIRouter(prefix="/api/history", tags=["History"])

# ----- mock data for now -----
# For now, we use static lists to simulate received payments and paid expenses.
RECEIVED_PAYMENTS = [
    {"id": 1, "from": "Olivia Hageman", "amount": 25.00, "group": "Roommates"},
    {"id": 2, "from": "Preet Kaur", "amount": 12.50, "group": "Debugging Divas"},
    {"id": 3, "from": "Elizabeth Dreste", "amount": 40.00, "group": "CS Study Group"},
]

PAID_EXPENSES = [
    {"id": 10, "to": "Apartment Utilities", "amount": 60.00, "group": "Roommates"},
    {"id": 11, "to": "Brunch Split", "amount": 18.75, "group": "Debugging Divas"},
    {"id": 12, "to": "Competition Fees", "amount": 30.00, "group": "Dance Crew"},
]

# GET /api/history/
# Lists history of received payments and paid expenses, with optional filtering by group or person.

@router.get("/")
def get_history(
    group: Optional[str] = Query(None),
    person: Optional[str] = Query(None),
    # later: current_user: str = Depends(...)
):
    # In a real app, we would verify current_user here
    # for demo purposes we won't block, but here's how it would look:
    # if not current_user:
    #     raise HTTPException(status_code=401, detail="Not authorized")

    # Start with full lists
    received = RECEIVED_PAYMENTS
    paid = PAID_EXPENSES

    # Filter by name of group if provided
    if group:
        group_lower = group.lower()
        received = [r for r in received if group_lower in r["group"].lower()]
        paid = [p for p in paid if group_lower in p["group"].lower()]

    # Filter by name of person if provided
    if person:
        person_lower = person.lower()
        # for received, we match on "from"
        received = [r for r in received if person_lower in r["from"].lower()]
        # for paid, we match on "to"
        paid = [p for p in paid if person_lower in p["to"].lower()]

    # Return the filtered lists
    return {"received": received, "paid": paid}

# GET /api/history/groups
# Lists unique groups from both received payments and paid expenses for filtering purposes.
@router.get("/groups")
def get_history_groups():
    # union of groups from both lists
    groups = {r["group"] for r in RECEIVED_PAYMENTS} | {p["group"] for p in PAID_EXPENSES}
    return {"groups": sorted(groups)}
