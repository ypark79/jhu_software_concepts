import pytest
from bs4 import BeautifulSoup
# Import the scrape module that exists inside the src/module_4 directory
# to test the functions within scrape.py.
import Scraper.scrape as scrape
import runpy
import urllib.request
from urllib.error import HTTPError, URLError
import time


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
    assert (
        scrape.extract_result_id("https://www.thegradcafe.com/result/123")
        == 123
    )

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


# Test extract_term_from_text returns the correct
# term from the string.
# term from the string.
@pytest.mark.analysis
def test_extract_term_from_text():
    # "Autumn" should normalize to "Fall"
    assert scrape.extract_term_from_text("Autumn 2026") == "Fall 2026"

    # If no term in text, expect None
    assert scrape.extract_term_from_text("No term here") is None

    # If input is None, expect None
    assert scrape.extract_term_from_text(None) is None


# Test infer_term_from_row returns the correct
# term from the string.
# term from the string.
@pytest.mark.analysis
def test_infer_term_from_row():
    # infer_term_from_row checks program/status/comments combined
    term = scrape.infer_term_from_row(
        "Program",
        "Status",
        "Admit for Autumn 2027"
    )
    assert term == "Fall 2027"

    # If no term anywhere, returns None
    assert scrape.infer_term_from_row("Program", "Status", "No term") is None


# Test extract_term_from_detail_row returns the correct
# term from the string.
# term from the string.
@pytest.mark.analysis
def test_extract_term_from_detail_row():
    # Detail row should detect "Fall 2026"
    assert (
        scrape.extract_term_from_detail_row("Applied for Fall 2026")
        == "Fall 2026"
    )

    # Missing or empty detail text returns None
    assert scrape.extract_term_from_detail_row("") is None


# Test extract_tr_rows_from_html returns the correct
# rows from the HTML string.
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
    # Build a BeautifulSoup row so we can test
    # _row_dict_from_tr directly
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
    # This fake function replaces download_html so we
    # never hit the internet.
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
    rows, stop_now = scrape.scrape_data(
        "https://www.thegradcafe.com/survey/",
        set()
    )

    # We should get one row
    assert len(rows) == 1
    assert stop_now is False

    # The detail row should infer term from the "detail" tr
    assert rows[0]["term_inferred"] == "Fall 2026"

    # result_text_raw should be populated from DETAIL_PAGE_HTML
    assert rows[0]["result_text_raw"] is not None


# Test scrape_data stops when it encounters an
# existing result ID.
# existing result ID.
@pytest.mark.analysis
def test_scrape_data_stops_on_existing_id(monkeypatch):
    def fake_download_html(url):
        return SURVEY_PAGE_HTML

    monkeypatch.setattr(scrape, "download_html", fake_download_html)
    monkeypatch.setattr(scrape.time, "sleep", lambda x: None)

    # existing_ids already has 123, so scraper should stop immediately
    rows, stop_now = scrape.scrape_data(
        "https://www.thegradcafe.com/survey/",
        {123}
    )

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
    rows, stop_now = scrape.scrape_data(
        "https://www.thegradcafe.com/survey/",
        set()
    )

    # No link means no detail URL; row should be skipped
    assert rows == []
    assert stop_now is False


# Test scrape_data sets result_text_raw to None
# if the detail page fetch fails.
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

    # Use monkeypatch to replace download_html with the fake function.
    monkeypatch.setattr(scrape, "download_html", fake_download_html)
    monkeypatch.setattr(scrape.time, "sleep", lambda x: None)

    # Run scrape_data with no existing IDs
    rows, _ = scrape.scrape_data("https://www.thegradcafe.com/survey/", set())

    # One row should be returned
    assert len(rows) == 1
    # If detail fetch fails, result_text_raw should be None
    assert rows[0]["result_text_raw"] is None


@pytest.mark.analysis
# This test checks request headers are set.
def test_make_request_headers():

    req = scrape._make_request("https://example.com")
    headers = dict(req.header_items())

    # Case-insensitive check
    lower_keys = {k.lower() for k in headers.keys()}
    assert "user-agent" in lower_keys
    assert "accept" in lower_keys
    assert req.get_method() == "GET"


@pytest.mark.analysis
# This test checks download_html returns decoded HTML.
def test_download_html_success(monkeypatch):

    class FakeResp:
        def read(self):
            return b"<html>ok</html>"

    monkeypatch.setattr(scrape, "urlopen", lambda req, timeout=60: FakeResp())
    assert scrape.download_html("https://example.com") == "<html>ok</html>"


