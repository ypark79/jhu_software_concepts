# These tests cover database writes and idempotency.
# Inserts use a separate test database so we do NOT touch real data.

import getpass
import os
import pytest
import psycopg
from app import create_app
from Scraper.clean import insert_rows_into_postgres

# These are the required keys as outlined in the mod 3 assignment. 
# I also included "result_id" because this is the unique identifier
# for each applicant and critical to my code to ensure that 
# only new entries are scraped/cleaned from gradcafe and that
# there are no duplicates. 
EXPECTED_KEYS = {
    "p_id",
    "result_id",
    "program",
    "comments",
    "date_added",
    "url",
    "status",
    "term",
    "us_or_international",
    "gpa",
    "gre",
    "gre_v",
    "gre_aw",
    "degree",
    "llm_generated_program",
    "llm_generated_university",
}

# Fake rows that will be inserted
fake_rows = [
    {
        "result_id": 1001,
        "program": "Computer Science, Johns Hopkins University",
        "comments": "Test entry",
        "date_added": "January 01, 2026",
        "url": "https://www.thegradcafe.com/result/1001",
        "status": "Accepted",
        "term": "Fall 2026",
        "US/International": "American",
        "GPA": 3.9,
        "GRE Score": 330,
        "GRE V Score": 165,
        "GRE AW": 4.5,
        "Degree": "MS",
        "llm-generated-program": "Computer Science",
        "llm-generated-university": "Johns Hopkins University",
    }
]


# Mark this test for database schema/inserts/selects.
@pytest.mark.db
# Test the database inserts/writes and idempotency.
def test_insert_on_pull_and_idempotency(monkeypatch):
    # Set environment variables for the test DB.
    # This prevents touching the real database.
    # Use current OS user as default (macOS often has no "postgres" role).
    default_user = os.getenv("PGUSER", getpass.getuser())
    monkeypatch.setenv("PGDATABASE", "module_5_db_test")
    monkeypatch.setenv("PGUSER", default_user)
    monkeypatch.setenv("PGPASSWORD", os.getenv("PGPASSWORD", ""))
    monkeypatch.setenv("PGHOST", "localhost")
    monkeypatch.setenv("PGPORT", "5432")

    # Create the Flask app and test client.
    app = create_app()
    client = app.test_client()

    # Connect to the test database using the environment variables.
    conn = psycopg.connect(
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5432")),
    )

  
    with conn.cursor() as cur:
        # Create test table 
        cur.execute("""
            CREATE TABLE IF NOT EXISTS applicants (
                p_id SERIAL,
                result_id INTEGER PRIMARY KEY,
                program TEXT,
                comments TEXT,
                date_added DATE,
                url TEXT,
                status TEXT,
                term TEXT,
                us_or_international TEXT,
                gpa FLOAT,
                gre FLOAT,
                gre_v FLOAT,
                gre_aw FLOAT,
                degree TEXT,
                llm_generated_program TEXT,
                llm_generated_university TEXT
            );
        """)
        # Ensure the table is cleared before each test as per the 
        # assignment instructions. 
        cur.execute("TRUNCATE TABLE applicants;")
        conn.commit()


    # Mocks subprocess,Popen so /pull-data inserts fake row directly 
    # into test table
    def fake_popen(*args, **kwargs):
        insert_rows_into_postgres(fake_rows, table_name="applicants")
        class Dummy:
            def poll(self): return 0
        return Dummy()

    monkeypatch.setattr("app.subprocess.Popen", fake_popen)

    # First pull inserts rows
    response = client.post("/pull-data")
    assert response.status_code == 200, response.get_json()

    # Keeps count of rows in the test table after the first pull.
    
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM applicants;")
        count_after_first = cur.fetchone()[0]
    assert count_after_first == 1

    # Check that all required fields are non-null after the pull. 
    # Select one row of fake data. 
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                result_id, program, comments, date_added, url, status,
                term, us_or_international, gpa, gre, gre_v, gre_aw,
                degree, llm_generated_program, llm_generated_university
            FROM applicants
            LIMIT 1;
        """)
        row = cur.fetchone()

    # Check to ensure none of the fields are NULL
    assert all(value is not None for value in row)

    # Second pull inserts the same fake row again and checks the count
    # to still be 1, which means it was not duplicated.
    # Confirms idempotency.
    response = client.post("/pull-data")
    assert response.status_code == 200, response.get_json()


    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM applicants;")
        count_after_second = cur.fetchone()[0]
    assert count_after_second == 1

    conn.close()

@pytest.mark.db
# Test that the query returns the expected keys.
def test_query_returns_expected_keys(monkeypatch):
    # Use test DB env vars; default to current OS user on macOS.
    default_user = os.getenv("PGUSER", getpass.getuser())
    monkeypatch.setenv("PGDATABASE", "module_5_db_test")
    monkeypatch.setenv("PGUSER", default_user)
    monkeypatch.setenv("PGPASSWORD", os.getenv("PGPASSWORD", ""))
    monkeypatch.setenv("PGHOST", "localhost")
    monkeypatch.setenv("PGPORT", "5432")

    # Connect to the test database
    conn = psycopg.connect(
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5432")),
    )

    with conn:
        with conn.cursor() as cur:
            # Create test table if it doesn't exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS applicants (
                    p_id SERIAL,
                    result_id INTEGER PRIMARY KEY,
                    program TEXT,
                    comments TEXT,
                    date_added DATE,
                    url TEXT,
                    status TEXT,
                    term TEXT,
                    us_or_international TEXT,
                    gpa FLOAT,
                    gre FLOAT,
                    gre_v FLOAT,
                    gre_aw FLOAT,
                    degree TEXT,
                    llm_generated_program TEXT,
                    llm_generated_university TEXT
                );
            """)
            # Clear table 
            cur.execute("TRUNCATE TABLE applicants;")
            conn.commit()
    conn.close()

    # Insert a row so the query has something to return
    def fake_popen(*args, **kwargs):
        insert_rows_into_postgres(fake_rows, table_name="applicants")
        class Dummy:
            def poll(self): return 0
        return Dummy()

    monkeypatch.setattr("app.subprocess.Popen", fake_popen)

    # Trigger insert via pull-data
    client = create_app().test_client()
    client.post("/pull-data")
    # This will call the helper in query_data.py to return
    # one row as a dict with the required keys.
    from query_data import get_sample_applicant_dict

    data = get_sample_applicant_dict(table_name="applicants")

    # Ensure the dict is returned as expected.
    assert isinstance(data, dict)

    # Ensure all required keys are present
    assert EXPECTED_KEYS.issubset(set(data.keys()))