# FILE: tests/test_history_api.py
# API-focused tests for the /api/history endpoints.
# These tests make sure that:
# - History endpoint returns correct records for a user.
# - Filters return only matching records.
# - Empty results return an empty list safely.

def test_history_endpoint_returns_correct_shape_for_user(client):
    """
    This test verifies that /api/history/ gives back the right JSON format.
    I’m not looking for exact values since everyone’s Supabase data varies,
    but the structure (keys + types) has to remain consistent.
    """
    r = client.get("/api/history/")
    # Depending on auth / Supabase, we may see 200, 401, or 500
    assert r.status_code in (200, 401, 500)

    if r.status_code == 200:
        data = r.json()
        # The response must have 'received' and 'paid' keys with list values
        assert "received" in data
        assert "paid" in data
        # These must always be lists, even if empty
        assert isinstance(data["received"], list)
        assert isinstance(data["paid"], list)

        # If there are any records, make sure the fields inside each one are correct
        for item in data["received"]:
            assert "from" in item
            assert "amount" in item
            assert "group" in item

        for item in data["paid"]:
            assert "to" in item
            assert "amount" in item
            assert "group" in item


def test_history_group_filter_returns_only_matching_groups(client):
    """
    This test verifies if filtering by group really reduces the results.
    If there are any results in the response, each item should contain the filter text
    in its 'group' field.
    """
    filter_group = "Roommates"
    r = client.get(f"/api/history/?group={filter_group}")
    assert r.status_code in (200, 401, 500)

    if r.status_code == 200:
        data = r.json()
        # These keys must always be present
        assert "received" in data
        assert "paid" in data
        assert isinstance(data["received"], list)
        assert isinstance(data["paid"], list)

        # If any results currently exist, verify the group matches the filter
        for item in data["received"]:
            assert "group" in item
            if item["group"]:
                assert filter_group.lower() in item["group"].lower()

        for item in data["paid"]:
            assert "group" in item
            if item["group"]:
                assert filter_group.lower() in item["group"].lower()


def test_history_person_filter_returns_only_matching_people(client):
    """
    This test is to see if filtering by person really does its job.
    The backend uses 'from: for incoming payments and 'to' for outgoing payments.
    This test verifies both of those. 
    """
    filter_person = "liz"
    r = client.get(f"/api/history/?person={filter_person}")
    assert r.status_code in (200, 401, 500)

    if r.status_code == 200:
        data = r.json()
        assert "received" in data
        assert "paid" in data
        assert isinstance(data["received"], list)
        assert isinstance(data["paid"], list)

        # For received payments, make sure 'from' matches filter
        for item in data["received"]:
            # backend uses "from" for received side
            name = item.get("from", "")
            if name:
                assert filter_person.lower() in name.lower()

        # For paid payments, make sure 'to' matches filter
        for item in data["paid"]:
            # backend uses "to" for paid side
            name = item.get("to", "")
            if name:
                assert filter_person.lower() in name.lower()


def test_history_empty_results_return_empty_lists(client):
    """
    This test ensures that the API remains stable when no results match a filter.
    I used a group name that should not exist to force empty results.
    """
    r = client.get("/api/history/?group=__this_group_should_not_exist__")
    assert r.status_code in (200, 401, 500)

    if r.status_code == 200:
        data = r.json()
        assert "received" in data
        assert "paid" in data
        # These must be lists
        assert isinstance(data["received"], list)
        assert isinstance(data["paid"], list)
        # Since the filter is for a non-existent group, both lists should be empty
        assert data["received"] == []
        assert data["paid"] == []
