import json
import pytest
import Scraper.clean as clean
import runpy


# Test the chunked function to ensure it splits a list into groups 
# of a given size.
@pytest.mark.analysis
def test_chunked_splits_list():
    # chunked should split a list into groups of a given size
    data = [1, 2, 3, 4, 5]
    chunks = list(clean.chunked(data, 2))
    assert chunks == [[1, 2], [3, 4], [5]]


# Test the clean_whitespace function to ensure it removes unnecessary 
# whitespace and standardizes spacing.
@pytest.mark.analysis
def test_clean_whitespace():
    # None should stay None
    assert clean.clean_whitespace(None) is None

    # Extra spaces should collapse to single spaces and strip ends
    assert clean.clean_whitespace("  hello   world  ") == "hello world"


# Test the clean_program_cell function to ensure it removes extra info 
# after "Accepted" and normalizes spacing.
@pytest.mark.analysis
def test_clean_program_cell():
    # Should remove extra info after "Accepted" and normalize spacing
    raw = "Computer Science Accepted Fall 2026"
    assert clean.clean_program_cell(raw) == "Computer Science"

# Test clean_program_cell with None input
@pytest.mark.analysis
def test_clean_program_cell_none():
    # None should stay None
    assert clean.clean_program_cell(None) is None


# Test normalize_zero with None input
@pytest.mark.analysis
def test_normalize_zero_none():
    # None should stay None
    assert clean.normalize_zero(None) is None

# Test the normalize_zero function to ensure it converts "0" and its variants 
# to None.
@pytest.mark.analysis
def test_normalize_zero():
    # "0" and its variants should become None
    assert clean.normalize_zero("0") is None
    assert clean.normalize_zero("0.0") is None
    assert clean.normalize_zero("0.00") is None

    # Non-zero stays the same
    assert clean.normalize_zero("3.5") == "3.5"


# Test the text_extractors_from_sample_text function to ensure it extracts 
# the correct fields from the sample text.
@pytest.mark.analysis
def test_text_extractors_from_sample_text():
    # This sample text includes all the fields we want to extract
    sample = (
        "Decision Accepted Notification on 01/02/2024 "
        "Notes Loved the program Timeline other text "
        "Degree Type PhD Degree's Country of Origin Domestic "
        "Undergrad GPA 3.80 GRE General: 330 GRE Verbal: 165 "
        "Analytical Writing: 5.0 Fall 2026"
    )

    assert clean.extract_decision(sample) == "Accepted"
    assert clean.extract_notification_date(sample) == "01/02/2024"
    assert clean.extract_notes(sample) == "Loved the program"
    assert clean.extract_degree_type(sample) == "PhD"
    assert clean.extract_country_origin(sample) == "Domestic"
    assert clean.extract_undergrad_gpa(sample) == "3.80"
    assert clean.extract_gre_general(sample) == "330"
    assert clean.extract_gre_verbal(sample) == "165"
    assert clean.extract_gre_aw(sample) == "5.0"
    assert clean.extract_term_year(sample) == "Fall 2026"


# Test extract_term_year normalizes "Autumn" to "Fall"
@pytest.mark.analysis
def test_extract_term_year_autumn_normalized():
    text = "Autumn 2026"
    assert clean.extract_term_year(text) == "Fall 2026"


# Test the text_extractors_none_inputs function to ensure it returns None 
# if the input is None.
@pytest.mark.analysis
def test_text_extractors_none_inputs():
    # All extraction helpers should return None if input is None
    assert clean.extract_notes(None) is None
    assert clean.extract_decision(None) is None
    assert clean.extract_notification_date(None) is None
    assert clean.extract_degree_type(None) is None
    assert clean.extract_country_origin(None) is None
    assert clean.extract_undergrad_gpa(None) is None
    assert clean.extract_gre_general(None) is None
    assert clean.extract_gre_verbal(None) is None
    assert clean.extract_gre_aw(None) is None
    assert clean.extract_term_year(None) is None


