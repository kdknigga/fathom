"""
Unit tests for form parsing, validation, and domain model construction.

Tests cover parse_form_data, extract_form_data, build_domain_objects,
and pydantic_errors_to_dict from the fathom.forms module.
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError
from werkzeug.datastructures import ImmutableMultiDict

from fathom.formatting import comma_format
from fathom.forms import (
    FormInput,
    OptionInput,
    _to_money,
    _try_decimal,
    build_domain_objects,
    extract_form_data,
    parse_form_data,
    pydantic_errors_to_dict,
)
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


def _get_errors(data: dict[str, str]) -> dict[str, str]:
    """Parse form data and return validation errors as a dict."""
    form = _make_form(data)
    try:
        parse_form_data(form)
    except ValidationError as exc:
        return pydantic_errors_to_dict(exc)
    return {}


# --- parse_form_data tests ---


class TestParseFormData:
    """Tests for parse_form_data function."""

    def test_returns_form_input(self):
        """Valid form data returns a FormInput instance."""
        form = _make_form(_valid_cash_loan_form())
        result = parse_form_data(form)
        assert result.purchase_price == "25000"

    def test_extracts_options(self):
        """Parse indexed option fields into a list."""
        form = _make_form(_valid_cash_loan_form())
        result = parse_form_data(form)
        assert len(result.options) == 2
        assert result.options[0].type == "cash"
        assert result.options[1].type == "traditional_loan"
        assert result.options[1].apr == "5.99"
        assert result.options[1].term_months == "36"

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
            },
        )
        result = parse_form_data(form)
        assert len(result.options) == 2
        assert result.options[0].type == "cash"
        assert result.options[1].type == "traditional_loan"

    def test_extracts_settings(self):
        """Parse global settings from form data."""
        form = _make_form(
            {
                **_valid_cash_loan_form(),
                "inflation_enabled": "1",
                "tax_enabled": "1",
            },
        )
        result = parse_form_data(form)
        assert result.settings.return_preset == "0.07"
        assert result.settings.inflation_enabled is True
        assert result.settings.tax_enabled is True
        assert result.settings.inflation_rate == "3"
        assert result.settings.tax_rate == "22"

    def test_checkbox_defaults_false(self):
        """Unchecked checkboxes default to False."""
        form = _make_form(_valid_cash_loan_form())
        result = parse_form_data(form)
        assert result.settings.inflation_enabled is False
        assert result.settings.tax_enabled is False

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
                "options[1][type]": "cash",
                "options[1][label]": "Cash",
                "return_preset": "0.07",
            },
        )
        result = parse_form_data(form)
        opt = result.options[0]
        assert opt.post_promo_apr == "24.99"
        assert opt.deferred_interest is True

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
            },
        )
        result = parse_form_data(form)
        assert result.options[0].cash_back_amount == "500"
        assert result.options[1].discounted_price == "22000"

    def test_raises_validation_error_on_invalid(self):
        """Invalid form data raises ValidationError."""
        form = _make_form({**_valid_cash_loan_form(), "purchase_price": ""})
        try:
            parse_form_data(form)
            pytest.fail("Should have raised ValidationError")
        except ValidationError:
            pass


# --- extract_form_data tests ---


class TestExtractFormData:
    """Tests for extract_form_data function."""

    def test_returns_dict(self):
        """extract_form_data returns a plain dict."""
        form = _make_form(_valid_cash_loan_form())
        result = extract_form_data(form)
        assert isinstance(result, dict)
        assert "purchase_price" in result
        assert "options" in result
        assert "settings" in result

    def test_extracts_purchase_price(self):
        """Extract purchase price from form data."""
        form = _make_form({"purchase_price": "25000"})
        result = extract_form_data(form)
        assert result["purchase_price"] == "25000"

    def test_extracts_options(self):
        """Extract indexed option fields into a list of dicts."""
        form = _make_form(_valid_cash_loan_form())
        result = extract_form_data(form)
        assert len(result["options"]) == 2
        assert result["options"][0]["type"] == "cash"
        assert result["options"][1]["type"] == "traditional_loan"


# --- validate_form_data tests (via parse + pydantic_errors_to_dict) ---


class TestValidateFormData:
    """Tests for validation via parse_form_data and pydantic_errors_to_dict."""

    def test_valid_data_returns_empty(self):
        """Valid form data produces no errors."""
        errors = _get_errors(_valid_cash_loan_form())
        assert errors == {}

    def test_empty_purchase_price(self):
        """Empty purchase price produces an error."""
        errors = _get_errors({**_valid_cash_loan_form(), "purchase_price": ""})
        assert "purchase_price" in errors

    def test_non_numeric_purchase_price(self):
        """Non-numeric purchase price produces an error."""
        errors = _get_errors({**_valid_cash_loan_form(), "purchase_price": "abc"})
        assert "purchase_price" in errors

    def test_zero_purchase_price(self):
        """Zero purchase price produces an error."""
        errors = _get_errors({**_valid_cash_loan_form(), "purchase_price": "0"})
        assert "purchase_price" in errors

    def test_apr_out_of_range(self):
        """APR above 40% produces an error."""
        data = _valid_cash_loan_form()
        data["options[1][apr]"] = "41"
        errors = _get_errors(data)
        assert "options.1.apr" in errors

    def test_term_months_out_of_range(self):
        """Term months outside 1-360 produces an error."""
        data = _valid_cash_loan_form()
        data["options[1][term_months]"] = "0"
        errors = _get_errors(data)
        assert "options.1.term_months" in errors

    def test_term_months_too_high(self):
        """Term months above 360 produces an error."""
        data = _valid_cash_loan_form()
        data["options[1][term_months]"] = "361"
        errors = _get_errors(data)
        assert "options.1.term_months" in errors

    def test_down_payment_exceeds_price(self):
        """Down payment exceeding purchase price produces an error."""
        data = _valid_cash_loan_form()
        data["options[1][down_payment]"] = "30000"
        errors = _get_errors(data)
        assert "options.1.down_payment" in errors

    def test_cash_skips_apr_validation(self):
        """Cash option does not require or validate APR."""
        errors = _get_errors(_valid_cash_loan_form())
        assert "options.0.apr" not in errors

    def test_promo_zero_requires_term(self):
        """Promo zero percent requires term_months."""
        errors = _get_errors(
            {
                "purchase_price": "10000",
                "options[0][type]": "promo_zero_percent",
                "options[0][label]": "Promo",
                "options[1][type]": "cash",
                "options[1][label]": "Cash",
                "return_preset": "0.07",
            },
        )
        assert "options.0.term_months" in errors

    def test_promo_cashback_requires_amount(self):
        """Promo cash back requires cash_back_amount."""
        errors = _get_errors(
            {
                "purchase_price": "10000",
                "options[0][type]": "promo_cash_back",
                "options[0][label]": "CB",
                "options[0][apr]": "5",
                "options[0][term_months]": "24",
                "options[1][type]": "cash",
                "options[1][label]": "Cash",
                "return_preset": "0.07",
            },
        )
        assert "options.0.cash_back_amount" in errors

    def test_promo_price_requires_discounted_price(self):
        """Promo price reduction requires discounted_price."""
        errors = _get_errors(
            {
                "purchase_price": "25000",
                "options[0][type]": "promo_price_reduction",
                "options[0][label]": "Price Cut",
                "options[0][apr]": "6",
                "options[0][term_months]": "36",
                "options[1][type]": "cash",
                "options[1][label]": "Cash",
                "return_preset": "0.07",
            },
        )
        assert "options.0.discounted_price" in errors

    def test_discounted_price_must_be_less_than_purchase(self):
        """Discounted price >= purchase price produces an error."""
        errors = _get_errors(
            {
                "purchase_price": "25000",
                "options[0][type]": "promo_price_reduction",
                "options[0][label]": "Price Cut",
                "options[0][apr]": "6",
                "options[0][term_months]": "36",
                "options[0][discounted_price]": "25000",
                "options[1][type]": "cash",
                "options[1][label]": "Cash",
                "return_preset": "0.07",
            },
        )
        assert "options.0.discounted_price" in errors

    def test_custom_return_rate_override(self):
        """Custom return rate with invalid value produces an error."""
        data = _valid_cash_loan_form()
        data["return_rate_custom"] = "35"
        errors = _get_errors(data)
        assert "settings.return_rate" in errors

    def test_valid_custom_return_rate(self):
        """Custom return rate within 0-30% produces no error."""
        data = _valid_cash_loan_form()
        data["return_rate_custom"] = "8.5"
        errors = _get_errors(data)
        assert "settings.return_rate" not in errors

    def test_error_message_purchase_price(self):
        """Purchase price error message matches expected text."""
        errors = _get_errors({**_valid_cash_loan_form(), "purchase_price": ""})
        assert (
            errors["purchase_price"]
            == "Purchase price is required and must be a number."
        )

    def test_error_message_apr_required(self):
        """APR required error message matches expected text."""
        data = _valid_cash_loan_form()
        data["options[1][apr]"] = ""
        errors = _get_errors(data)
        assert errors["options.1.apr"] == "APR is required."

    def test_error_message_term_required(self):
        """Term required error message matches expected text."""
        data = _valid_cash_loan_form()
        data["options[1][term_months]"] = ""
        errors = _get_errors(data)
        assert errors["options.1.term_months"] == "Term is required."


# --- build_domain_objects tests ---


class TestBuildDomainObjects:
    """Tests for build_domain_objects function."""

    def test_builds_financing_options(self):
        """Build FinancingOption instances from validated form data."""
        form = _make_form(_valid_cash_loan_form())
        form_input = parse_form_data(form)
        options, _settings = build_domain_objects(form_input)
        assert len(options) == 2
        assert options[0].option_type == OptionType.CASH
        assert options[0].label == "Pay in Full"
        assert options[1].option_type == OptionType.TRADITIONAL_LOAN
        assert options[1].purchase_price == Decimal(25000)

    def test_uses_decimal_not_float(self):
        """All monetary and rate values are Decimal, never float."""
        form = _make_form(_valid_cash_loan_form())
        form_input = parse_form_data(form)
        options, settings = build_domain_objects(form_input)
        assert isinstance(options[1].apr, Decimal)
        assert isinstance(options[1].purchase_price, Decimal)
        assert isinstance(settings.return_rate, Decimal)

    def test_converts_percentage_to_decimal(self):
        """APR "5.99" is converted to Decimal("5.99") / 100."""
        form = _make_form(_valid_cash_loan_form())
        form_input = parse_form_data(form)
        options, _settings = build_domain_objects(form_input)
        assert options[1].apr == Decimal("5.99") / Decimal(100)

    def test_custom_return_rate_overrides_preset(self):
        """Custom return rate takes precedence over preset radio."""
        data = _valid_cash_loan_form()
        data["return_rate_custom"] = "8.5"
        form = _make_form(data)
        form_input = parse_form_data(form)
        _options, settings = build_domain_objects(form_input)
        assert settings.return_rate == Decimal("8.5") / Decimal(100)

    def test_preset_return_rate_used_when_no_custom(self):
        """Preset return rate is used when custom is empty."""
        form = _make_form(_valid_cash_loan_form())
        form_input = parse_form_data(form)
        _options, settings = build_domain_objects(form_input)
        assert settings.return_rate == Decimal("0.07")

    def test_inflation_defaults_when_enabled(self):
        """Inflation defaults to 3% when enabled but no custom rate."""
        data = _valid_cash_loan_form()
        data["inflation_enabled"] = "1"
        form = _make_form(data)
        form_input = parse_form_data(form)
        _options, settings = build_domain_objects(form_input)
        assert settings.inflation_enabled is True
        assert settings.inflation_rate == Decimal(3) / Decimal(100)

    def test_tax_defaults_when_enabled(self):
        """Tax defaults to 22% when enabled but no custom rate."""
        data = _valid_cash_loan_form()
        data["tax_enabled"] = "1"
        form = _make_form(data)
        form_input = parse_form_data(form)
        _options, settings = build_domain_objects(form_input)
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
                "options[1][type]": "cash",
                "options[1][label]": "Cash",
                "return_preset": "0.07",
            },
        )
        form_input = parse_form_data(form)
        options, _settings = build_domain_objects(form_input)
        assert options[0].option_type == OptionType.PROMO_ZERO_PERCENT
        assert options[0].term_months == 12
        assert options[0].post_promo_apr == Decimal("24.99") / Decimal(100)
        assert options[0].deferred_interest is True

    def test_retroactive_interest_passed_when_deferred(self):
        """build_domain_objects passes retroactive_interest=True when deferred_interest checked."""
        form = _make_form(
            {
                "purchase_price": "10000",
                "options[0][type]": "promo_zero_percent",
                "options[0][label]": "Promo",
                "options[0][term_months]": "12",
                "options[0][deferred_interest]": "1",
                "options[0][retroactive_interest]": "1",
                "options[1][type]": "cash",
                "options[1][label]": "Cash",
                "return_preset": "0.07",
            },
        )
        form_input = parse_form_data(form)
        options, _settings = build_domain_objects(form_input)
        assert options[0].retroactive_interest is True

    def test_retroactive_interest_false_when_deferred_unchecked(self):
        """build_domain_objects passes retroactive_interest=False when deferred_interest unchecked."""
        form = _make_form(
            {
                "purchase_price": "10000",
                "options[0][type]": "promo_zero_percent",
                "options[0][label]": "Promo",
                "options[0][term_months]": "12",
                "options[1][type]": "cash",
                "options[1][label]": "Cash",
                "return_preset": "0.07",
            },
        )
        form_input = parse_form_data(form)
        options, _settings = build_domain_objects(form_input)
        assert options[0].retroactive_interest is False


# --- Retroactive interest cross-field validation tests ---


class TestRetroactiveInterestValidation:
    """Tests for retroactive_interest cross-field validation on OptionInput."""

    def test_retroactive_with_deferred_and_promo_zero(self):
        """retroactive_interest=True with deferred_interest=True and promo_zero validates."""
        opt = OptionInput(
            type=OptionType.PROMO_ZERO_PERCENT.value,
            retroactive_interest=True,
            deferred_interest=True,
            term_months="12",
            purchase_price="10000",
        )
        assert opt.retroactive_interest is True

    def test_retroactive_reset_when_deferred_false(self):
        """retroactive_interest silently resets to False when deferred_interest=False."""
        opt = OptionInput(
            type=OptionType.PROMO_ZERO_PERCENT.value,
            retroactive_interest=True,
            deferred_interest=False,
            term_months="12",
            purchase_price="10000",
        )
        assert opt.retroactive_interest is False

    def test_retroactive_reset_when_not_promo_zero(self):
        """retroactive_interest silently resets to False when type is not promo_zero_percent."""
        opt = OptionInput(
            type=OptionType.TRADITIONAL_LOAN.value,
            retroactive_interest=True,
            deferred_interest=True,
            apr="5",
            term_months="36",
            purchase_price="10000",
        )
        assert opt.retroactive_interest is False


# --- Option count validation tests ---


class TestOptionCountValidation:
    """Tests for FormInput option count validation."""

    def test_one_option_rejected(self):
        """FormInput with 1 option raises ValidationError containing '2 and 4'."""
        try:
            FormInput(
                purchase_price="10000",
                options=[
                    OptionInput(
                        type=OptionType.CASH.value,
                        purchase_price="10000",
                    ),
                ],
                settings={"return_preset": "0.07"},
            )
            pytest.fail("Should have raised ValidationError")
        except ValidationError as exc:
            error_str = str(exc)
            assert "2 and 4" in error_str

    def test_five_options_rejected(self):
        """FormInput with 5 options raises ValidationError containing '2 and 4'."""
        opts = [
            OptionInput(type=OptionType.CASH.value, purchase_price="10000")
            for _ in range(5)
        ]
        try:
            FormInput(
                purchase_price="10000",
                options=opts,
                settings={"return_preset": "0.07"},
            )
            pytest.fail("Should have raised ValidationError")
        except ValidationError as exc:
            error_str = str(exc)
            assert "2 and 4" in error_str

    def test_two_options_valid(self):
        """FormInput with 2 options validates successfully."""
        form = FormInput(
            purchase_price="10000",
            options=[
                OptionInput(type=OptionType.CASH.value, purchase_price="10000"),
                OptionInput(
                    type=OptionType.TRADITIONAL_LOAN.value,
                    apr="5",
                    term_months="36",
                    purchase_price="10000",
                ),
            ],
            settings={"return_preset": "0.07"},
        )
        assert len(form.options) == 2

    def test_four_options_valid(self):
        """FormInput with 4 options validates successfully."""
        opts = [
            OptionInput(type=OptionType.CASH.value, purchase_price="10000")
            for _ in range(4)
        ]
        form = FormInput(
            purchase_price="10000",
            options=opts,
            settings={"return_preset": "0.07"},
        )
        assert len(form.options) == 4


# --- Comma handling tests ---


class TestCommaHandling:
    """Tests for comma/dollar stripping in parsing and comma_format rendering."""

    # _try_decimal with commas and dollar signs

    def test_try_decimal_strips_commas(self):
        """_try_decimal('25,000') returns Decimal('25000')."""
        assert _try_decimal("25,000") == Decimal(25000)

    def test_try_decimal_strips_dollar_and_commas(self):
        """_try_decimal('$100,000.50') returns Decimal('100000.50')."""
        assert _try_decimal("$100,000.50") == Decimal("100000.50")

    def test_try_decimal_strips_multiple_commas(self):
        """_try_decimal('1,000,000') returns Decimal('1000000')."""
        assert _try_decimal("1,000,000") == Decimal(1000000)

    def test_try_decimal_strips_dollar_and_spaces(self):
        """_try_decimal('$ 25,000') returns Decimal('25000')."""
        assert _try_decimal("$ 25,000") == Decimal(25000)

    def test_try_decimal_empty_returns_none(self):
        """_try_decimal('') returns None (existing behavior)."""
        assert _try_decimal("") is None

    def test_try_decimal_invalid_returns_none(self):
        """_try_decimal('abc') returns None (existing behavior)."""
        assert _try_decimal("abc") is None

    # _to_money with commas and dollar signs

    def test_to_money_strips_commas(self):
        """_to_money('25,000') returns Decimal('25000')."""
        assert _to_money("25,000") == Decimal(25000)

    def test_to_money_strips_dollar_and_commas(self):
        """_to_money('$50,000.99') returns Decimal('50000.99')."""
        assert _to_money("$50,000.99") == Decimal("50000.99")

    # comma_format function

    def test_comma_format_integer(self):
        """comma_format('25000') returns '25,000'."""
        assert comma_format("25000") == "25,000"

    def test_comma_format_decimal(self):
        """comma_format('25000.50') returns '25,000.50'."""
        assert comma_format("25000.50") == "25,000.50"

    def test_comma_format_trailing_zero(self):
        """comma_format('25000.10') returns '25,000.10' (trailing zero preserved)."""
        assert comma_format("25000.10") == "25,000.10"

    def test_comma_format_empty(self):
        """comma_format('') returns ''."""
        assert comma_format("") == ""

    def test_comma_format_invalid(self):
        """comma_format('abc') returns 'abc' (passthrough)."""
        assert comma_format("abc") == "abc"

    def test_comma_format_idempotent(self):
        """comma_format('25,000') returns '25,000' (already formatted)."""
        assert comma_format("25,000") == "25,000"

    # FormInput validator returns cleaned string

    def test_purchase_price_validator_cleans_commas(self):
        """FormInput purchase_price validator strips commas for downstream Decimal()."""
        form = FormInput(
            purchase_price="25,000",
            options=[
                OptionInput(type=OptionType.CASH.value, purchase_price="25,000"),
                OptionInput(
                    type=OptionType.TRADITIONAL_LOAN.value,
                    apr="5",
                    term_months="36",
                    purchase_price="25,000",
                ),
            ],
            settings={"return_preset": "0.07"},
        )
        assert form.purchase_price == "25000"

    # Full form submission round-trip with commas

    def test_full_submission_with_commas(self):
        """Submit form with comma values, verify correct ComparisonResult."""
        form_data = _make_form(
            {
                "purchase_price": "25,000",
                "options[0][type]": "cash",
                "options[0][label]": "Pay in Full",
                "options[1][type]": "traditional_loan",
                "options[1][label]": "Bank Loan",
                "options[1][apr]": "5.99",
                "options[1][term_months]": "36",
                "options[1][down_payment]": "5,000",
                "return_preset": "0.07",
                "return_rate_custom": "",
                "inflation_rate": "3",
                "tax_rate": "22",
            },
        )
        form_input = parse_form_data(form_data)
        options, _settings = build_domain_objects(form_input)
        assert options[0].purchase_price == Decimal(25000)
        assert options[1].down_payment == Decimal(5000)


# --- Export dict tests ---


class TestExportDict:
    """Tests for form_data_to_export_dict function."""

    def test_adds_version_field(self):
        """Export dict includes version: 1."""
        from fathom.forms import form_data_to_export_dict

        parsed = {
            "purchase_price": "25000",
            "options": [
                {"type": "cash", "label": "Cash", "deferred_interest": False},
                {
                    "type": "traditional_loan",
                    "label": "Loan",
                    "apr": "5.99",
                    "term_months": "36",
                    "deferred_interest": False,
                    "retroactive_interest": False,
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
        result = form_data_to_export_dict(parsed)
        assert result["version"] == 1

    def test_includes_all_sections(self):
        """Export dict includes purchase_price, options, and settings."""
        from fathom.forms import form_data_to_export_dict

        parsed = {
            "purchase_price": "10000",
            "options": [
                {"type": "cash", "label": "Pay in Full", "deferred_interest": False},
                {
                    "type": "traditional_loan",
                    "label": "Loan",
                    "apr": "6",
                    "term_months": "24",
                    "deferred_interest": False,
                    "retroactive_interest": False,
                },
            ],
            "settings": {
                "return_preset": "0.07",
                "return_rate_custom": "",
                "inflation_enabled": True,
                "inflation_rate": "3",
                "tax_enabled": False,
                "tax_rate": "22",
            },
        }
        result = form_data_to_export_dict(parsed)
        assert result["purchase_price"] == "10000"
        assert len(result["options"]) == 2
        assert result["settings"]["inflation_enabled"] is True

    def test_booleans_are_native(self):
        """Export dict preserves native Python booleans, not strings."""
        from fathom.forms import form_data_to_export_dict

        parsed = {
            "purchase_price": "10000",
            "options": [
                {"type": "cash", "label": "Cash", "deferred_interest": False},
                {
                    "type": "traditional_loan",
                    "label": "Loan",
                    "apr": "5",
                    "term_months": "12",
                    "deferred_interest": True,
                    "retroactive_interest": False,
                },
            ],
            "settings": {
                "return_preset": "0.07",
                "return_rate_custom": "",
                "inflation_enabled": False,
                "inflation_rate": "3",
                "tax_enabled": True,
                "tax_rate": "22",
            },
        }
        result = form_data_to_export_dict(parsed)
        assert isinstance(result["settings"]["tax_enabled"], bool)
        assert result["settings"]["tax_enabled"] is True
        assert isinstance(result["options"][1]["deferred_interest"], bool)
        assert result["options"][1]["deferred_interest"] is True


# --- Inflation rate validation tests ---


class TestInflationRateValidation:
    """Tests for inflation rate bounds validation on SettingsInput."""

    def test_valid_inflation_rate(self):
        """SettingsInput with inflation_enabled=True, inflation_rate='3' validates without error."""
        from fathom.forms import SettingsInput

        s = SettingsInput(inflation_enabled=True, inflation_rate="3")
        assert s.inflation_rate == "3"

    def test_inflation_rate_at_bounds(self):
        """inflation_rate='0' and '20' both pass validation."""
        from fathom.forms import SettingsInput

        s0 = SettingsInput(inflation_enabled=True, inflation_rate="0")
        assert s0.inflation_rate == "0"
        s20 = SettingsInput(inflation_enabled=True, inflation_rate="20")
        assert s20.inflation_rate == "20"

    def test_inflation_rate_below_zero(self):
        """inflation_rate='-1' raises ValueError with bounds message."""
        from fathom.forms import SettingsInput

        with pytest.raises(ValidationError, match="between 0% and 20%"):
            SettingsInput(inflation_enabled=True, inflation_rate="-1")

    def test_inflation_rate_above_twenty(self):
        """inflation_rate='21' raises ValueError with bounds message."""
        from fathom.forms import SettingsInput

        with pytest.raises(ValidationError, match="between 0% and 20%"):
            SettingsInput(inflation_enabled=True, inflation_rate="21")

    def test_inflation_rate_non_numeric(self):
        """inflation_rate='abc' raises ValueError with 'Must be a number'."""
        from fathom.forms import SettingsInput

        with pytest.raises(ValidationError, match="Must be a number"):
            SettingsInput(inflation_enabled=True, inflation_rate="abc")

    def test_inflation_rate_skipped_when_disabled(self):
        """inflation_enabled=False, inflation_rate='999' validates without error."""
        from fathom.forms import SettingsInput

        s = SettingsInput(inflation_enabled=False, inflation_rate="999")
        assert s.inflation_rate == "999"


# --- Tax rate validation tests ---


class TestTaxRateValidation:
    """Tests for tax rate bounds validation on SettingsInput."""

    def test_valid_tax_rate(self):
        """SettingsInput with tax_enabled=True, tax_rate='22' validates without error."""
        from fathom.forms import SettingsInput

        s = SettingsInput(tax_enabled=True, tax_rate="22")
        assert s.tax_rate == "22"

    def test_tax_rate_at_bounds(self):
        """tax_rate='0' and '60' both pass validation."""
        from fathom.forms import SettingsInput

        s0 = SettingsInput(tax_enabled=True, tax_rate="0")
        assert s0.tax_rate == "0"
        s60 = SettingsInput(tax_enabled=True, tax_rate="60")
        assert s60.tax_rate == "60"

    def test_tax_rate_below_zero(self):
        """tax_rate='-1' raises ValueError with bounds message."""
        from fathom.forms import SettingsInput

        with pytest.raises(ValidationError, match="between 0% and 60%"):
            SettingsInput(tax_enabled=True, tax_rate="-1")

    def test_tax_rate_above_sixty(self):
        """tax_rate='61' raises ValueError with bounds message."""
        from fathom.forms import SettingsInput

        with pytest.raises(ValidationError, match="between 0% and 60%"):
            SettingsInput(tax_enabled=True, tax_rate="61")

    def test_tax_rate_non_numeric(self):
        """tax_rate='abc' raises ValueError with 'Must be a number'."""
        from fathom.forms import SettingsInput

        with pytest.raises(ValidationError, match="Must be a number"):
            SettingsInput(tax_enabled=True, tax_rate="abc")

    def test_tax_rate_skipped_when_disabled(self):
        """tax_enabled=False, tax_rate='999' validates without error."""
        from fathom.forms import SettingsInput

        s = SettingsInput(tax_enabled=False, tax_rate="999")
        assert s.tax_rate == "999"
