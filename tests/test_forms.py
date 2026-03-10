"""
Unit tests for form parsing, validation, and domain model construction.

Tests cover parse_form_data, validate_form_data, and build_domain_objects
from the fathom.forms module.
"""

from decimal import Decimal

from werkzeug.datastructures import ImmutableMultiDict

from fathom.forms import build_domain_objects, parse_form_data, validate_form_data
from fathom.models import OptionType


def _make_form(data: dict[str, str]) -> ImmutableMultiDict:
    """Build an ImmutableMultiDict from a flat dict for test convenience."""
    return ImmutableMultiDict(data)


def _valid_cash_loan_form() -> dict[str, str]:
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


# --- parse_form_data tests ---


class TestParseFormData:
    """Tests for parse_form_data function."""

    def test_extracts_purchase_price(self):
        """Parse purchase price from form data."""
        form = _make_form({"purchase_price": "25000"})
        parsed = parse_form_data(form)
        assert parsed["purchase_price"] == "25000"

    def test_extracts_options_by_index(self):
        """Parse indexed option fields into a list."""
        form = _make_form(_valid_cash_loan_form())
        parsed = parse_form_data(form)
        assert len(parsed["options"]) == 2
        assert parsed["options"][0]["type"] == "cash"
        assert parsed["options"][1]["type"] == "traditional_loan"
        assert parsed["options"][1]["apr"] == "5.99"
        assert parsed["options"][1]["term_months"] == "36"

    def test_handles_index_gaps(self):
        """Parse options correctly when indices have gaps (e.g., 0, 2)."""
        form = _make_form(
            {
                "purchase_price": "10000",
                "options[0][type]": "cash",
                "options[0][label]": "Cash",
                "options[2][type]": "traditional_loan",
                "options[2][label]": "Loan",
                "options[2][apr]": "6",
                "options[2][term_months]": "24",
            }
        )
        parsed = parse_form_data(form)
        assert len(parsed["options"]) == 2
        assert parsed["options"][0]["type"] == "cash"
        assert parsed["options"][1]["type"] == "traditional_loan"

    def test_extracts_settings(self):
        """Parse global settings from form data."""
        form = _make_form(
            {
                **_valid_cash_loan_form(),
                "inflation_enabled": "1",
                "tax_enabled": "1",
            }
        )
        parsed = parse_form_data(form)
        assert parsed["settings"]["return_preset"] == "0.07"
        assert parsed["settings"]["inflation_enabled"] is True
        assert parsed["settings"]["tax_enabled"] is True
        assert parsed["settings"]["inflation_rate"] == "3"
        assert parsed["settings"]["tax_rate"] == "22"

    def test_checkbox_defaults_false(self):
        """Unchecked checkboxes default to False."""
        form = _make_form(_valid_cash_loan_form())
        parsed = parse_form_data(form)
        assert parsed["settings"]["inflation_enabled"] is False
        assert parsed["settings"]["tax_enabled"] is False

    def test_extracts_all_option_fields(self):
        """Parse all possible option fields including promo-specific ones."""
        form = _make_form(
            {
                "purchase_price": "10000",
                "options[0][type]": "promo_zero_percent",
                "options[0][label]": "Promo",
                "options[0][term_months]": "12",
                "options[0][down_payment]": "1000",
                "options[0][post_promo_apr]": "24.99",
                "options[0][deferred_interest]": "1",
            }
        )
        parsed = parse_form_data(form)
        opt = parsed["options"][0]
        assert opt["post_promo_apr"] == "24.99"
        assert opt["deferred_interest"] is True

    def test_extracts_cash_back_and_discounted_price(self):
        """Parse cash_back_amount and discounted_price fields."""
        form = _make_form(
            {
                "purchase_price": "25000",
                "options[0][type]": "promo_cash_back",
                "options[0][label]": "Cash Back",
                "options[0][apr]": "5",
                "options[0][term_months]": "24",
                "options[0][cash_back_amount]": "500",
                "options[1][type]": "promo_price_reduction",
                "options[1][label]": "Price Cut",
                "options[1][discounted_price]": "22000",
                "options[1][apr]": "6",
                "options[1][term_months]": "36",
            }
        )
        parsed = parse_form_data(form)
        assert parsed["options"][0]["cash_back_amount"] == "500"
        assert parsed["options"][1]["discounted_price"] == "22000"


# --- validate_form_data tests ---


