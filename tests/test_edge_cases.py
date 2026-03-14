"""
Edge case tests for form validation and HTMX error handling.

Covers boundary conditions, malformed inputs, and edge cases in
form parsing and submission that are not covered by the main test suite.
"""

from flask.testing import FlaskClient
from pydantic import ValidationError
from werkzeug.datastructures import ImmutableMultiDict

from fathom.forms import parse_form_data, pydantic_errors_to_dict


def _make_form(data: dict[str, str]) -> ImmutableMultiDict:
    """Build an ImmutableMultiDict from a flat dict for test convenience."""
    return ImmutableMultiDict(data)


def _get_errors(data: dict[str, str]) -> dict[str, str]:
    """Parse form data and return validation errors as a dict."""
    form = _make_form(data)
    try:
        parse_form_data(form)
    except ValidationError as exc:
        return pydantic_errors_to_dict(exc)
    return {}


class TestFormValidationEdgeCases:
    """Edge cases in form validation."""

    def test_negative_purchase_price(self):
        """Negative purchase price produces an error."""
        errors = _get_errors(
            {
                "purchase_price": "-100",
                "options[0][type]": "cash",
                "options[0][label]": "Cash",
                "options[1][type]": "cash",
                "options[1][label]": "Cash2",
                "return_preset": "0.07",
            },
        )
        assert "purchase_price" in errors

    def test_whitespace_only_purchase_price(self):
        """Whitespace-only purchase price produces an error."""
        errors = _get_errors(
            {
                "purchase_price": "   ",
                "options[0][type]": "cash",
                "options[0][label]": "Cash",
                "options[1][type]": "cash",
                "options[1][label]": "Cash2",
                "return_preset": "0.07",
            },
        )
        assert "purchase_price" in errors

    def test_negative_down_payment(self):
        """Negative down payment produces an error."""
        errors = _get_errors(
            {
                "purchase_price": "10000",
                "options[0][type]": "traditional_loan",
                "options[0][label]": "Loan",
                "options[0][apr]": "5",
                "options[0][term_months]": "24",
                "options[0][down_payment]": "-500",
                "options[1][type]": "cash",
                "options[1][label]": "Cash",
                "return_preset": "0.07",
            },
        )
        assert "options.0.down_payment" in errors

    def test_non_numeric_term_months(self):
        """Non-numeric term months produces an error."""
        errors = _get_errors(
            {
                "purchase_price": "10000",
                "options[0][type]": "traditional_loan",
                "options[0][label]": "Loan",
                "options[0][apr]": "5",
                "options[0][term_months]": "abc",
                "options[1][type]": "cash",
                "options[1][label]": "Cash",
                "return_preset": "0.07",
            },
        )
        assert "options.0.term_months" in errors

    def test_non_numeric_apr(self):
        """Non-numeric APR produces an error."""
        errors = _get_errors(
            {
                "purchase_price": "10000",
                "options[0][type]": "traditional_loan",
                "options[0][label]": "Loan",
                "options[0][apr]": "bad",
                "options[0][term_months]": "24",
                "options[1][type]": "cash",
                "options[1][label]": "Cash",
                "return_preset": "0.07",
            },
        )
        assert "options.0.apr" in errors

    def test_zero_cash_back_amount(self):
        """Zero cash-back amount produces an error."""
        errors = _get_errors(
            {
                "purchase_price": "10000",
                "options[0][type]": "promo_cash_back",
                "options[0][label]": "CB",
                "options[0][apr]": "5",
                "options[0][term_months]": "24",
                "options[0][cash_back_amount]": "0",
                "options[1][type]": "cash",
                "options[1][label]": "Cash",
                "return_preset": "0.07",
            },
        )
        assert "options.0.cash_back_amount" in errors

    def test_invalid_return_rate_preset(self):
        """Invalid return rate preset produces an error."""
        errors = _get_errors(
            {
                "purchase_price": "10000",
                "options[0][type]": "cash",
                "options[0][label]": "Cash",
                "options[1][type]": "cash",
                "options[1][label]": "Cash2",
                "return_preset": "0.99",
                "return_rate_custom": "",
            },
        )
        assert "settings.return_rate" in errors

    def test_non_numeric_custom_return_rate(self):
        """Non-numeric custom return rate produces an error."""
        errors = _get_errors(
            {
                "purchase_price": "10000",
                "options[0][type]": "cash",
                "options[0][label]": "Cash",
                "options[1][type]": "cash",
                "options[1][label]": "Cash2",
                "return_preset": "0.07",
                "return_rate_custom": "xyz",
            },
        )
        assert "settings.return_rate" in errors

    def test_post_promo_apr_out_of_range(self):
        """Post-promo APR above 40% produces an error."""
        errors = _get_errors(
            {
                "purchase_price": "10000",
                "options[0][type]": "promo_zero_percent",
                "options[0][label]": "Promo",
                "options[0][term_months]": "12",
                "options[0][post_promo_apr]": "50",
                "options[1][type]": "cash",
                "options[1][label]": "Cash",
                "return_preset": "0.07",
            },
        )
        assert "options.0.post_promo_apr" in errors

    def test_zero_discounted_price(self):
        """Zero discounted price produces an error."""
        errors = _get_errors(
            {
                "purchase_price": "25000",
                "options[0][type]": "promo_price_reduction",
                "options[0][label]": "Price Cut",
                "options[0][apr]": "6",
                "options[0][term_months]": "36",
                "options[0][discounted_price]": "0",
                "options[1][type]": "cash",
                "options[1][label]": "Cash",
                "return_preset": "0.07",
            },
        )
        assert "options.0.discounted_price" in errors


class TestHtmxEdgeCases:
    """Edge cases in HTMX endpoint behavior."""

    def test_type_switch_invalid_type_falls_back(self, client: FlaskClient):
        """Unknown option type in type switch falls back to cash fields."""
        response = client.get(
            "/partials/option-fields/0?options[0][type]=nonexistent_type",
        )
        assert response.status_code == 200

    def test_remove_invalid_index_no_crash(self, client: FlaskClient):
        """Removing an out-of-range index doesn't crash."""
        response = client.post(
            "/partials/option/99/remove",
            data={
                "purchase_price": "10000",
                "options[0][type]": "cash",
                "options[0][label]": "A",
                "options[1][type]": "cash",
                "options[1][label]": "B",
            },
        )
        assert response.status_code == 200

    def test_htmx_partial_errors_show_validation_messages(self, client: FlaskClient):
        """HTMX error response contains specific field error messages."""
        response = client.post(
            "/compare",
            data={
                "purchase_price": "10000",
                "options[0][type]": "traditional_loan",
                "options[0][label]": "Loan",
                "options[0][apr]": "",
                "options[0][term_months]": "",
                "options[1][type]": "cash",
                "options[1][label]": "Cash",
                "return_preset": "0.07",
            },
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "required" in html.lower()

    def test_compare_with_all_settings_enabled(self, client: FlaskClient):
        """POST /compare with inflation and tax enabled returns valid results."""
        response = client.post(
            "/compare",
            data={
                "purchase_price": "20000",
                "options[0][type]": "cash",
                "options[0][label]": "Pay Cash",
                "options[1][type]": "traditional_loan",
                "options[1][label]": "Loan",
                "options[1][apr]": "6",
                "options[1][term_months]": "48",
                "options[1][down_payment]": "3000",
                "return_preset": "0.07",
                "return_rate_custom": "",
                "inflation_enabled": "1",
                "inflation_rate": "3",
                "tax_enabled": "1",
                "tax_rate": "25",
            },
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "recommendation-card" in html
        assert "breakdown-table" in html
