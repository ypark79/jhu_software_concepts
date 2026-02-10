# test_flask_page.py
# These tests check that the Flask page loads and that all routes work so
# so the webpage shows expected content.
import pytest

# Import the Flask app
from app import create_app
# import BeautifulSoup to parse index.html to test for the two buttons. 
from bs4 import BeautifulSoup


# Mark this test file in the "page load/HTML structure" category
@pytest.mark.web
def test_app_has_required_routes():
    app = create_app()
    # Collect all the route paths registered in Flask
    routes = [rule.rule for rule in app.url_map.iter_rules()]

    # Check that the main page route exists
    assert "/" in routes

    # Test that the page contains the routes to the Pull Data and 
    # Update Analysis buttons. 
    assert "/pull-data" in routes
    assert "/update-analysis" in routes

# Test flask page that displays analysis results
@pytest.mark.web
def test_get_analysis_page():
    app = create_app()
    # Create a fake web brwoser to test GET/POST requests without opening
    # an actual browser. 
    client = app.test_client()

    # Send a GET request to the page route
    response = client.get("/analysis")

    # Status 200 means success
    assert response.status_code == 200

    # Convert HTML response into text to test to see if the query outputs
    # displayed have the word "analysis" and "answer"in them. 
    html = response.get_data(as_text=True)

    # Parse the HTML to test if the two buttons functionally exist. 
    soup = BeautifulSoup(html, "html.parser")

    # Look for the form that submits to /pull-data
    pull_form = soup.find("form", {"action": "/pull-data"})

    # Look for the form that submits to /update-analysis
    update_form = soup.find("form", {"action": "/update-analysis"})

    # These asserts confirm the button exists
    assert pull_form is not None
    assert update_form is not None

    # Check the page contains the word "analysis" and "answer". Secondary
    # check for the two buttons. 
    assert "Analysis" in html
    assert "Answer:" in html

    # Test that the buttons exist by searching for their text labels. 
    # A third test to confirm the buttons exist. 
    assert "Pull Data" in html
    assert "Update Analysis" in html