class TestValidateFormData:
    """Tests for validate_form_data function."""

    def test_valid_data_returns_empty(self):
        """Valid form data produces no errors."""
        form = _make_form(_valid_cash_loan_form())
        parsed = parse_form_data(form)
        errors = validate_form_data(parsed)
        assert errors == {}

    def test_empty_purchase_price(self):
        """Empty purchase price produces an error."""
        form = _make_form({**_valid_cash_loan_form(), "purchase_price": ""})
        parsed = parse_form_data(form)
        errors = validate_form_data(parsed)
        assert "purchase_price" in errors

    def test_non_numeric_purchase_price(self):
        """Non-numeric purchase price produces an error."""
        form = _make_form({**_valid_cash_loan_form(), "purchase_price": "abc"})
        parsed = parse_form_data(form)
        errors = validate_form_data(parsed)
        assert "purchase_price" in errors

    def test_zero_purchase_price(self):
        """Zero purchase price produces an error."""
        form = _make_form({**_valid_cash_loan_form(), "purchase_price": "0"})
        parsed = parse_form_data(form)
        errors = validate_form_data(parsed)
        assert "purchase_price" in errors

    def test_apr_out_of_range(self):
        """APR above 40% produces an error."""
        data = _valid_cash_loan_form()
        data["options[1][apr]"] = "41"
        form = _make_form(data)
        parsed = parse_form_data(form)
        errors = validate_form_data(parsed)
        assert "options.1.apr" in errors

    def test_term_months_out_of_range(self):
        """Term months outside 1-360 produces an error."""
        data = _valid_cash_loan_form()
        data["options[1][term_months]"] = "0"
        form = _make_form(data)
        parsed = parse_form_data(form)
        errors = validate_form_data(parsed)
        assert "options.1.term_months" in errors

    def test_term_months_too_high(self):
        """Term months above 360 produces an error."""
        data = _valid_cash_loan_form()
        data["options[1][term_months]"] = "361"
        form = _make_form(data)
        parsed = parse_form_data(form)
        errors = validate_form_data(parsed)
        assert "options.1.term_months" in errors

    def test_down_payment_exceeds_price(self):
        """Down payment exceeding purchase price produces an error."""
        data = _valid_cash_loan_form()
        data["options[1][down_payment]"] = "30000"
        form = _make_form(data)
        parsed = parse_form_data(form)
        errors = validate_form_data(parsed)
        assert "options.1.down_payment" in errors

    def test_cash_skips_apr_validation(self):
        """Cash option does not require or validate APR."""
        form = _make_form(_valid_cash_loan_form())
        parsed = parse_form_data(form)
        errors = validate_form_data(parsed)
        assert "options.0.apr" not in errors

    def test_promo_zero_requires_term(self):
        """Promo zero percent requires term_months."""
        form = _make_form(
            {
                "purchase_price": "10000",
                "options[0][type]": "promo_zero_percent",
                "options[0][label]": "Promo",
                "return_preset": "0.07",
            }
        )
        parsed = parse_form_data(form)
        errors = validate_form_data(parsed)
        assert "options.0.term_months" in errors

    def test_promo_cashback_requires_amount(self):
        """Promo cash back requires cash_back_amount."""
        form = _make_form(
            {
                "purchase_price": "10000",
                "options[0][type]": "promo_cash_back",
                "options[0][label]": "CB",
                "options[0][apr]": "5",
                "options[0][term_months]": "24",
                "return_preset": "0.07",
            }
        )
        parsed = parse_form_data(form)
        errors = validate_form_data(parsed)
        assert "options.0.cash_back_amount" in errors

    def test_promo_price_requires_discounted_price(self):
        """Promo price reduction requires discounted_price."""
        form = _make_form(
            {
                "purchase_price": "25000",
                "options[0][type]": "promo_price_reduction",
                "options[0][label]": "Price Cut",
                "options[0][apr]": "6",
                "options[0][term_months]": "36",
                "return_preset": "0.07",
            }
        )
        parsed = parse_form_data(form)
        errors = validate_form_data(parsed)
        assert "options.0.discounted_price" in errors

    def test_discounted_price_must_be_less_than_purchase(self):
        """Discounted price >= purchase price produces an error."""
        form = _make_form(
            {
                "purchase_price": "25000",
                "options[0][type]": "promo_price_reduction",
                "options[0][label]": "Price Cut",
                "options[0][apr]": "6",
                "options[0][term_months]": "36",
                "options[0][discounted_price]": "25000",
                "return_preset": "0.07",
            }
        )
        parsed = parse_form_data(form)
        errors = validate_form_data(parsed)
        assert "options.0.discounted_price" in errors

    def test_custom_return_rate_override(self):
        """Custom return rate with invalid value produces an error."""
        data = _valid_cash_loan_form()
        data["return_rate_custom"] = "35"
        form = _make_form(data)
        parsed = parse_form_data(form)
        errors = validate_form_data(parsed)
        assert "settings.return_rate" in errors

    def test_valid_custom_return_rate(self):
        """Custom return rate within 0-30% produces no error."""
        data = _valid_cash_loan_form()
        data["return_rate_custom"] = "8.5"
        form = _make_form(data)
        parsed = parse_form_data(form)
        errors = validate_form_data(parsed)
        assert "settings.return_rate" not in errors


