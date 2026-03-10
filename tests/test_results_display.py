"""
Integration tests for results display templates.

Uses the Flask test client to verify that the recommendation card,
savings display, caveats, and breakdown table render correctly
in the full page response after form submission.
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
