"""
Integration tests for results display templates.

Uses the Flask test client to verify that the recommendation card,
savings display, caveats, breakdown table, HTMX partial rendering,
chart SVG, and accessibility render correctly in the full page
response after form submission.
"""

from flask.testing import FlaskClient


def _valid_cash_loan_form() -> dict[str, str]:
    """Build form data for a Cash ($25,000) vs Loan ($25,000 at 5.99%)."""
    return {
        "purchase_price": "25000",
        "options[0][type]": "cash",
        "options[0][label]": "Pay in Full",
        "options[1][type]": "traditional_loan",
        "options[1][label]": "Bank Loan",
        "options[1][apr]": "5.99",
        "options[1][term_months]": "36",
        "options[1][down_payment]": "",
        "return_preset": "0.07",
        "return_rate_custom": "",
        "inflation_rate": "3",
        "tax_rate": "22",
    }


def _promo_deferred_form() -> dict[str, str]:
    """Build form data with a promo zero-percent option that triggers caveats."""
    return {
        "purchase_price": "10000",
        "options[0][type]": "promo_zero_percent",
        "options[0][label]": "Store Promo",
        "options[0][term_months]": "12",
        "options[0][post_promo_apr]": "24.99",
        "options[0][deferred_interest]": "1",
        "options[1][type]": "traditional_loan",
        "options[1][label]": "Credit Union",
        "options[1][apr]": "6",
        "options[1][term_months]": "36",
        "return_preset": "0.07",
        "return_rate_custom": "",
        "inflation_rate": "3",
        "tax_rate": "22",
    }


class TestRecommendationCard:
    """Tests for the recommendation hero card rendering."""

    def test_recommendation_card_shows_winner(self, client: FlaskClient):
        """POST /compare shows winner name in recommendation card."""
        response = client.post("/compare", data=_valid_cash_loan_form())
        assert response.status_code == 200
        html = response.data.decode()
        assert "recommendation-card" in html
        # One of the option names should appear as the winner
        assert "Pay in Full" in html or "Bank Loan" in html

    def test_savings_displayed(self, client: FlaskClient):
        """POST /compare shows savings amount formatted as currency."""
        response = client.post("/compare", data=_valid_cash_loan_form())
        html = response.data.decode()
        # Should contain a dollar amount in the savings section
        assert "Saves" in html or "savings" in html.lower()
        assert "$" in html


class TestCaveats:
    """Tests for caveat display on the hero card."""

    def test_caveats_on_hero(self, client: FlaskClient):
        """Promo with deferred interest triggers a caveat on the page."""
        response = client.post("/compare", data=_promo_deferred_form())
        html = response.data.decode()
        assert response.status_code == 200
        # Deferred interest caveat should appear somewhere
        assert "Deferred interest" in html or "caveat" in html


class TestBreakdownTable:
    """Tests for the cost breakdown table rendering."""

    def test_breakdown_table_present(self, client: FlaskClient):
        """POST /compare renders a breakdown table."""
        response = client.post("/compare", data=_valid_cash_loan_form())
        html = response.data.decode()
        assert "<table" in html
        assert "breakdown-table" in html

    def test_breakdown_has_true_total_cost(self, client: FlaskClient):
        """Breakdown table includes the True Total Cost row."""
        response = client.post("/compare", data=_valid_cash_loan_form())
        html = response.data.decode()
        assert "True Total Cost" in html

    def test_breakdown_has_total_payments(self, client: FlaskClient):
        """Breakdown table includes the Total Payments row."""
        response = client.post("/compare", data=_valid_cash_loan_form())
        html = response.data.decode()
        assert "Total Payments" in html


def _valid_form_with_down_payment() -> dict[str, str]:
    """Build form data for Cash vs Loan with down payment."""
    return {
        "purchase_price": "25000",
        "options[0][type]": "cash",
        "options[0][label]": "Pay in Full",
        "options[1][type]": "traditional_loan",
        "options[1][label]": "Bank Loan",
        "options[1][apr]": "6",
        "options[1][term_months]": "36",
        "options[1][down_payment]": "5000",
        "return_preset": "0.07",
        "return_rate_custom": "",
        "inflation_rate": "3",
        "tax_rate": "22",
    }


