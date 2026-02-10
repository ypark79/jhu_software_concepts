# load_data.py has several "helper functions" that were used to ensure
# raw data was properly formatted and converted to the correct data types
# to facilitate data insertion into the SQL database. This test file will
# ensure those helper functions work as expected. 
import json
import pytest
from datetime import date
import load_data
import builtins

@pytest.mark.db
# Test the "infer term" helper function to ensure it returns the correct term
# based on the status and date added fields. These infer terms were written
# because the module 2 scraper failed to scrape the term field. 
def test_infer_term_from_status_date():
    # Status has date 01/15/2026 → should return Fall 2026
    result = load_data.infer_term("January 01, 2026", "Accepted on 01/15/2026")
    assert result == "Fall 2026"


@pytest.mark.db
def test_infer_term_from_date_added():
    # Date in October → should return next year Fall
    result = load_data.infer_term("October 15, 2025", None)
    assert result == "Fall 2026"


# Test the "parse date" helper function to ensure it returns the correct date
# object based on the date string. 
@pytest.mark.db
def test_parse_date_valid():
    d = load_data.parse_date("January 05, 2026")
    assert isinstance(d, date)
    assert d.year == 2026


@pytest.mark.db
def test_parse_date_invalid():
    assert load_data.parse_date("not a real date") is None
    assert load_data.parse_date("") is None


# Test the "try float" helper function to ensure it returns the correct float
# value based on the string value. 
@pytest.mark.db
def test_try_float():
    assert load_data.try_float("3.9") == 3.9
    assert load_data.try_float(None) is None
    assert load_data.try_float("abc") is None


# Test the "main" function to ensure it successfully inserts the data into
# the SQL database. 
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

    # Fake cursor to collect SQL calls and ensure the data is inserted
    # into the SQL database. 
    class FakeCursor:
        def __init__(self):
            self.executed = []

        def execute(self, sql, params=None):
            self.executed.append((sql, params))

        def __enter__(self): return self
        def __exit__(self, *args): pass

    # Fake connection object to test that main() executes the connection to the
    # the SQL database successfully. 
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

    # Use monkepatch to run the test connection. 
    fake_conn = FakeConn()
    monkeypatch.setattr(load_data, "get_connection", lambda: fake_conn)

    # Use monkey patch to open the test JSON file. 
    monkeypatch.setattr(load_data, "json_file", "fake.json")

    # Fake open() to return fake JSON to ensure the data is inserted
    # into the SQL database. 
    def fake_open(*args, **kwargs):
        return DummyFile(json.dumps(fake_json))

    # Create a test file object 
    class DummyFile:
        def __init__(self, text): self.text = text
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self): return self.text

    # Monkeypatch open() to return test file object to ensure the data is
    # inserted into the SQL database. 
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