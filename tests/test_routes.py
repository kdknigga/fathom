"""
Integration tests for all routes including HTMX endpoints.

Uses the Flask test client to test the index page, HTMX partial
endpoints for type switching, add/remove options, and form submission
with validation and result display.
"""

from flask.testing import FlaskClient


class TestGetIndex:
    """Tests for GET / route."""

    def test_returns_200(self, client: FlaskClient):
        """GET / returns 200 status."""
        response = client.get("/")
        assert response.status_code == 200

    def test_contains_default_options(self, client: FlaskClient):
        """GET / contains 2 default option cards."""
        response = client.get("/")
        html = response.data.decode()
        assert 'id="option-0"' in html
        assert 'id="option-1"' in html

    def test_contains_purchase_price_input(self, client: FlaskClient):
        """GET / contains the purchase price input field."""
        response = client.get("/")
        html = response.data.decode()
        assert 'name="purchase_price"' in html

    def test_labels_have_for_attribute(self, client: FlaskClient):
        """GET / response has label elements with for attributes (A11Y)."""
        response = client.get("/")
        html = response.data.decode()
        assert 'for="purchase-price"' in html


class TestTypeSwitch:
    """Tests for GET /partials/option-fields/<idx> HTMX endpoint."""

    def test_traditional_returns_apr_field(self, client: FlaskClient):
        """Type switch to traditional_loan returns APR field."""
        response = client.get(
            "/partials/option-fields/0?options[0][type]=traditional_loan"
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "apr" in html.lower()

    def test_cash_returns_explanation(self, client: FlaskClient):
        """Type switch to cash returns explanation text."""
        response = client.get("/partials/option-fields/0?options[0][type]=cash")
        assert response.status_code == 200
        html = response.data.decode()
        assert "upfront" in html.lower() or "full" in html.lower()

    def test_promo_zero_returns_term_field(self, client: FlaskClient):
        """Type switch to promo_zero_percent returns term field."""
        response = client.get(
            "/partials/option-fields/0?options[0][type]=promo_zero_percent"
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "term_months" in html


class TestAddOption:
    """Tests for POST /partials/option/add HTMX endpoint."""

    def test_add_option_returns_three(self, client: FlaskClient):
        """POST /partials/option/add with 2 options returns 3 options."""
        response = client.post(
            "/partials/option/add",
            data={
                "purchase_price": "25000",
                "options[0][type]": "cash",
                "options[0][label]": "Cash",
                "options[1][type]": "traditional_loan",
                "options[1][label]": "Loan",
                "options[1][apr]": "5.99",
                "options[1][term_months]": "36",
            },
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert 'id="option-0"' in html
        assert 'id="option-1"' in html
        assert 'id="option-2"' in html

    def test_add_option_max_four_hides_button(self, client: FlaskClient):
        """POST /partials/option/add at 3 options returns 4 with no add button."""
        response = client.post(
            "/partials/option/add",
            data={
                "purchase_price": "25000",
                "options[0][type]": "cash",
                "options[0][label]": "A",
                "options[1][type]": "cash",
                "options[1][label]": "B",
                "options[2][type]": "cash",
                "options[2][label]": "C",
            },
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert 'id="option-3"' in html
        assert "Add Financing Option" not in html

    def test_add_preserves_existing_values(self, client: FlaskClient):
        """POST /partials/option/add preserves existing option labels."""
        response = client.post(
            "/partials/option/add",
            data={
                "purchase_price": "10000",
                "options[0][type]": "cash",
                "options[0][label]": "My Cash Option",
                "options[1][type]": "traditional_loan",
                "options[1][label]": "My Loan",
                "options[1][apr]": "6.5",
                "options[1][term_months]": "48",
            },
        )
        html = response.data.decode()
        assert "My Cash Option" in html
        assert "My Loan" in html


class TestRemoveOption:
    """Tests for POST /partials/option/<idx>/remove HTMX endpoint."""

    def test_remove_option(self, client: FlaskClient):
        """POST /partials/option/1/remove with 3 options returns 2."""
        response = client.post(
            "/partials/option/1/remove",
            data={
                "purchase_price": "10000",
                "options[0][type]": "cash",
                "options[0][label]": "A",
                "options[1][type]": "traditional_loan",
                "options[1][label]": "B",
                "options[1][apr]": "5",
                "options[1][term_months]": "24",
                "options[2][type]": "cash",
                "options[2][label]": "C",
            },
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert 'id="option-0"' in html
        assert 'id="option-1"' in html
        assert 'id="option-2"' not in html

    def test_remove_preserves_values(self, client: FlaskClient):
        """POST /partials/option/1/remove preserves option 0 and 2 values."""
        response = client.post(
            "/partials/option/1/remove",
            data={
                "purchase_price": "10000",
                "options[0][type]": "cash",
                "options[0][label]": "First",
                "options[1][type]": "traditional_loan",
                "options[1][label]": "Middle",
                "options[1][apr]": "5",
                "options[1][term_months]": "24",
                "options[2][type]": "cash",
                "options[2][label]": "Last",
            },
        )
        html = response.data.decode()
        assert "First" in html
        assert "Last" in html
        assert "Middle" not in html


class TestFormSubmission:
    """Tests for POST /compare form submission handler."""

    def test_submit_valid_form(self, client: FlaskClient):
        """POST /compare with valid Cash + Loan data returns 200."""
        response = client.post(
            "/compare",
            data={
                "purchase_price": "25000",
                "options[0][type]": "cash",
                "options[0][label]": "Pay in Full",
                "options[1][type]": "traditional_loan",
                "options[1][label]": "Bank Loan",
                "options[1][apr]": "5.99",
                "options[1][term_months]": "36",
                "options[1][down_payment]": "5000",
                "return_preset": "0.07",
                "return_rate_custom": "",
                "inflation_rate": "3",
                "tax_rate": "22",
            },
        )
        assert response.status_code == 200

    def test_submit_invalid_shows_errors(self, client: FlaskClient):
        """POST /compare with empty purchase price shows error."""
        response = client.post(
            "/compare",
            data={
                "purchase_price": "",
                "options[0][type]": "cash",
                "options[0][label]": "Cash",
                "return_preset": "0.07",
            },
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "field-error" in html

    def test_submit_repopulates_values(self, client: FlaskClient):
        """POST /compare with invalid data preserves entered values."""
        response = client.post(
            "/compare",
            data={
                "purchase_price": "",
                "options[0][type]": "traditional_loan",
                "options[0][label]": "My Special Loan",
                "options[0][apr]": "5.99",
                "options[0][term_months]": "36",
                "return_preset": "0.07",
            },
        )
        html = response.data.decode()
        assert "My Special Loan" in html
        assert "5.99" in html

    def test_return_rate_presets(self, client: FlaskClient):
        """POST /compare with return_preset=0.04 uses 4% rate (no error)."""
        response = client.post(
            "/compare",
            data={
                "purchase_price": "10000",
                "options[0][type]": "cash",
                "options[0][label]": "Cash",
                "options[1][type]": "traditional_loan",
                "options[1][label]": "Loan",
                "options[1][apr]": "5",
                "options[1][term_months]": "24",
                "return_preset": "0.04",
                "return_rate_custom": "",
                "inflation_rate": "3",
                "tax_rate": "22",
            },
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "field-error" not in html or "return" not in html.lower()

    def test_inflation_toggle(self, client: FlaskClient):
        """POST /compare with inflation enabled processes correctly."""
        response = client.post(
            "/compare",
            data={
                "purchase_price": "10000",
                "options[0][type]": "cash",
                "options[0][label]": "Cash",
                "options[1][type]": "traditional_loan",
                "options[1][label]": "Loan",
                "options[1][apr]": "5",
                "options[1][term_months]": "24",
                "return_preset": "0.07",
                "return_rate_custom": "",
                "inflation_enabled": "1",
                "inflation_rate": "2.5",
                "tax_rate": "22",
            },
        )
        assert response.status_code == 200

    def test_submit_with_scroll_to_error(self, client: FlaskClient):
        """POST /compare with errors includes scroll-to-error script."""
        response = client.post(
            "/compare",
            data={
                "purchase_price": "",
                "options[0][type]": "cash",
                "options[0][label]": "Cash",
                "return_preset": "0.07",
            },
        )
        html = response.data.decode()
        assert "scrollIntoView" in html
