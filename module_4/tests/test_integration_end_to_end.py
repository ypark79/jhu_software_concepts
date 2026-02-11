# These series of tests check that the end-to-end flow of the Flask 
# webpage works as expected. They check that the pull data button inserts
# rows into the database, the update analysis button updates the analysis
# page, and the second pull with overlapping data does not duplicate rows. 
# 1) Pull data (inserts rows)
# 2) Update analysis (should succeed when not busy)
# 3) Render analysis page
# 4) Second pull with overlapping data (should not duplicate)
import os
import pytest
import psycopg
import re
from app import create_app
from Scraper.clean import insert_rows_into_postgres

# Mark this test properly for pytest.ini. 
@pytest.mark.integration

# This test checks that the end-to-end flow of the Flask webpage works as expected.
def test_end_to_end_pull_update_render(monkeypatch):
    # Use test database to avoid touching real database. 
    monkeypatch.setenv("PGDATABASE", "module_4_db_test")
    monkeypatch.setenv("PGUSER", os.getenv("PGUSER", "postgres"))
    monkeypatch.setenv("PGPASSWORD", os.getenv("PGPASSWORD", "postgres"))
    monkeypatch.setenv("PGHOST", "localhost")
    monkeypatch.setenv("PGPORT", "5432")

    # Create app object and fake browser. 
    app = create_app()
    client = app.test_client()

    # Connect to test db (module_4_db_test) and create test table 
    # (applicants)
    conn = psycopg.connect(
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres"),
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5432")),
    )

    with conn.cursor() as cur:
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
        cur.execute("TRUNCATE TABLE applicants;")
    conn.commit()

    # Create 2x Fake rows for pull-data with fake result_ids. 
    fake_rows = [
        {
            "result_id": 2001,
            "program": "Computer Science, Johns Hopkins University",
            "comments": "Test row 1",
            "date_added": "January 01, 2026",
            "url": "https://www.thegradcafe.com/result/2001",
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
        },
        {
            "result_id": 2002,
            "program": "Computer Science, MIT",
            "comments": "Test row 2",
            "date_added": "January 02, 2026",
            "url": "https://www.thegradcafe.com/result/2002",
            "status": "Accepted",
            "term": "Fall 2026",
            "US/International": "International",
            "GPA": 3.8,
            "GRE Score": 325,
            "GRE V Score": 162,
            "GRE AW": 4.0,
            "Degree": "PhD",
            "llm-generated-program": "Computer Science",
            "llm-generated-university": "MIT",
        }
    ]

    # Fake subprocess to insert our rows instead of scraping
    def fake_popen(*args, **kwargs):
        insert_rows_into_postgres(fake_rows, table_name="applicants")
        class Dummy:
            def poll(self): return 0
        return Dummy()

    monkeypatch.setattr("app.subprocess.Popen", fake_popen)

    #Pull data (inserts rows into db)
    response = client.post("/pull-data")
    assert response.status_code == 200

    # Check rows exist in DB
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM applicants;")
        count = cur.fetchone()[0]
    assert count == 2

    # Update analysis (should succeed when not busy)
    response = client.post("/update-analysis")
    assert response.status_code == 200

    # Render analysis page
    response = client.get("/analysis")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Find all percent values in the html. 
    percents = re.findall(r"\b\d+(?:\.\d+)?%\b", html)

    # All percentage values must have exactly two decimals. 
    for p in percents:
        assert re.fullmatch(r"\d+\.\d{2}%", p)

    # Verify all answer blocks contain "Answer:" label. 
    assert html.count("Answer:") >= 11

    # Execute a re-pull and verify that the total count of data rows has
    # not changed. This indicates that there are no duplicate rows. 
    response = client.post("/pull-data")
    assert response.status_code == 200

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM applicants;")
        count_after_second = cur.fetchone()[0]
    assert count_after_second == 2

    conn.close()