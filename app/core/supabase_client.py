import os
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Optional

# Load .env from the project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env"))

# Get environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TESTING = os.getenv("TESTING") == "1"

# Create Supabase client if possible; if not, or if TESTING, use an in memory fake client
if SUPABASE_URL and SUPABASE_KEY and not TESTING:
    # Real Supabase client for local dev and production
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    logging.warning(
        "Missing SUPABASE_URL or SUPABASE_KEY in .env or TESTING=1; "
        "using in memory fake supabase client."
    )

    # Lightweight in memory fake Supabase client used for tests or when real credentials
    # are not available. It implements the subset of the API used by the app routers:
    # supabase.table(...).select(...).eq(...).insert(...).update(...).limit(...).execute()
    from typing import Any, Dict, List
    import uuid

    class ExecResult:
        def __init__(self, data: Any):
            # Store returned data from fake query
            self.data = data

    class TableMock:
        def __init__(self, db: Dict[str, List[Dict[str, Any]]], name: str):
            # Keep reference to global in memory store and table name
            self._db = db
            self._name = name
            self._action = None
            self._payload = None
            self._filters = []
            self._limit = None
            self._select_cols = None

        def select(self, cols: str = "*"):
            # Mark this operation as a select with optional column list
            self._action = "select"
            self._select_cols = cols
            return self

        def eq(self, column: str, value: Any):
            # Add a simple equality filter for later execution
            self._filters.append((column, value))
            return self

        def insert(self, payload: Dict[str, Any]):
            # Mark this operation as an insert and store payload
            self._action = "insert"
            self._payload = payload
            return self

        def update(self, payload: Dict[str, Any]):
            # Mark this operation as an update and store payload
            self._action = "update"
            self._payload = payload
            return self

        def limit(self, n: int):
            # Apply a limit to the result set
            self._limit = n
            return self

        def execute(self):
            # Perform the queued action against the in memory table
            table = self._db.setdefault(self._name, [])

            if self._action == "select":
                rows = list(table)
                for col, val in self._filters:
                    rows = [r for r in rows if r.get(col) == val]
                if self._select_cols and self._select_cols != "*":
                    cols = [c.strip() for c in self._select_cols.split(",")]
                    rows = [{c: r.get(c) for c in cols if c in r} for r in rows]
                if self._limit is not None:
                    rows = rows[: self._limit]
                return ExecResult(rows)

            if self._action == "insert":
                row = dict(self._payload)
                if "id" not in row:
                    row["id"] = str(uuid.uuid4())
                table.append(row)
                return ExecResult([row])

            if self._action == "update":
                updated = []
                for r in table:
                    match = True
                    for col, val in self._filters:
                        if r.get(col) != val:
                            match = False
                            break
                    if match:
                        r.update(self._payload)
                        updated.append(r)
                return ExecResult(updated)

            # Default case returns empty result
            return ExecResult([])

    class FakeSupabase:
        def __init__(self):
            # Global in memory store keyed by table name
            self._db: Dict[str, List[Dict[str, Any]]] = {}

        def table(self, name: str) -> TableMock:
            # Create a TableMock bound to the given table name
            return TableMock(self._db, name)

    # Expose fake client as module level supabase object
    supabase = FakeSupabase()

def get_supabase():
    """
    Return the Supabase client used by the application.

    Tests patch this function to inject a mock client.
    """
    return supabase