# --- build_domain_objects tests ---


class TestBuildDomainObjects:
    """Tests for build_domain_objects function."""

    def test_builds_financing_options(self):
        """Build FinancingOption instances from parsed data."""
        form = _make_form(_valid_cash_loan_form())
        parsed = parse_form_data(form)
        options, _settings = build_domain_objects(parsed)
        assert len(options) == 2
        assert options[0].option_type == OptionType.CASH
        assert options[0].label == "Pay in Full"
        assert options[1].option_type == OptionType.TRADITIONAL_LOAN
        assert options[1].purchase_price == Decimal(25000)

    def test_uses_decimal_not_float(self):
        """All monetary and rate values are Decimal, never float."""
        form = _make_form(_valid_cash_loan_form())
        parsed = parse_form_data(form)
        options, settings = build_domain_objects(parsed)
        assert isinstance(options[1].apr, Decimal)
        assert isinstance(options[1].purchase_price, Decimal)
        assert isinstance(settings.return_rate, Decimal)

    def test_converts_percentage_to_decimal(self):
        """APR "5.99" is converted to Decimal("5.99") / 100."""
        form = _make_form(_valid_cash_loan_form())
        parsed = parse_form_data(form)
        options, _settings = build_domain_objects(parsed)
        assert options[1].apr == Decimal("5.99") / Decimal(100)

    def test_custom_return_rate_overrides_preset(self):
        """Custom return rate takes precedence over preset radio."""
        data = _valid_cash_loan_form()
        data["return_rate_custom"] = "8.5"
        form = _make_form(data)
        parsed = parse_form_data(form)
        _options, settings = build_domain_objects(parsed)
        assert settings.return_rate == Decimal("8.5") / Decimal(100)

    def test_preset_return_rate_used_when_no_custom(self):
        """Preset return rate is used when custom is empty."""
        form = _make_form(_valid_cash_loan_form())
        parsed = parse_form_data(form)
        _options, settings = build_domain_objects(parsed)
        assert settings.return_rate == Decimal("0.07")

    def test_inflation_defaults_when_enabled(self):
        """Inflation defaults to 3% when enabled but no custom rate."""
        data = _valid_cash_loan_form()
        data["inflation_enabled"] = "1"
        form = _make_form(data)
        parsed = parse_form_data(form)
        _options, settings = build_domain_objects(parsed)
        assert settings.inflation_enabled is True
        assert settings.inflation_rate == Decimal(3) / Decimal(100)

    def test_tax_defaults_when_enabled(self):
        """Tax defaults to 22% when enabled but no custom rate."""
        data = _valid_cash_loan_form()
        data["tax_enabled"] = "1"
        form = _make_form(data)
        parsed = parse_form_data(form)
        _options, settings = build_domain_objects(parsed)
        assert settings.tax_enabled is True
        assert settings.tax_rate == Decimal(22) / Decimal(100)

    def test_builds_promo_option_fields(self):
        """Promo zero percent fields are correctly mapped."""
        form = _make_form(
            {
                "purchase_price": "10000",
                "options[0][type]": "promo_zero_percent",
                "options[0][label]": "Promo",
                "options[0][term_months]": "12",
                "options[0][post_promo_apr]": "24.99",
                "options[0][deferred_interest]": "1",
                "return_preset": "0.07",
            }
        )
        parsed = parse_form_data(form)
        options, _settings = build_domain_objects(parsed)
        assert options[0].option_type == OptionType.PROMO_ZERO_PERCENT
        assert options[0].term_months == 12
        assert options[0].post_promo_apr == Decimal("24.99") / Decimal(100)
        assert options[0].deferred_interest is True
