# These tests check that the Flask page loads and that all routes work
# so the webpage shows expected content.
import pytest

# Import the Flask app
from app import create_app
# import BeautifulSoup to parse index.html to test for query asnwer formatting 
# and for the two buttons. 
from bs4 import BeautifulSoup


# Mark this test file with "web" marker for pytest.ini. 
@pytest.mark.web
def test_app_has_required_routes():
    app = create_app()
    # Collect all the route paths registered in Flask
    routes = [rule.rule for rule in app.url_map.iter_rules()]

    # Check that the main page route exists
    assert "/analysis" in routes

    # Test that the page contains the routes to the Pull Data and 
    # Update Analysis buttons. 
    assert "/pull-data" in routes
    assert "/update-analysis" in routes

# Test flask page that displays analysis results
@pytest.mark.web
def test_get_analysis_page():
    # Create flask app object andfake web browser to test GET/POST requests 
    # without opening an actual browser. 
    app = create_app()

    client = app.test_client()

    # Send a GET request to the page route
    # If successful, the response status code should be 200. 
    response = client.get("/analysis")

    assert response.status_code == 200

    # Convert HTML response into text and convert to a BeautifulSoup object
    # to faciltiate text parsing. 
    html = response.get_data(as_text=True)

    soup = BeautifulSoup(html, "html.parser")

    # Look for the form that submits to /pull-data and /update-analysis. 
    # Confirm the two buttons exist. 
    pull_form = soup.find("form", {"action": "/pull-data"})

    update_form = soup.find("form", {"action": "/update-analysis"})

    assert pull_form is not None

    assert update_form is not None

    # Check query results contains the word "analysis" and "answer". Secondary
    # check for the two buttons by checking their text labels. 
    assert "Analysis" in html
    assert "Answer:" in html

    assert "Pull Data" in html
    assert "Update Analysis" in html
