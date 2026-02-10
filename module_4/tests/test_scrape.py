import pytest
from bs4 import BeautifulSoup
# Import the scrape module that exists inside the src/module_4 directory
# to test the functions within scrape.py. 
import Scraper.scrape as scrape


# This fixture simulates the GradCafe survey list page.
# It has:
# - One "main" row with 5 <td> cells and a link to /result page. 
# - One "detail" row with a single <td> that contains term info
SURVEY_PAGE_HTML = """
<table>
  <tr>
    <td>University A</td>
    <td>Computer Science</td>
    <td>January 31, 2026</td>
    <td>Accepted</td>
    <td>Great offer</td>
    <td><a href="/result/123">View</a></td>
  </tr>
  <tr>
    <td>Applied for Fall 2026, thanks!</td>
  </tr>
</table>
"""

# This fixture simulates the detail page for a specific result.
DETAIL_PAGE_HTML = """
<html>
  <body>
    <div>Full application details here.</div>
  </body>
</html>
"""

# This fixture has a row with no student application link.
# It should be skipped by scrape_data.
SURVEY_PAGE_NO_LINK_HTML = """
<table>
  <tr>
    <td>University B</td>
    <td>Biology</td>
    <td>February 1, 2026</td>
    <td>Rejected</td>
    <td>Ok</td>
  </tr>
</table>
"""


# Test the extract_result_id function to ensure it returns the correct 
# result ID from the URL.
@pytest.mark.analysis
def test_extract_result_id():
    # If URL is None, expect None
    assert scrape.extract_result_id(None) is None

    # If URL has /result/123, expect int 123
    assert scrape.extract_result_id("https://www.thegradcafe.com/result/123") == 123

    # If URL does not match pattern, expect None
    assert scrape.extract_result_id("https://example.com/nope") is None


# Test the parse_date_added function to ensure it returns the correct 
# date from the string.
@pytest.mark.analysis
def test_parse_date_added():
    # Valid date should parse
    dt = scrape.parse_date_added("January 31, 2026")
    assert dt is not None
    assert dt.year == 2026

    # Invalid date should return None
    assert scrape.parse_date_added("Not a date") is None

    # Empty string should return None
    assert scrape.parse_date_added("") is None


# Test the extract_term_from_text function to ensure it returns the correct 
# term from the string.
@pytest.mark.analysis
def test_extract_term_from_text():
    # "Autumn" should normalize to "Fall"
    assert scrape.extract_term_from_text("Autumn 2026") == "Fall 2026"

    # If no term in text, expect None
    assert scrape.extract_term_from_text("No term here") is None

    # If input is None, expect None
    assert scrape.extract_term_from_text(None) is None


# Test the infer_term_from_row function to ensure it returns the correct 
# term from the string.
@pytest.mark.analysis
def test_infer_term_from_row():
    # infer_term_from_row checks program/status/comments combined
    term = scrape.infer_term_from_row("Program", "Status", "Admit for Autumn 2027")
    assert term == "Fall 2027"

    # If no term anywhere, returns None
    assert scrape.infer_term_from_row("Program", "Status", "No term") is None


# Test the extract_term_from_detail_row function to ensure it returns the correct 
# term from the string.
@pytest.mark.analysis
def test_extract_term_from_detail_row():
    # Detail row should detect "Fall 2026"
    assert scrape.extract_term_from_detail_row("Applied for Fall 2026") == "Fall 2026"

    # Missing or empty detail text returns None
    assert scrape.extract_term_from_detail_row("") is None


# Test the extract_tr_rows_from_html function to ensure it returns the correct 
# rows from the HTML string.
@pytest.mark.analysis
def test_extract_tr_rows_from_html():
    # This should return only rows that actually have <td> cells
    rows = scrape._extract_tr_rows_from_html(SURVEY_PAGE_HTML)
    assert len(rows) == 2  # two <tr> tags with td content


