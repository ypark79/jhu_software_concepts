# These tests check that the Flask page loads and that all routes work
# so the webpage shows expected content.
import pytest
import runpy
import flask.app
# Import the Flask app
from app import create_app
# import BeautifulSoup to parse index.html and test query
# answer formatting and the two buttons.
from bs4 import BeautifulSoup


# Mark this test file with "web" marker for pytest.ini.
@pytest.mark.web
# Test that the app has the required routes.
def test_app_has_required_routes():
    app = create_app()
    # Collect all the route paths registered in Flask
    routes = [rule.rule for rule in app.url_map.iter_rules()]

    # Check that the main page route exists
    assert "/analysis" in routes
    # Root URL should exist (redirects to /analysis)
    assert "/" in routes

    # Test that the page contains the routes to the Pull Data and
    # Update Analysis buttons.
    assert "/pull-data" in routes
    assert "/update-analysis" in routes


@pytest.mark.web
# Test that GET / redirects to /analysis.
def test_root_redirects_to_analysis():
    app = create_app()
    client = app.test_client()
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.location and "analysis" in resp.location

# Test flask page that displays analysis results
@pytest.mark.web
def test_get_analysis_page():
    # Create flask app object and fake web browser to
    # test GET/POST requests.
    # without opening an actual browser.
    app = create_app()

    client = app.test_client()

    # Send a GET request to the page route
    # If successful, the response status code should be 200.
    response = client.get("/analysis")

    assert response.status_code == 200

    # Convert HTML response into text and convert to
    # a BeautifulSoup object.
    # to faciltiate text parsing.
    html = response.get_data(as_text=True)

    soup = BeautifulSoup(html, "html.parser")

    # Look for the form that submits to /pull-data
    # and /update-analysis.
    # Confirm the two buttons exist.
    pull_form = soup.find("form", {"action": "/pull-data"})

    update_form = soup.find("form", {"action": "/update-analysis"})

    assert pull_form is not None

    assert update_form is not None

    # Check query results contains the word "analysis" and "answer".
    # check for the two buttons by checking their text labels.
    assert "Analysis" in html
    assert "Answer:" in html

    assert "Pull Data" in html
    assert "Update Analysis" in html

@pytest.mark.web
# Test that /scrape-status is False when no process is running.
def test_scrape_status_route_idle():

    app = create_app()
    client = app.test_client()

    resp = client.get("/scrape-status")
    assert resp.status_code == 200
    assert resp.get_json() == {"is_scraping": False}


@pytest.mark.web
# Test that /scrape-status is True when a process is running.
def test_scrape_status_route_busy():

    class DummyProcess:
        def poll(self):
            return None  # None means "still running"

    app = create_app()
    app.scraping_process = DummyProcess()
    client = app.test_client()

    resp = client.get("/scrape-status")
    assert resp.status_code == 200
    assert resp.get_json() == {"is_scraping": True}


@pytest.mark.buttons
# This test checks /pull-data returns 500 when subprocess fails.
def test_pull_data_exception_returns_500(monkeypatch):

    def fake_popen(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("app.subprocess.Popen", fake_popen)

    app = create_app()
    client = app.test_client()
    resp = client.post("/pull-data")

    assert resp.status_code == 500
    assert resp.get_json()["ok"] is False


@pytest.mark.web
# This test covers the /analysis path when get_connection() returns None
# (no DB available); the page still renders with empty results.
def test_analysis_handles_connection_none(monkeypatch):
    monkeypatch.setattr("app.get_connection", lambda: None)
    app = create_app()
    client = app.test_client()
    resp = client.get("/analysis")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "analysis" in html.lower() or "answer" in html.lower()


@pytest.mark.web
# This test checks /analysis still renders when DB query fails.
def test_analysis_handles_db_error(monkeypatch):

    class BadCursor:
        def execute(self, *args, **kwargs):
            raise Exception("db error")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class BadConn:
        def cursor(self):
            return BadCursor()

        def close(self):
            pass

    monkeypatch.setattr("app.get_connection", lambda: BadConn())

    app = create_app()
    client = app.test_client()
    resp = client.get("/analysis")

    assert resp.status_code == 200


@pytest.mark.web
# This test checks the __main__ block runs without
# starting a real server.
def test_app_main_block(monkeypatch):

    monkeypatch.setattr(flask.app.Flask, "run", lambda *a, **k: None)
    runpy.run_module("app", run_name="__main__")