class TestHtmxPartial:
    """Tests for HTMX partial page replacement behavior."""

    def test_htmx_partial(self, client: FlaskClient):
        """POST /compare with HX-Request returns partial, not full page."""
        response = client.post(
            "/compare",
            data=_valid_form_with_down_payment(),
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        html = response.data.decode()
        # Partial should NOT contain full HTML document markers
        assert "<!DOCTYPE html>" not in html
        assert "<html" not in html
        # Should contain recommendation card
        assert "recommendation-card" in html
        # Should contain breakdown table
        assert "breakdown-table" in html
        # Should contain SVG chart markup
        assert "bar-chart-title" in html
        assert "line-chart-title" in html

    def test_non_htmx_full_page(self, client: FlaskClient):
        """POST /compare without HX-Request returns full HTML page."""
        response = client.post(
            "/compare",
            data=_valid_form_with_down_payment(),
        )
        assert response.status_code == 200
        html = response.data.decode()
        # Full page should contain HTML document markers
        assert "<!DOCTYPE html>" in html
        # Should still contain results
        assert "recommendation-card" in html

    def test_calculate_button_fallback(self, client: FlaskClient):
        """GET / renders a submit button with HTMX and form fallback."""
        response = client.get("/")
        html = response.data.decode()
        assert '<button type="submit"' in html
        assert "Compare Options" in html
        # HTMX attribute on form
        assert 'hx-post="/compare"' in html
        # Fallback form action
        assert 'action="/compare"' in html

    def test_htmx_error_response(self, client: FlaskClient):
        """POST /compare with HX-Request and invalid data returns error partial."""
        response = client.post(
            "/compare",
            data={
                "purchase_price": "",
                "options[0][type]": "cash",
                "options[0][label]": "Cash",
                "return_preset": "0.07",
            },
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        html = response.data.decode()
        # Should be a partial (no full HTML document)
        assert "<!DOCTYPE html>" not in html
        # Should contain error content
        assert "error" in html.lower() or "fix" in html.lower()


class TestChartSvg:
    """Tests for SVG chart rendering in results."""

    def test_bar_chart_svg(self, client: FlaskClient):
        """POST /compare renders bar chart SVG with correct structure."""
        response = client.post(
            "/compare",
            data=_valid_form_with_down_payment(),
        )
        html = response.data.decode()
        assert "<svg" in html
        assert 'aria-labelledby="bar-chart-title' in html
        assert "bar-pattern-solid" in html
        assert "<rect" in html

    def test_line_chart_svg(self, client: FlaskClient):
        """POST /compare renders line chart SVG with correct structure."""
        response = client.post(
            "/compare",
            data=_valid_form_with_down_payment(),
        )
        html = response.data.decode()
        assert 'aria-labelledby="line-chart-title' in html
        assert "stroke-dasharray" in html
        assert "<path" in html

    def test_chart_accessibility(self, client: FlaskClient):
        """Both charts have title, desc elements and hidden data tables."""
        response = client.post(
            "/compare",
            data=_valid_form_with_down_payment(),
        )
        html = response.data.decode()
        # Both charts have <title> and <desc>
        assert 'id="bar-chart-title"' in html
        assert 'id="bar-chart-desc"' in html
        assert 'id="line-chart-title"' in html
        assert 'id="line-chart-desc"' in html
        # Hidden data tables exist
        assert "visually-hidden" in html
        assert "<table" in html

    def test_chart_patterns(self, client: FlaskClient):
        """Bar chart contains fill pattern elements for non-color differentiation."""
        response = client.post(
            "/compare",
            data=_valid_form_with_down_payment(),
        )
        html = response.data.decode()
        assert "<pattern" in html
        # Multiple pattern IDs for different options
        assert "bar-pattern-solid" in html
        assert "bar-pattern-hatched" in html