# Test text_extractors_no_match with text that has no matching fields.
@pytest.mark.analysis
def test_text_extractors_no_match():
    text = "This text has no matching fields."

    assert clean.extract_notes(text) is None
    assert clean.extract_decision(text) is None
    assert clean.extract_notification_date(text) is None
    assert clean.extract_degree_type(text) is None
    assert clean.extract_country_origin(text) is None
    assert clean.extract_undergrad_gpa(text) is None
    assert clean.extract_gre_general(text) is None
    assert clean.extract_gre_verbal(text) is None
    assert clean.extract_gre_aw(text) is None
    assert clean.extract_term_year(text) is None


# Test the load_data_file_not_found function to ensure it returns an 
# empty list if the file does not exist.
@pytest.mark.analysis
def test_load_data_file_not_found(tmp_path):
    # If file doesn't exist, load_data should return []
    missing_path = tmp_path / "missing.json"
    assert clean.load_data(str(missing_path)) == []


# Test the save_and_load_data_roundtrip function to ensure it saves and loads 
# data correctly.
@pytest.mark.analysis
def test_save_and_load_data_roundtrip(tmp_path):
    # save_data should write JSON that load_data can read back
    data = [{"a": 1}, {"b": 2}]
    path = tmp_path / "data.json"

    clean.save_data(data, str(path))
    loaded = clean.load_data(str(path))

    assert loaded == data


# Test load_data when JSON is malformed
@pytest.mark.analysis
def test_load_data_bad_json_returns_empty(tmp_path):
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{not valid json}", encoding="utf-8")

    # Should return [] on JSON parsing error
    assert clean.load_data(str(bad_path)) == []


# Test the llm_post_rows_success function to ensure it returns the correct 
# data from the LLM.
@pytest.mark.analysis
def test_llm_post_rows_success(monkeypatch):
    # Fake HTTP response object with a .read() method
    class FakeResponse:
        def read(self):
            return json.dumps({
                "rows": [{"llm-generated-program": "CS",
                          "llm-generated-university": "Uni"}]
            }).encode("utf-8")

    # Fake urlopen to return our FakeResponse
    def fake_urlopen(req, timeout=300):
        return FakeResponse()

    # Replace urlopen and time.sleep so no real network or delays
    monkeypatch.setattr(clean, "urlopen", fake_urlopen)
    monkeypatch.setattr(clean.time, "sleep", lambda x: None)

    rows = [{"program": "CS, Uni"}]
    out = clean._llm_post_rows("http://fake-llm", rows)

    assert out[0]["llm-generated-program"] == "CS"
    assert out[0]["llm-generated-university"] == "Uni"


# Test the llm_post_rows_missing_rows_raises function to ensure it raises 
# a RuntimeError if the LLM response does not include "rows".
@pytest.mark.analysis
def test_llm_post_rows_missing_rows_raises(monkeypatch):
    # Fake response that does NOT include "rows"
    class FakeResponse:
        def read(self):
            return json.dumps({"error": "missing rows"}).encode("utf-8")

    def fake_urlopen(req, timeout=300):
        return FakeResponse()

    monkeypatch.setattr(clean, "urlopen", fake_urlopen)
    monkeypatch.setattr(clean.time, "sleep", lambda x: None)

    with pytest.raises(RuntimeError):
        clean._llm_post_rows("http://fake-llm", [{"program": "X"}])


# Test _llm_post_rows retry loop and final failure
@pytest.mark.analysis
def test_llm_post_rows_all_retries_fail(monkeypatch):
    # Always fail so retries happen
    def fake_urlopen(req, timeout=300):
        raise Exception("LLM down")

    monkeypatch.setattr(clean, "urlopen", fake_urlopen)
    monkeypatch.setattr(clean.time, "sleep", lambda x: None)

    # Should raise after retries are exhausted
    with pytest.raises(RuntimeError):
        clean._llm_post_rows("http://fake-llm", [{"program": "X"}])


