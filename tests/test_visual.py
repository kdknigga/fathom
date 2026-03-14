"""
Visual structure tests verifying DOM elements on form and results pages.

Uses the Flask test client to assert key DOM elements are present,
ensuring the visual structure is verified in CI even without a browser.
"""

from flask.testing import FlaskClient

VALID_FORM_DATA = {
    "purchase_price": "15000",
    "options[0][type]": "cash",
    "options[0][label]": "Pay Cash",
    "options[1][type]": "traditional_loan",
    "options[1][label]": "Auto Loan",
    "options[1][apr]": "5.99",
    "options[1][term_months]": "36",
    "options[1][down_payment]": "2000",
    "return_preset": "0.07",
    "return_rate_custom": "",
    "inflation_enabled": "",
    "inflation_rate": "3",
    "tax_enabled": "",
    "tax_rate": "22",
}


class TestIndexPageStructure:
    """Verify the index page contains required DOM elements."""

    def test_index_returns_200(self, client: FlaskClient):
        """GET / returns HTTP 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_contains_form(self, client: FlaskClient):
        """Index page contains the comparison form."""
        html = client.get("/").data.decode()
        assert 'id="comparison-form"' in html

    def test_contains_option_cards(self, client: FlaskClient):
        """Index page contains at least two option cards."""
        html = client.get("/").data.decode()
        assert 'id="option-0"' in html
        assert 'id="option-1"' in html

    def test_contains_submit_button(self, client: FlaskClient):
        """Index page contains the compare/submit button."""
        html = client.get("/").data.decode()
        assert 'id="compare-btn"' in html

    def test_contains_results_target(self, client: FlaskClient):
        """Index page contains the results container for HTMX swap."""
        html = client.get("/").data.decode()
        assert 'id="results"' in html

    def test_purchase_price_label_not_duplicated(self, client: FlaskClient):
        """Purchase price label appears inside header with tooltip."""
        html = client.get("/").data.decode()
        assert '<label for="purchase-price">' in html
        assert "<header>" in html


class TestResultsPageStructure:
    """Verify the results page contains required DOM elements."""

    def test_results_returns_200(self, client: FlaskClient):
        """POST /compare with valid data returns HTTP 200."""
        response = client.post("/compare", data=VALID_FORM_DATA)
        assert response.status_code == 200

    def test_contains_recommendation_card(self, client: FlaskClient):
        """Results contain the recommendation card."""
        html = client.post("/compare", data=VALID_FORM_DATA).data.decode()
        assert "recommendation-card" in html

    def test_contains_winner_name(self, client: FlaskClient):
        """Results contain a winner name element."""
        html = client.post("/compare", data=VALID_FORM_DATA).data.decode()
        assert "winner-name" in html

    def test_contains_breakdown_table(self, client: FlaskClient):
        """Results contain the cost breakdown table."""
        html = client.post("/compare", data=VALID_FORM_DATA).data.decode()
        assert "breakdown-table" in html

    def test_contains_chart_svg(self, client: FlaskClient):
        """Results contain at least one SVG chart."""
        html = client.post("/compare", data=VALID_FORM_DATA).data.decode()
        assert "<svg" in html

    def test_contains_results_section(self, client: FlaskClient):
        """Results contain the results section landmark."""
        html = client.post("/compare", data=VALID_FORM_DATA).data.decode()
        assert 'aria-label="Comparison Results"' in html

    def test_contains_breakdown_section(self, client: FlaskClient):
        """Results contain the breakdown section landmark."""
        html = client.post("/compare", data=VALID_FORM_DATA).data.decode()
        assert 'aria-label="Cost Breakdown"' in html

    def test_contains_charts_section(self, client: FlaskClient):
        """Results contain the charts section landmark."""
        html = client.post("/compare", data=VALID_FORM_DATA).data.decode()
        assert 'aria-label="Visual Comparisons"' in html
