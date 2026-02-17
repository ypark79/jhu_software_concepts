# load_data.py has helper functions used to ensure raw data is
# formatted correctly for SQL insertion. This test file ensures
# those helpers work as expected.
import json
import pytest
from datetime import date

import psycopg

import load_data
import builtins
import io
import runpy
import db_connection

@pytest.mark.db
# Test infer_term returns the correct term from status/date fields.
# These infer terms were written because module 2 did not scrape term.
def test_infer_term_from_status_date():
    # Status has date 01/15/2026 → should return Fall 2026
    result = load_data.infer_term("January 01, 2026", "Accepted on 01/15/2026")
    assert result == "Fall 2026"


@pytest.mark.db
def test_infer_term_from_date_added():
    # Date in October → should return next year Fall
    result = load_data.infer_term("October 15, 2025", None)
    assert result == "Fall 2026"


# Test parse_date returns the correct date object.
@pytest.mark.db
def test_parse_date_valid():
    d = load_data.parse_date("January 05, 2026")
    assert isinstance(d, date)
    assert d.year == 2026


@pytest.mark.db
def test_parse_date_invalid():
    assert load_data.parse_date("not a real date") is None
    assert load_data.parse_date("") is None


# Test try_float returns the correct float value.
@pytest.mark.db
def test_try_float():
    assert load_data.try_float("3.9") == 3.9
    assert load_data.try_float(None) is None
    assert load_data.try_float("abc") is None


# Test main inserts data into the SQL database.
@pytest.mark.db
def test_main_success(monkeypatch):
    # Fake JSON data with one row
    fake_json = [
        {
            "program": "Computer Science",
            "comments": "Test",
            "date_added": "January 01, 2026",
            "url": "http://example.com",
            "status": "Accepted on 01/15/2026",
            "term": None,
            "US/International": "American",
            "GPA": "3.8",
            "GRE Score": "330",
            "GRE V Score": "165",
            "GRE AW": "4.5",
            "Degree": "MS",
            "llm-generated-program": "Computer Science",
            "llm-generated-university": "MIT"
        }
    ]

    # Fake cursor to collect SQL calls and ensure insertion works.
    class FakeCursor:
        def __init__(self):
            self.executed = []

        def execute(self, sql, params=None):
            self.executed.append((sql, params))

        def __enter__(self): return self
        def __exit__(self, *args): pass

    # Fake connection object to test that main() executes the
    # SQL database connection successfully.
    class FakeConn:
        def __init__(self):
            self.cursor_obj = FakeCursor()
            self.committed = False
            self.rolled_back = False
            self.closed = False

        def cursor(self): return self.cursor_obj
        def commit(self): self.committed = True
        def rollback(self): self.rolled_back = True
        def close(self): self.closed = True

    # Use monkeypatch to run the test connection.
    fake_conn = FakeConn()
    monkeypatch.setattr(load_data, "get_connection", lambda: fake_conn)

    # Use monkeypatch to open the test JSON file.
    monkeypatch.setattr(load_data, "JSON_FILE", "fake.json")

    # Fake open() to return JSON and ensure the insert runs.
    def fake_open(*args, **kwargs):
        return DummyFile(json.dumps(fake_json))

    # Create a test file object
    class DummyFile:
        def __init__(self, text): self.text = text
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self): return self.text

    # Monkeypatch open() to return a test file object and
    # ensure the data is inserted into the SQL database.
    monkeypatch.setattr(builtins, "open", fake_open)

    # Run main()
    load_data.main()

    # Ensure commit happened and connection closed
    assert fake_conn.committed is True
    assert fake_conn.closed is True


# Test the "main" function to ensure it exits without error when the
# connection to the SQL database fails.
@pytest.mark.db
def test_main_connection_fail(monkeypatch):
    # Force get_connection to return None to ensure the function exits
    # without error.
    monkeypatch.setattr(load_data, "get_connection", lambda: None)

    # Run main() — should just exit without error
    load_data.main()


@pytest.mark.analysis
# This test checks infer_term uses the year in the status string.
def test_infer_term_from_status_year():

    assert (
        load_data.infer_term(
            "January 1, 2025",
            "Accepted on 01/15/2026"
        )
        == "Fall 2026"
    )


@pytest.mark.analysis
# This test checks month-based fallback logic.
def test_infer_term_fallback_months():

    assert load_data.infer_term("October 1, 2025", None) == "Fall 2026"
    assert load_data.infer_term("May 1, 2025", None) == "Fall 2025"


@pytest.mark.analysis
# This test checks invalid dates return None.
def test_infer_term_invalid_date():

    assert load_data.infer_term("bad date", None) is None


@pytest.mark.db
# This test checks main() rolls back and closes on DB error.
def test_load_data_main_rollback(monkeypatch):

    class FakeCursor:
        def execute(self, *args, **kwargs):
            raise psycopg.ProgrammingError("db error")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeConn:
        def __init__(self):
            self.rolled_back = False
            self.closed = False

        def cursor(self):
            return FakeCursor()

        def commit(self):
            pass

        def rollback(self):
            self.rolled_back = True

        def close(self):
            self.closed = True

    conn = FakeConn()
    monkeypatch.setattr(load_data, "get_connection", lambda: conn)

    load_data.main()
    assert conn.rolled_back is True
    assert conn.closed is True


@pytest.mark.analysis
# This test checks the __main__ block runs safely.
def test_load_data_main_block(monkeypatch):

    class FakeCursor:
        def execute(self, *args, **kwargs):
            return None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeConn:
        def cursor(self):
            return FakeCursor()

        def commit(self):
            pass

        def rollback(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(db_connection, "get_connection", lambda: FakeConn())
    monkeypatch.setattr(builtins, "open", lambda *a, **k: io.StringIO("[]"))

    runpy.run_module("load_data", run_name="__main__")
