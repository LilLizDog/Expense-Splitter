import pytest
from supabase import create_client, Client
import uuid
import os

# --- Setup Supabase client ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Fixtures ---
@pytest.fixture
def test_user():
    """Create a test user ID"""
    return str(uuid.uuid4())

@pytest.fixture
def test_group(test_user):
    """Create a test group and clean up after"""
    group_data = {
        "name": "Test Group",
        "description": "A group for testing",
        "members": [test_user],
    }
    result = supabase.table("groups").insert(group_data).execute()
    group_id = result.data[0]["id"]
    yield group_id, group_data
    # Cleanup
    supabase.table("groups").delete().eq("id", group_id).execute()

# --- Tests ---

def test_create_group_inserts_correct_record(test_user):
    group_data = {
        "name": "Unit Test Group",
        "description": "Testing insert",
        "members": [test_user],
    }
    result = supabase.table("groups").insert(group_data).execute()
    
    assert result.status_code == 201 or result.status_code == 200
    inserted = result.data[0]
    assert inserted["name"] == group_data["name"]
    assert inserted["description"] == group_data["description"]
    assert test_user in inserted["members"]

    # Cleanup
    supabase.table("groups").delete().eq("id", inserted["id"]).execute()

def test_fetch_groups_returns_only_user_groups(test_user, test_group):
    group_id, group_data = test_group
    
    # Fetch all groups where user is a member
    result = supabase.table("groups").select("*").contains("members", [test_user]).execute()
    
    assert result.status_code == 200
    groups = result.data
    # All returned groups must include the test_user
    for g in groups:
        assert test_user in g["members"]

def test_fetch_group_members_returns_correct_list(test_group, test_user):
    group_id, group_data = test_group
    
    # Fetch members of the group
    result = supabase.table("groups").select("members").eq("id", group_id).execute()
    assert result.status_code == 200
    members = result.data[0]["members"]
    assert members == group_data["members"]
    assert test_user in members
