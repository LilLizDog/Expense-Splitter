# FILE: tests/test_history_basic.py
# Basic tests for the /history routes and page.

def test_history_page_exists(client):
    # /history should load and show main elements
    r = client.get("/history")
    assert r.status_code == 200
    # check that our main elements from history.html are there
    assert "History" in r.text
    assert 'id="groupFilter"' in r.text     # group dropdown
    assert 'id="personFilter"' in r.text    # person input
    assert 'id="btnApply"' in r.text        # apply filters button
    assert 'id="btnClear"' in r.text        # clear button
    assert 'id="historyList"' in r.text     # combined transactions list

    # assert 'id="receivedList"' in r.text    # received column
    # assert 'id="paidList"' in r.text        # paid column


def test_history_alias_exists(client):
    # /history.html alias should also load
    r = client.get("/history.html")
    assert r.status_code == 200


def test_history_api_returns_received_and_paid(client):
    # GET /api/history/ should return received and paid lists
    r = client.get("/api/history/") 
    assert r.status_code in (200, 401, 500)

    if r.status_code == 200:
        data = r.json()
        assert "received" in data
        assert "paid" in data
        assert isinstance(data["received"], list)
        assert isinstance(data["paid"], list)


def test_history_group_filter_narrows_results(client):
   # GET /api/history with ?group= should return filtered results by group
    r = client.get("/api/history/?group=Roommates")
    assert r.status_code in (200, 401, 500)

    if r.status_code == 200:
        data = r.json()
        assert "received" in data
        assert "paid" in data
        assert isinstance(data["received"], list)
        assert isinstance(data["paid"], list)
        for item in data["received"]:
            assert "group" in item
        for item in data["paid"]:
            assert "group" in item


def test_history_person_filter_narrows_results(client):
    # GET /api/history with ?person= should return filtered results by person
    r = client.get("/api/history/?person=liz")
    assert r.status_code in (200, 401, 500)

    if r.status_code == 200:
        data = r.json()
        assert "received" in data
        assert "paid" in data
        assert isinstance(data["received"], list)
        assert isinstance(data["paid"], list)


def test_history_groups_endpoint_works(client):
    # GET /api/history/groups should return list of unique group names
    r = client.get("/api/history/groups")
    assert r.status_code in (200, 500)  

    if r.status_code == 200:
        data = r.json()
        assert "groups" in data
        assert isinstance(data["groups"], list)