@pytest.mark.analysis
# This test checks 5xx errors retry then fail.
def test_download_html_http_error_retries(monkeypatch):

    def fake_urlopen(req, timeout=60):
        raise HTTPError(req.full_url, 500, "Server Error", hdrs=None, fp=None)

    monkeypatch.setattr(scrape, "urlopen", fake_urlopen)
    monkeypatch.setattr(scrape.time, "sleep", lambda x: None)

    with pytest.raises(RuntimeError):
        scrape.download_html("https://example.com")


@pytest.mark.analysis
# This test checks non-5xx HTTP errors raise immediately.
def test_download_html_http_error_non_retry(monkeypatch):

    def fake_urlopen(req, timeout=60):
        raise HTTPError(req.full_url, 404, "Not Found", hdrs=None, fp=None)

    monkeypatch.setattr(scrape, "urlopen", fake_urlopen)

    with pytest.raises(HTTPError):
        scrape.download_html("https://example.com")


@pytest.mark.analysis
# This test checks URLError retries then fails.
def test_download_html_urlerror(monkeypatch):

    def fake_urlopen(req, timeout=60):
        raise URLError("network")

    monkeypatch.setattr(scrape, "urlopen", fake_urlopen)
    monkeypatch.setattr(scrape.time, "sleep", lambda x: None)

    with pytest.raises(RuntimeError):
        scrape.download_html("https://example.com")


@pytest.mark.analysis
# This test checks Autumn is normalized to Fall.
def test_extract_term_from_detail_row_autumn():

    assert scrape.extract_term_from_detail_row("Autumn 2026") == "Fall 2026"


@pytest.mark.analysis
# This test checks empty pages return ([], False).
def test_scrape_data_empty_page(monkeypatch):

    monkeypatch.setattr(scrape, "download_html", lambda url: "<html></html>")
    rows, stop_now = scrape.scrape_data("https://example.com", set())
    assert rows == []
    assert stop_now is False


@pytest.mark.analysis
# This test checks rows without numeric result_id are skipped.
def test_scrape_data_missing_result_id(monkeypatch):

    html = """
    <table>
      <tr>
        <td>U</td><td>P</td><td>D</td><td>S</td><td>C</td>
        <td><a href="/result/notnumber">View</a></td>
      </tr>
    </table>
    """
    monkeypatch.setattr(scrape, "download_html", lambda url: html)
    monkeypatch.setattr(scrape.time, "sleep", lambda x: None)

    rows, stop_now = scrape.scrape_data("https://example.com", set())
    assert rows == []
    assert stop_now is False


@pytest.mark.analysis
# This test checks detail rows without term keep term_inferred None.
def test_scrape_data_detail_row_no_term(monkeypatch):

    html = """
    <table>
      <tr>
        <td>U</td><td>P</td><td>D</td><td>S</td><td>C</td>
        <td><a href="/result/123">View</a></td>
      </tr>
      <tr>
        <td>No term here</td>
      </tr>
    </table>
    """
    monkeypatch.setattr(scrape, "download_html", lambda url: html)
    monkeypatch.setattr(scrape.time, "sleep", lambda x: None)

    rows, stop_now = scrape.scrape_data("https://example.com", set())
    assert len(rows) == 1
    assert rows[0]["term_inferred"] is None


@pytest.mark.analysis
# This test checks save_data/load_data roundtrip.
def test_scrape_save_and_load(tmp_path):

    data = [{"x": 1}]
    path = tmp_path / "data.json"
    scrape.save_data(data, str(path))
    assert scrape.load_data(str(path)) == data


@pytest.mark.analysis
# This test checks load_data returns [] on bad JSON.
def test_scrape_load_bad_json(tmp_path):

    bad = tmp_path / "bad.json"
    bad.write_text("{bad", encoding="utf-8")
    assert scrape.load_data(str(bad)) == []


@pytest.mark.analysis
# This test checks __main__ runs safely without real network.
def test_scrape_main_block(monkeypatch, tmp_path):

    class FakeResp:
        def read(self):
            return b"<html></html>"

    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: FakeResp())
    monkeypatch.setattr(scrape.time, "sleep", lambda x: None)
    monkeypatch.chdir(tmp_path)

    runpy.run_module("Scraper.scrape", run_name="__main__")


@pytest.mark.analysis
# Simulates the scraper’s __main__ loop with empty pages to cover the
# early‑exit logic without real network calls.
def test_scrape_main_loop_paths(monkeypatch, tmp_path):

    monkeypatch.chdir(tmp_path)

    class FakeResp:
        def read(self):
            return b"<html></html>"

    # Patch the global urlopen used by the __main__ module
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: FakeResp())
    monkeypatch.setattr(time, "sleep", lambda x: None)

    runpy.run_module("Scraper.scrape", run_name="__main__")


