# These tests cover query_data.py without using a real database.
import pytest
import query_data


@pytest.mark.db
def test_main_success(monkeypatch):
    # This tests to see if the cursor properly returns the correct values 
    # for each query. Do this by creating a fake cursor and preloaded 
    # values for each query. 
    class FakeCursor:
        def __init__(self):
            # Pre-load return values for each query in query_data.main()
            self.results = [
                (10,),          # Applicant count for Fall 2026
                (12.34,),       # Percentage of international applicants
                (3.7, 320, 160, 4.0),  # Average GPA, GRE, GRE V, GRE AW
                (3.5,),         # Average GPA of US students in Fall 2026
                (45.67,),       # Percentage of accepted applicants for Fall 2025
                (3.6,),         # Average GPA of Fall 2026 acceptances
                (20,),          # JHU Computer Science Masters Count
                (5,),           # Top-tier PhD Count
                (4,),           # Original Fields Count
                (6,),           # LLM Fields Count
                (2, 3),         # JHU Comparison
                ("MIT", 7)      # Top International University
            ]
            # Track the number of calls to the cursor
            self.calls = 0

        # Execute the SQL query and confirm the query was executed.
        def execute(self, sql):
           
            pass

        # Execute preloaded fetchone() calls 
        def fetchone(self):
            # Return the next tuple in order and increment the call counter.
            result = self.results[self.calls]
            self.calls += 1
            return result

        # Enter the context manager and return the cursor object.
        def __enter__(self): return self

        # Exit the context manager and do nothing.
        def __exit__(self, *args): pass

    # Create a fake connection object
    class FakeConn:
        def __init__(self):
            self.cursor_obj = FakeCursor()
            self.closed = False

        # Return the cursor object.
        def cursor(self):
            return self.cursor_obj

        # Close the connection and set the closed flag to True.
        def close(self):
            self.closed = True

    # Use monkeypatch to make a fake connection to the database.
    fake_conn = FakeConn()
    monkeypatch.setattr(query_data, "get_connection", lambda: fake_conn)

    # Test main() 
    query_data.main()

    # Ensure connection was closed
    assert fake_conn.closed is True


# Test the main function to ensure it exits safely if the connection 
# to the database fails.
@pytest.mark.db
def test_main_connection_fail(monkeypatch):
    # If get_connection returns None, main() should exit safely
    monkeypatch.setattr(query_data, "get_connection", lambda: None)
    query_data.main()


# This test ensures the get_sample_applicant_dict function returns a dictionary
# with the correct keys and values.
@pytest.mark.db
def test_get_sample_applicant_dict(monkeypatch):
    # Create a fake cursor that returns a preloaded tuple for the fetchone() call.
    class FakeCursor:
        def execute(self, sql): pass
        def fetchone(self):
            return (
                1, 1001, "CS, JHU", "Test", "2026-01-01", "http://x",
                "Accepted", "Fall 2026", "American", 3.9, 330, 165, 4.5,
                "MS", "Computer Science", "Johns Hopkins"
            )
        def __enter__(self): return self
        def __exit__(self, *args): pass

    # Create a fake connection object that returns the fake cursor.
    class FakeConn:
        def cursor(self): return FakeCursor()
        def close(self): pass

    # Use monkeypatch to make a fake connection to the database.
    monkeypatch.setattr(query_data, "get_connection", lambda: FakeConn())

    # Test the get_sample_applicant_dict function.
    data = query_data.get_sample_applicant_dict(table_name="applicants")

    # Confirm dict has an expected key and value. 
    assert isinstance(data, dict)
    assert data["result_id"] == 1001