# Test the clean_data_basic function to ensure it cleans the data correctly.
@pytest.mark.analysis
def test_clean_data_basic(monkeypatch):
    # Fake LLM response to avoid real HTTP call
    def fake_llm_post_rows(llm_url, rows_payload, timeout_s=300):
        # Return one cleaned row for each input row
        return [{
            "llm-generated-program": "CS",
            "llm-generated-university": "Uni"
        } for _ in rows_payload]

    monkeypatch.setattr(clean, "_llm_post_rows", fake_llm_post_rows)

    # One raw row to clean
    raw_rows = [{
        "result_id": 123,
        "university_raw": "University A",
        "program_raw": "Computer Science Accepted",
        "date_added_raw": "January 31, 2026",
        "status_raw": "Accepted",
        "comments_raw": "  Great offer   ",
        "application_url_raw": "https://www.thegradcafe.com/result/123",
        "result_text_raw": (
            "Decision Accepted Notification on 01/02/2024 "
            "Notes Loved the program Timeline other text "
            "Degree Type PhD Degree's Country of Origin Domestic "
            "Undergrad GPA 3.80 GRE General: 330 GRE Verbal: 165 "
            "Analytical Writing: 5.0 Fall 2026"
        ),
        "term_inferred": "Fall 2026"
    }]

    extracted, final_rows, final_rows_no_llm = clean.clean_data(raw_rows)

    # Final rows should have cleaned program + university
    assert final_rows[0]["program"] == "CS, Uni"

    # Check key fields were extracted
    assert final_rows[0]["status"] == "Accepted on 01/02/2024"
    assert final_rows[0]["term"] == "Fall 2026"
    assert final_rows[0]["US/International"] == "American"
    assert final_rows[0]["GPA"] == "3.80"
    assert final_rows[0]["GRE Score"] == "330"
    assert final_rows[0]["GRE V Score"] == "165"
    assert final_rows[0]["GRE AW"] == "5.0"

    # The "no LLM" output should not include LLM fields
    assert "llm-generated-program" not in final_rows_no_llm[0]
    assert "llm-generated-university" not in final_rows_no_llm[0]


# Test clean_data when decision is missing and term comes from extract_term_year
@pytest.mark.analysis
def test_clean_data_missing_decision_and_term_fallback(monkeypatch):
    # Fake LLM response
    def fake_llm_post_rows(llm_url, rows_payload, timeout_s=300):
        return [{
            "llm-generated-program": "CS",
            "llm-generated-university": "Uni"
        } for _ in rows_payload]

    monkeypatch.setattr(clean, "_llm_post_rows", fake_llm_post_rows)

    raw_rows = [{
        "result_id": 456,
        "university_raw": "University B",
        "program_raw": "Biology",
        "date_added_raw": "January 31, 2026",
        "status_raw": None,
        "comments_raw": None,
        "application_url_raw": "https://www.thegradcafe.com/result/456",
        "result_text_raw": (
            # No "Decision" here, but term is present
            "Notes Some note Timeline other text Fall 2027"
        ),
        "term_inferred": None
    }]

    _, final_rows, _ = clean.clean_data(raw_rows)

    # Decision missing → Applicant Status should be None
    assert final_rows[0]["status"] is None

    # term should fall back to extract_term_year
    assert final_rows[0]["term"] == "Fall 2027"

# Test internal parsing helpers for invalid inputs
@pytest.mark.analysis
def test_parse_date_and_to_float_invalid():
    # Invalid date should return None
    assert clean._parse_date("Not a real date") is None

    # Invalid float should return None
    assert clean._to_float("not-a-number") is None


# Test the append_rows_to_master function to ensure it appends the new rows 
# to the master file correctly.
@pytest.mark.analysis
def test_append_rows_to_master(tmp_path):
    # Start with master file that already has result_id=1
    master_path = tmp_path / "master.json"
    initial = [{"result_id": 1, "program": "X"}]
    with open(master_path, "w", encoding="utf-8") as f:
        json.dump(initial, f)

    # New rows include a duplicate (1) and a new (2)
    new_rows = [{"result_id": 1, "program": "X"},
                {"result_id": 2, "program": "Y"}]

    added = clean.append_rows_to_master(new_rows, str(master_path))

    # Only the new row should be returned
    assert added == [{"result_id": 2, "program": "Y"}]

    # Master file should now have result_id=2 at the top
    with open(master_path, "r", encoding="utf-8") as f:
        saved = json.load(f)
    assert saved[0]["result_id"] == 2