@pytest.mark.analysis
# Forces the __main__ loop to stop when it hits
# an already-known result_id.
def test_scrape_main_loop_stop_now(monkeypatch, tmp_path):
    import io, json, builtins
    monkeypatch.chdir(tmp_path)

    # Fake master data so existing_ids contains 123
    def fake_open(path, mode="r", *args, **kwargs):
        if "r" in mode:
            return io.StringIO(json.dumps([{"url": "/result/123"}]))
        return io.StringIO()
    monkeypatch.setattr(builtins, "open", fake_open)

    # List page HTML contains /result/123, so scrape_data
    # sets stop_now True
    class FakeResp:
        def read(self):
            return b"""
            <table>
              <tr>
                <td>U</td><td>P</td><td>D</td><td>S</td><td>C</td>
                <td><a href="/result/123">View</a></td>
              </tr>
            </table>
            """

    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: FakeResp())
    monkeypatch.setattr(time, "sleep", lambda x: None)

    runpy.run_module("Scraper.scrape", run_name="__main__")


@pytest.mark.analysis
# Forces a page scrape error once to cover the error-handling branch.
def test_scrape_main_loop_error_path(monkeypatch, tmp_path):
    import io, builtins
    monkeypatch.chdir(tmp_path)

    # Fake master data
    monkeypatch.setattr(builtins, "open", lambda *a, **k: io.StringIO("[]"))

    # First 5 urlopen calls raise HTTPError (download_html fails),
    # then return empty HTML so the loop exits.
    calls = {"n": 0}
    def fake_urlopen(req, timeout=60):
        class FakeResp:
            def read(self): return b"<html></html>"

        if calls["n"] < 5:
            calls["n"] += 1
            raise HTTPError(
                req.full_url,
                500,
                "Server Error",
                hdrs=None,
                fp=None
            )
        return FakeResp()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(time, "sleep", lambda x: None)

    runpy.run_module("Scraper.scrape", run_name="__main__")

@pytest.mark.analysis
# Runs the scraper __main__ loop through a non-empty page,
# then empty pages to hit the main success path and early exit.
# to hit the main success path and early exit.
def test_scrape_main_loop_non_empty_then_empty(monkeypatch, tmp_path):

    monkeypatch.chdir(tmp_path)

    # Fake master data so existing_ids gets populated
    import io, json, builtins
    def fake_open(path, mode="r", *args, **kwargs):
        if "r" in mode:
            return io.StringIO(json.dumps([{"url": "/result/999"}]))
        return io.StringIO()
    monkeypatch.setattr(builtins, "open", fake_open)

    # Return one real row on first page, then empty pages
    page_calls = {"n": 0}
    def fake_urlopen(req, timeout=60):
        class FakeResp:
            def __init__(self, text): self.text = text
            def read(self): return self.text.encode("utf-8")

        url = req.full_url if hasattr(req, "full_url") else str(req)

        if "/result/" in url:
            return FakeResp("<html>detail</html>")

        # First page returns one row + a detail row
        if page_calls["n"] == 0:
            page_calls["n"] += 1
            return FakeResp("""
            <table>
              <tr>
                <td>U</td><td>P</td><td>D</td><td>S</td><td>C</td>
                <td><a href="/result/123">View</a></td>
              </tr>
              <tr>
                <td>Applied for Fall 2026</td>
              </tr>
            </table>
            """)
        # After that, return empty HTML
        return FakeResp("<html></html>")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(time, "sleep", lambda x: None)

    runpy.run_module("Scraper.scrape", run_name="__main__")


@pytest.mark.analysis
# Forces a page scrape error in the __main__ loop to cover the
# error‑handling branch.
def test_scrape_main_loop_error_path(monkeypatch, tmp_path):

    monkeypatch.chdir(tmp_path)

    # Fake master data (so load_data succeeds)
    import io
    import builtins
    def fake_open(path, mode="r", *args, **kwargs):
        if "r" in mode:
            return io.StringIO("[]")
        return io.StringIO()
    monkeypatch.setattr(builtins, "open", fake_open)

    # First call raises HTTPError, then empty HTML to exit
    calls = {"n": 0}
    def fake_urlopen(req, timeout=60):
        class FakeResp:
            def read(self): return b"<html></html>"

        if calls["n"] == 0:
            calls["n"] += 1
            raise HTTPError(
                req.full_url,
                500,
                "Server Error",
                hdrs=None,
                fp=None
            )
        return FakeResp()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(time, "sleep", lambda x: None)

    runpy.run_module("Scraper.scrape", run_name="__main__")