# Test the row_dict_from_tr function to ensure it returns the correct 
# dictionary from the HTML string.
@pytest.mark.analysis
def test_row_dict_from_tr_parses_fields():
    # Build a BeautifulSoup row so we can test _row_dict_from_tr directly
    soup = BeautifulSoup(SURVEY_PAGE_HTML, "html.parser")
    tr = soup.find_all("tr")[0]

    row = scrape._row_dict_from_tr(tr)

    # result_id pulled from /result/123
    assert row["result_id"] == 123

    # Basic field checks
    assert row["university_raw"] == "University A"
    assert row["program_raw"] == "Computer Science"
    assert row["status_raw"] == "Accepted"
    assert row["comments_raw"] == "Great offer"

    # Full URL should be expanded
    assert row["application_url_raw"].startswith("https://")


# Test the scrape_data function to ensure it returns the correct 
# rows from the HTML string.
@pytest.mark.analysis
def test_scrape_data_happy_path(monkeypatch):
    # This fake function replaces download_html so we never hit the internet.
    def fake_download_html(url):
        # If scraping the page list, return the survey list fixture
        if "survey" in url:
            return SURVEY_PAGE_HTML

        # If scraping the detail page, return detail fixture
        if "result/123" in url:
            return DETAIL_PAGE_HTML

        # Default fallback (should not happen here)
        return ""

    # Avoid real sleeps during tests
    monkeypatch.setattr(scrape, "download_html", fake_download_html)
    monkeypatch.setattr(scrape.time, "sleep", lambda x: None)

    # Run scrape_data with no existing IDs
    rows, stop_now = scrape.scrape_data("https://www.thegradcafe.com/survey/", set())

    # We should get one row
    assert len(rows) == 1
    assert stop_now is False

    # The detail row should infer term from the "detail" tr
    assert rows[0]["term_inferred"] == "Fall 2026"

    # result_text_raw should be populated from DETAIL_PAGE_HTML
    assert rows[0]["result_text_raw"] is not None


# Test the scrape_data function to ensure it stops when it encounters an 
# existing result ID.
@pytest.mark.analysis
def test_scrape_data_stops_on_existing_id(monkeypatch):
    def fake_download_html(url):
        return SURVEY_PAGE_HTML

    monkeypatch.setattr(scrape, "download_html", fake_download_html)
    monkeypatch.setattr(scrape.time, "sleep", lambda x: None)

    # existing_ids already has 123, so scraper should stop immediately
    rows, stop_now = scrape.scrape_data("https://www.thegradcafe.com/survey/", {123})

    assert rows == []
    assert stop_now is True


# Test the scrape_data function to ensure it skips rows without a 
# student application link.
@pytest.mark.analysis
def test_scrape_data_skips_rows_without_link(monkeypatch):
    def fake_download_html(url):
        return SURVEY_PAGE_NO_LINK_HTML

    # Use monkeypatch to replace the download_html function with the 
    # fake function.
    monkeypatch.setattr(scrape, "download_html", fake_download_html)
    monkeypatch.setattr(scrape.time, "sleep", lambda x: None)

    # Run scrape_data with no existing IDs
    rows, stop_now = scrape.scrape_data("https://www.thegradcafe.com/survey/", set())

    # No link means no detail URL; row should be skipped
    assert rows == []
    assert stop_now is False


# Test the scrape_data function to ensure it sets result_text_raw to None 
# if the detail page fetch fails.
@pytest.mark.analysis
def test_scrape_data_detail_fetch_error_sets_none(monkeypatch):
    def fake_download_html(url):
        # The list page should load fine
        if "survey" in url:
            return SURVEY_PAGE_HTML

        # The detail page should fail (simulate error)
        if "result/123" in url:
            raise Exception("Simulated error")

        return ""

    # Use monkeypatch to replace the download_html function with the fake function.
    monkeypatch.setattr(scrape, "download_html", fake_download_html)
    monkeypatch.setattr(scrape.time, "sleep", lambda x: None)

    # Run scrape_data with no existing IDs
    rows, _ = scrape.scrape_data("https://www.thegradcafe.com/survey/", set())

    # One row should be returned
    assert len(rows) == 1
    # If detail fetch fails, result_text_raw should be None
    assert rows[0]["result_text_raw"] is None