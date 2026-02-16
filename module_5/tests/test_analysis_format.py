# These tests check that analysis labels and percentage formatting
# are to two decimal places as per the assignment instructions.
import re
import pytest
from bs4 import BeautifulSoup
from app import create_app


@pytest.mark.analysis
def test_analysis_has_answer_labels_and_two_decimal_percents():
    # Create flask app and test client/fake browser.
    app = create_app()
    client = app.test_client()

    # Send request for homepage/analysis page.
    response = client.get("/analysis")

    # Assert page loaded successfully
    assert response.status_code == 200

    # Get HTML text from response
    html = response.get_data(as_text=True)

    # Parse HTML so we can search content cleanly and consolidate all
    soup = BeautifulSoup(html, "html.parser")

    # Find every answer block for all 11 queries.
    answers = soup.find_all("span", class_="answer")

    # Check that there are 11 answers (one per query)
    assert len(answers) == 11

    # Loop through each answer to check formatting
    for answer in answers:
        # Get the text for this answer
        answer_text = answer.get_text(" ")

        # Each answer should include the word "Answer:"
        assert "Answer:" in answer_text

        # Find all percent values inside this answer text using REGEX.
        percents = re.findall(r"\b\d+(\.\d+)?%\b", answer_text)

        # For each percent, confirm it has exactly two decimals
        for p in percents:
            assert re.fullmatch(r"\d+\.\d{2}%", p)
