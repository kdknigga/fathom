"""
Integration tests for all routes including HTMX endpoints.

Uses the Flask test client to test the index page, HTMX partial
endpoints for type switching, add/remove options, and form submission
with validation and result display.
"""

import io
import json

from flask import Flask
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

    def test_reset_form(self, client: FlaskClient):
        """GET / returns fresh default state: empty purchase price and 2 default options."""
        response = client.get("/")
        assert response.status_code == 200
        html = response.data.decode()
        # Purchase price is empty on fresh load
        assert 'name="purchase_price"' in html
        assert 'value=""' in html
        # Exactly 2 default option cards
        assert 'id="option-0"' in html
        assert 'id="option-1"' in html
        assert 'id="option-2"' not in html
        # No validation errors on fresh page
        assert "field-error" not in html

    def test_grid_layout(self, client: FlaskClient):
        """GET / response contains two-column grid structure (LYOT-01)."""
        response = client.get("/")
        html = response.data.decode()
        # Outer grid wrapper for the two-column layout
        assert 'class="grid"' in html
        # Form column on the left
        assert 'id="comparison-form"' in html
        # Results column on the right
        assert 'id="results"' in html


class TestTypeSwitch:
    """Tests for GET /partials/option-fields/<idx> HTMX endpoint."""

    def test_traditional_returns_apr_field(self, client: FlaskClient):
        """Type switch to traditional_loan returns APR field."""
        response = client.get(
            "/partials/option-fields/0?options[0][type]=traditional_loan",
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
            "/partials/option-fields/0?options[0][type]=promo_zero_percent",
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


class TestReturnPresetFormat:
    """Tests for return_preset format in GET / route."""

    def test_return_preset_format_010(self, app: Flask):
        """Return preset formats 0.10 as '0.10' not '0.1'."""
        app.config["FATHOM_SETTINGS"].default_return_rate = 0.10
        with app.test_client() as c:
            response = c.get("/")
            html = response.data.decode()
            # The 10% radio should be checked when default is 0.10
            assert "checked" in html
            # The template checks settings.return_preset == '0.10'
            # If the bug exists (str(0.10) -> "0.1"), the radio won't be checked
            # Verify the checked attribute appears near the 0.10 radio
            idx_010 = html.find('value="0.10"')
            assert idx_010 != -1
            # Find the nearest checked attribute within 100 chars
            snippet = html[max(0, idx_010 - 100) : idx_010 + 100]
            assert "checked" in snippet


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

    def test_tax_toggle(self, client: FlaskClient):
        """POST /compare with tax_enabled checkbox processes tax without errors."""
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
                "tax_enabled": "1",
                "tax_rate": "22",
                "inflation_rate": "3",
            },
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "field-error" not in html


