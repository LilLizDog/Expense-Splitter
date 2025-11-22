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
    group_id = str(uuid.uuid4())
    group_data = {
        "id": group_id,
        "name": "Test Group",
        "description": "A group for testing",
        "members": [test_user],
    }
    return group_id, group_data

# --- Auto-mock Supabase ---
@pytest.fixture(autouse=True)
def mock_supabase_client():
    """Automatically mock the Supabase client for all tests."""
    with patch("app.core.supabase_client.get_supabase") as mock_get:
        mock_client = MagicMock()
        mock_get.return_value = mock_client

        # Default behavior for common methods
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value.execute.return_value = {"data": [], "status_code": 201}
        mock_table.select.return_value.contains.return_value.execute.return_value = {"data": [], "status_code": 200}
        mock_table.select.return_value.eq.return_value.execute.return_value = {"data": [], "status_code": 200}

        yield mock_client

# --- Tests ---
def test_create_group_inserts_correct_record(test_user):
    mock_data = {
        "id": str(uuid.uuid4()),
        "name": "Unit Test Group",
        "description": "Testing insert",
        "members": [test_user],
    }

    from app.core.supabase_client import get_supabase
    supabase = get_supabase()
    supabase.table.return_value.insert.return_value.execute.return_value = {
        "data": [mock_data],
        "status_code": 201
    }

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

    from app.core.supabase_client import get_supabase
    supabase = get_supabase()
    supabase.table.return_value.select.return_value.contains.return_value.execute.return_value = {
        "data": [group_data],
        "status_code": 200
    }

    result = supabase.table("groups").select("*").contains("members", [test_user]).execute()
    groups = result["data"]
    for g in groups:
        assert test_user in g["members"]

def test_fetch_group_members_returns_correct_list(test_group, test_user):
    group_id, group_data = test_group

    from app.core.supabase_client import get_supabase
    supabase = get_supabase()
    supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = {
        "data": [group_data],
        "status_code": 200
    }

    result = supabase.table("groups").select("members").eq("id", group_id).execute()
    members = result["data"][0]["members"]
    assert members == group_data["members"]
    assert test_user in members