# Test append_rows_to_master skips rows without result_id
@pytest.mark.analysis
def test_append_rows_to_master_skips_none_id(tmp_path):
    master_path = tmp_path / "master.json"
    with open(master_path, "w", encoding="utf-8") as f:
        json.dump([], f)

    new_rows = [{"result_id": None, "program": "X"}]
    added = clean.append_rows_to_master(new_rows, str(master_path))

    # No rows should be added
    assert added == []


# Test the insert_rows_into_postgres function to ensure it inserts the 
# new rows into the database correctly.
@pytest.mark.db
def test_insert_rows_into_postgres_empty_returns_zero():
    # If rows is empty, should return 0 and do nothing
    assert clean.insert_rows_into_postgres([]) == 0


# Test the insert_rows_into_postgres function to ensure it returns 0 if 
# the rows are empty.
@pytest.mark.db
def test_insert_rows_into_postgres_fake_connection(monkeypatch):
    # Fake cursor that pretends to execute SQL
    class FakeCursor:
        def __init__(self):
            self.rowcount = 1  # simulate "one row affected"

        def execute(self, sql, params):
            # We don't actually execute SQL, just pretend
            return None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    # Fake connection that returns FakeCursor
    class FakeConn:
        def cursor(self):
            return FakeCursor()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def close(self):
            return None

    # Use monkeypatch to replace psycopg.connect with the fake connection.
    monkeypatch.setattr(clean.psycopg, "connect", lambda **kwargs: FakeConn())

    rows = [{
        "result_id": 999,
        "program": "CS, Uni",
        "comments": "Nice",
        "date_added": "January 31, 2026",
        "url": "https://example.com",
        "status": "Accepted",
        "term": "Fall 2026",
        "US/International": "American",
        "GPA": "3.90",
        "GRE Score": "330",
        "GRE V Score": "165",
        "GRE AW": "5.0",
        "Degree": "PhD",
        "llm-generated-program": "CS",
        "llm-generated-university": "Uni"
    }]

    inserted = clean.insert_rows_into_postgres(rows)
    assert inserted == 1

# Test insert_rows_into_postgres skips rows without result_id
@pytest.mark.db
def test_insert_rows_into_postgres_skips_missing_id(monkeypatch):
    class FakeCursor:
        def __init__(self):
            self.rowcount = 1

        def execute(self, sql, params):
            return None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeConn:
        def cursor(self):
            return FakeCursor()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def close(self):
            return None

    monkeypatch.setattr(clean.psycopg, "connect", lambda **kwargs: FakeConn())

    # One row missing result_id should be skipped
    rows = [{
        "result_id": None,
        "program": "CS, Uni",
        "comments": "Nice",
        "date_added": "January 31, 2026",
        "url": "https://example.com",
        "status": "Accepted",
        "term": "Fall 2026",
        "US/International": "American",
        "GPA": "3.90",
        "GRE Score": "330",
        "GRE V Score": "165",
        "GRE AW": "5.0",
        "Degree": "PhD",
        "llm-generated-program": "CS",
        "llm-generated-university": "Uni"
    }]

    inserted = clean.insert_rows_into_postgres(rows)
    assert inserted == 0


@pytest.mark.analysis
# This test checks decision-only branch sets status without date.
def test_clean_data_decision_only(monkeypatch):
    
    def fake_llm_post_rows(llm_url, rows_payload, timeout_s=300):
        return [{"llm-generated-program": "CS", "llm-generated-university": "Uni"}]

    monkeypatch.setattr(clean, "_llm_post_rows", fake_llm_post_rows)

    raw_rows = [{
        "result_id": 1,
        "university_raw": "Uni",
        "program_raw": "CS",
        "date_added_raw": "January 31, 2026",
        "status_raw": None,
        "comments_raw": None,
        "application_url_raw": "url",
        "result_text_raw": "Decision Accepted Notification on ",
        "term_inferred": None
    }]

    extracted, final_rows, _ = clean.clean_data(raw_rows)
    # Final rows still should have status
    assert final_rows[0]["status"] == "Accepted"
    
    # These keys exist only in extracted_fields_raw
    assert extracted[0]["Accepted: Acceptance Date"] is None
    assert extracted[0]["Rejected: Rejection Date"] is None


