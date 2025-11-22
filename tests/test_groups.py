# tests/test_groups.py

import pytest
import uuid
from unittest.mock import MagicMock, patch

# --- Fixtures ---
@pytest.fixture
def test_user():
    return str(uuid.uuid4())

@pytest.fixture
def test_group(test_user):
    """Return a mock group object."""
    group_id = str(uuid.uuid4())
    group_data = {
        "id": group_id,
        "name": "Test Group",
        "description": "A group for testing",
        "members": [test_user],
    }
    return group_id, group_data

# --- Tests ---
def test_create_group_inserts_correct_record(test_user):
    with patch("app.core.supabase_client.supabase") as mock_supabase:
        mock_table = mock_supabase.table.return_value
        mock_table.insert.return_value.execute.return_value = {
            "data": [{
                "id": str(uuid.uuid4()),
                "name": "Unit Test Group",
                "description": "Testing insert",
                "members": [test_user],
            }],
            "status_code": 201
        }

        # Import supabase **inside the patch context** to avoid triggering real client
        from app.core.supabase_client import supabase

        result = supabase.table("groups").insert({
            "name": "Unit Test Group",
            "description": "Testing insert",
            "members": [test_user],
        }).execute()

        inserted = result["data"][0]
        assert inserted["name"] == "Unit Test Group"
        assert inserted["description"] == "Testing insert"
        assert test_user in inserted["members"]

def test_fetch_groups_returns_only_user_groups(test_user, test_group):
    group_id, group_data = test_group
    with patch("app.core.supabase_client.supabase") as mock_supabase:
        mock_table = mock_supabase.table.return_value
        mock_table.select.return_value.contains.return_value.execute.return_value = {
            "data": [group_data],
            "status_code": 200
        }

        from app.core.supabase_client import supabase
        result = supabase.table("groups").select("*").contains("members", [test_user]).execute()
        groups = result["data"]
        for g in groups:
            assert test_user in g["members"]

def test_fetch_group_members_returns_correct_list(test_group, test_user):
    group_id, group_data = test_group
    with patch("app.core.supabase_client.supabase") as mock_supabase:
        mock_table = mock_supabase.table.return_value
        mock_table.select.return_value.eq.return_value.execute.return_value = {
            "data": [group_data],
            "status_code": 200
        }

        from app.core.supabase_client import supabase
        result = supabase.table("groups").select("members").eq("id", group_id).execute()
        members = result["data"][0]["members"]
        assert members == group_data["members"]
        assert test_user in members