class TestCommaFormattedRendering:
    """Tests for comma-formatted values in server-rendered HTML."""

    def test_purchase_price_comma_formatted(self, client: FlaskClient):
        """Submit with purchase_price=25000, response shows value='25,000'."""
        response = client.post(
            "/compare",
            data={
                "purchase_price": "25000",
                "options[0][type]": "cash",
                "options[0][label]": "Cash",
                "options[1][type]": "traditional_loan",
                "options[1][label]": "Loan",
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
        html = response.data.decode()
        assert 'value="25,000"' in html

    def test_down_payment_comma_formatted(self, client: FlaskClient):
        """Submit with down_payment=5000, response shows value='5,000'."""
        response = client.post(
            "/compare",
            data={
                "purchase_price": "25000",
                "options[0][type]": "cash",
                "options[0][label]": "Cash",
                "options[1][type]": "traditional_loan",
                "options[1][label]": "Loan",
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
        html = response.data.decode()
        assert 'value="5,000"' in html

    def test_comma_input_accepted_and_reformatted(self, client: FlaskClient):
        """Submit with comma values, verify correct parsing and reformatted output."""
        response = client.post(
            "/compare",
            data={
                "purchase_price": "100,000",
                "options[0][type]": "cash",
                "options[0][label]": "Cash",
                "options[1][type]": "traditional_loan",
                "options[1][label]": "Loan",
                "options[1][apr]": "5.99",
                "options[1][term_months]": "36",
                "options[1][down_payment]": "10,000",
                "return_preset": "0.07",
                "return_rate_custom": "",
                "inflation_rate": "3",
                "tax_rate": "22",
            },
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "field-error" not in html
        assert 'value="100,000"' in html


def _valid_form_data() -> dict[str, str]:
    """Return a minimal valid form with cash + traditional loan options."""
    return {
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
    }


class TestExport:
    """Tests for POST /export route."""

    def test_returns_200(self, client: FlaskClient):
        """POST /export with valid form data returns 200."""
        response = client.post("/export", data=_valid_form_data())
        assert response.status_code == 200

    def test_content_disposition(self, client: FlaskClient):
        """POST /export returns Content-Disposition attachment header."""
        response = client.post("/export", data=_valid_form_data())
        cd = response.headers.get("Content-Disposition", "")
        assert "attachment" in cd

    def test_filename_pattern(self, client: FlaskClient):
        """POST /export filename matches fathom-YYYY-MM-DD.json."""
        response = client.post("/export", data=_valid_form_data())
        cd = response.headers.get("Content-Disposition", "")
        # Expect filename like fathom-2026-03-13.json
        assert "fathom-" in cd
        assert ".json" in cd

    def test_content_type_json(self, client: FlaskClient):
        """POST /export returns application/json content type."""
        response = client.post("/export", data=_valid_form_data())
        assert "application/json" in response.content_type

    def test_json_has_version(self, client: FlaskClient):
        """POST /export JSON body includes version field."""
        response = client.post("/export", data=_valid_form_data())
        data = json.loads(response.data)
        assert "version" in data
        assert data["version"] == 1

    def test_json_structure(self, client: FlaskClient):
        """POST /export JSON body has purchase_price, options, settings."""
        response = client.post("/export", data=_valid_form_data())
        data = json.loads(response.data)
        assert data["purchase_price"] == "25000"
        assert len(data["options"]) == 2
        assert "settings" in data


class TestImport:
    """Tests for POST /import with valid JSON."""

    def test_import_repopulates_form(self, client: FlaskClient):
        """POST /import with valid JSON repopulates form with imported values."""
        export_data = {
            "version": 1,
            "purchase_price": "25000",
            "options": [
                {"type": "cash", "label": "Pay in Full"},
                {
                    "type": "traditional_loan",
                    "label": "Bank Loan",
                    "apr": "5.99",
                    "term_months": "36",
                    "down_payment": "5000",
                    "deferred_interest": False,
                    "retroactive_interest": False,
                    "post_promo_apr": "",
                    "cash_back_amount": "",
                    "discounted_price": "",
                    "custom_label": "",
                },
            ],
            "settings": {
                "return_preset": "0.07",
                "return_rate_custom": "",
                "inflation_enabled": False,
                "inflation_rate": "3",
                "tax_enabled": False,
                "tax_rate": "22",
            },
        }
        json_bytes = json.dumps(export_data).encode()
        response = client.post(
            "/import",
            data={"import_file": (io.BytesIO(json_bytes), "fathom-2026-03-13.json")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "Bank Loan" in html
        assert "5.99" in html


class TestImportErrors:
    """Tests for POST /import error handling."""

    def test_no_file_shows_error(self, client: FlaskClient):
        """POST /import with no file returns error message."""
        response = client.post(
            "/import",
            data={},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "field-error" in html or "import" in html.lower()

    def test_malformed_json_shows_error(self, client: FlaskClient):
        """POST /import with malformed JSON returns structural error."""
        response = client.post(
            "/import",
            data={
                "import_file": (
                    io.BytesIO(b"not valid json{{{"),
                    "bad.json",
                ),
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "not a valid Fathom export" in html or "field-error" in html

    def test_invalid_field_values_show_errors(self, client: FlaskClient):
        """POST /import with invalid field values shows inline field errors."""
        bad_data = {
            "version": 1,
            "purchase_price": "-100",
            "options": [
                {"type": "cash", "label": "Cash"},
                {
                    "type": "traditional_loan",
                    "label": "Loan",
                    "apr": "5",
                    "term_months": "36",
                    "deferred_interest": False,
                    "retroactive_interest": False,
                    "post_promo_apr": "",
                    "cash_back_amount": "",
                    "discounted_price": "",
                    "custom_label": "",
                    "down_payment": "",
                },
            ],
            "settings": {
                "return_preset": "0.07",
                "return_rate_custom": "",
                "inflation_enabled": False,
                "inflation_rate": "3",
                "tax_enabled": False,
                "tax_rate": "22",
            },
        }
        json_bytes = json.dumps(bad_data).encode()
        response = client.post(
            "/import",
            data={"import_file": (io.BytesIO(json_bytes), "bad-data.json")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "field-error" in html


class TestDetailTab:
    """Tests for POST /partials/detail/<idx> HTMX endpoint."""

    def test_detail_tab_returns_200(self, client: FlaskClient):
        """POST /partials/detail/0 with valid form data returns 200."""
        response = client.post("/partials/detail/0", data=_valid_form_data())
        assert response.status_code == 200

    def test_detail_tab_contains_table(self, client: FlaskClient):
        """POST /partials/detail/0 returns HTML with detail-table."""
        response = client.post("/partials/detail/0", data=_valid_form_data())
        html = response.data.decode()
        assert "detail-table" in html

    def test_detail_tab_annual(self, client: FlaskClient):
        """POST /partials/detail/0?granularity=annual returns annual data."""
        response = client.post(
            "/partials/detail/0?granularity=annual",
            data=_valid_form_data(),
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "Year" in html

    def test_detail_tab_invalid_index(self, client: FlaskClient):
        """POST /partials/detail/99 returns error message."""
        response = client.post("/partials/detail/99", data=_valid_form_data())
        assert response.status_code == 200
        html = response.data.decode()
        assert "not found" in html.lower() or "Option" in html


class TestDetailCompare:
    """Tests for POST /partials/detail/compare HTMX endpoint."""

    def test_compare_returns_200(self, client: FlaskClient):
        """POST /partials/detail/compare with valid form data returns 200."""
        response = client.post("/partials/detail/compare", data=_valid_form_data())
        assert response.status_code == 200

    def test_compare_contains_table(self, client: FlaskClient):
        """POST /partials/detail/compare returns HTML with detail-table."""
        response = client.post("/partials/detail/compare", data=_valid_form_data())
        html = response.data.decode()
        assert "detail-table" in html

    def test_compare_shows_option_names(self, client: FlaskClient):
        """POST /partials/detail/compare shows option names in header."""
        response = client.post("/partials/detail/compare", data=_valid_form_data())
        html = response.data.decode()
        assert "Pay in Full" in html
        assert "Bank Loan" in html


class TestAddOptionGuard:
    """Tests for add option guard when at maximum 4 options."""

    def test_add_option_at_4_returns_unchanged(self, client: FlaskClient):
        """POST /partials/option/add with 4 options returns unchanged form with warning."""
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
                "options[3][type]": "cash",
                "options[3][label]": "D",
            },
        )
        assert response.status_code == 200
        html = response.data.decode()
        # Still exactly 4 option cards (not 5)
        assert 'id="option-0"' in html
        assert 'id="option-1"' in html
        assert 'id="option-2"' in html
        assert 'id="option-3"' in html
        assert 'id="option-4"' not in html
        # Warning message present
        assert "Maximum 4 options allowed" in html

    def test_add_option_at_3_succeeds(self, client: FlaskClient):
        """POST /partials/option/add with 3 options returns 4 options (normal behavior)."""
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
        assert "Maximum 4 options allowed" not in html


class TestRemoveOptionGuard:
    """Tests for remove option guard when at minimum 2 options."""

    def test_remove_option_at_2_returns_unchanged(self, client: FlaskClient):
        """POST /partials/option/0/remove with 2 options returns unchanged form with warning."""
        response = client.post(
            "/partials/option/0/remove",
            data={
                "purchase_price": "25000",
                "options[0][type]": "cash",
                "options[0][label]": "A",
                "options[1][type]": "cash",
                "options[1][label]": "B",
            },
        )
        assert response.status_code == 200
        html = response.data.decode()
        # Still exactly 2 option cards (not 1)
        assert 'id="option-0"' in html
        assert 'id="option-1"' in html
        # Warning message present
        assert "Minimum 2 options required" in html

    def test_remove_option_at_3_succeeds(self, client: FlaskClient):
        """POST /partials/option/0/remove with 3 options returns 2 options (normal behavior)."""
        response = client.post(
            "/partials/option/0/remove",
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
        assert 'id="option-0"' in html
        assert 'id="option-1"' in html
        assert 'id="option-2"' not in html
        assert "Minimum 2 options required" not in html


class TestCustomOptionDisplay:
    """Tests for custom option label flow and template field labels."""

    def test_custom_label_in_rendered_results(self, client: FlaskClient):
        """POST /compare with custom option shows custom_label in results HTML."""
        response = client.post(
            "/compare",
            data={
                "purchase_price": "10000",
                "options[0][type]": "cash",
                "options[0][label]": "Pay in Full",
                "options[1][type]": "custom",
                "options[1][label]": "Custom/Other",
                "options[1][custom_label]": "Store Credit Card",
                "options[1][apr]": "18.99",
                "options[1][term_months]": "24",
                "return_preset": "0.07",
                "return_rate_custom": "",
                "inflation_rate": "3",
                "tax_rate": "22",
            },
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "Store Credit Card" in html

    def test_custom_option_down_payment_optional_label(self, client: FlaskClient):
        """Custom option form shows 'Down Payment (optional)' label."""
        response = client.get(
            "/partials/option-fields/0?options[0][type]=custom",
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "Down Payment (optional)" in html
        assert "Upfront Cash Required" not in html

    def test_custom_option_name_field_label(self, client: FlaskClient):
        """Custom option form shows 'Option Name (optional)' label."""
        response = client.get(
            "/partials/option-fields/0?options[0][type]=custom",
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "Option Name (optional)" in html
        assert "Description (optional)" not in html


class TestImportRoundTrip:
    """Tests for export-then-import round-trip fidelity."""

    def test_round_trip_preserves_values(self, client: FlaskClient):
        """Export then import produces form with identical values."""
        # Step 1: Export
        form_data = _valid_form_data()
        export_resp = client.post("/export", data=form_data)
        assert export_resp.status_code == 200
        exported_json = export_resp.data

        # Step 2: Import the exported JSON
        import_resp = client.post(
            "/import",
            data={
                "import_file": (
                    io.BytesIO(exported_json),
                    "fathom-roundtrip.json",
                ),
            },
            content_type="multipart/form-data",
        )
        assert import_resp.status_code == 200
        html = import_resp.data.decode()

        # Verify key values are present in the re-rendered form
        assert "Pay in Full" in html
        assert "Bank Loan" in html
        assert "5.99" in html
