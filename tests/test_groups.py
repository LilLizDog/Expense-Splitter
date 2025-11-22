# tests/conftest.py
import pytest

class ExecResultMock:
    def __init__(self, data=None, error=None, status_code=200):
        self.data = data
        self.error = error
        self.status_code = status_code

class TableMock:
    def __init__(self, data=None):
        # data should be a list (for select) or whatever you want execute() to return
        self._data = data or []
        self._last_insert = None

    # chainable methods
    def select(self, *args, **kwargs):
        return self
    def insert(self, insert_data):
        self._last_insert = insert_data
        return self
    def contains(self, *args, **kwargs):
        return self
    def order(self, *args, **kwargs):
        return self
    def eq(self, *args, **kwargs):
        return self
    def single(self):
        return self
    def in_(self, *args, **kwargs):
        return self

    def execute(self):
        # If an insert occurred, pretend insert returns the new row
        if self._last_insert is not None:
            return ExecResultMock(data=[{**self._last_insert, "id": "new-id"}], error=None)
        return ExecResultMock(data=self._data, error=None)

class SupabaseMock:
    def __init__(self, initial=None):
        initial = initial or {}
        self._initial = initial

    def table(self, name):
        data = self._initial.get(name, [])
        return TableMock(data=list(data))

@pytest.fixture(autouse=True)
def mock_supabase(monkeypatch):
    initial = {
        "groups": [
            {"id": "xyz", "members": ["uuid-123"], "created_at": "2025-11-01"}
        ],
        "users": [
            {"id": "uuid-123", "name": "Liz", "email": "liz@example.com"}
        ],
    }
    mock = SupabaseMock(initial)
    # patch the supabase objects used by the app (both routers and main)
    monkeypatch.setattr("app.routers.groups.supabase", mock)
    monkeypatch.setattr("app.main.supabase", mock)
    yield