@pytest.mark.analysis
# This test checks rejected branch sets rejection date.
def test_clean_data_rejected_branch(monkeypatch):
    
    def fake_llm_post_rows(llm_url, rows_payload, timeout_s=300):
        return [{"llm-generated-program": "CS", "llm-generated-university": "Uni"}]

    monkeypatch.setattr(clean, "_llm_post_rows", fake_llm_post_rows)

    raw_rows = [{
        "result_id": 2,
        "university_raw": "Uni",
        "program_raw": "CS",
        "date_added_raw": "January 31, 2026",
        "status_raw": None,
        "comments_raw": None,
        "application_url_raw": "url",
        "result_text_raw": "Decision Rejected Notification on 01/02/2024",
        "term_inferred": None
    }]

    extracted, final_rows, _ = clean.clean_data(raw_rows)

    # Final rows still should have status
    assert final_rows[0]["status"] == "Rejected on 01/02/2024"

    # This key is on extracted_fields_raw
    assert extracted[0]["Rejected: Rejection Date"] == "01/02/2024"


@pytest.mark.analysis
# This test checks program-only, uni-only, and neither cases.
def test_clean_data_combined_program_branches(monkeypatch):
    
    def fake_llm_post_rows(llm_url, rows_payload, timeout_s=300):
        return [
            {"llm-generated-program": "CS", "llm-generated-university": None},
            {"llm-generated-program": None, "llm-generated-university": "Uni"},
            {"llm-generated-program": None, "llm-generated-university": None},
        ]

    monkeypatch.setattr(clean, "_llm_post_rows", fake_llm_post_rows)

    raw_rows = [
        {"result_id": 1, "university_raw": "U1", "program_raw": "P1",
         "date_added_raw": "", "status_raw": "", "comments_raw": "",
         "application_url_raw": "", "result_text_raw": "", "term_inferred": None},
        {"result_id": 2, "university_raw": "U2", "program_raw": "P2",
         "date_added_raw": "", "status_raw": "", "comments_raw": "",
         "application_url_raw": "", "result_text_raw": "", "term_inferred": None},
        {"result_id": 3, "university_raw": "U3", "program_raw": "P3",
         "date_added_raw": "", "status_raw": "", "comments_raw": "",
         "application_url_raw": "", "result_text_raw": "", "term_inferred": None},
    ]

    _, final_rows, _ = clean.clean_data(raw_rows)

    assert final_rows[0]["program"] == "CS"
    assert final_rows[1]["program"] == "Uni"
    assert final_rows[2]["program"] is None


@pytest.mark.analysis
# This test checks empty/None inputs return None.
def test_parse_date_empty_and_to_float_none():
    
    assert clean._parse_date("") is None
    assert clean._to_float(None) is None


@pytest.mark.analysis
# This test checks main() runs without running the real process. 
def test_clean_main(monkeypatch):
    
    monkeypatch.setattr(clean, "load_data", lambda *a, **k: [])
    monkeypatch.setattr(clean, "clean_data", lambda *a, **k: ([], [], []))
    monkeypatch.setattr(clean, "append_rows_to_master", lambda *a, **k: [])
    monkeypatch.setattr(clean, "save_data", lambda *a, **k: None)
    monkeypatch.setattr(clean, "insert_rows_into_postgres", lambda *a, **k: 0)

    clean.main()


@pytest.mark.analysis
# This test checks the __main__ block runs safely.
def test_clean_main_block(tmp_path, monkeypatch):
    
    monkeypatch.chdir(tmp_path)
    runpy.run_module("Scraper.clean", run_name="__main__")