"""
Form parsing, validation, and domain model construction for Fathom.

Handles extraction of POST data from Flask's ImmutableMultiDict,
validates all fields using Pydantic models with type-specific range
checks, and converts validated data into domain model instances.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, ValidationError, field_validator, model_validator

from fathom.models import FinancingOption, GlobalSettings, OptionType

if TYPE_CHECKING:
    from werkzeug.datastructures import ImmutableMultiDict

# Fields that are checkboxes (present=True, absent=False)
_CHECKBOX_FIELDS = {"deferred_interest", "retroactive_interest"}

# All extractable per-option fields
_OPTION_FIELDS = (
    "type",
    "label",
    "apr",
    "term_months",
    "down_payment",
    "post_promo_apr",
    "deferred_interest",
    "retroactive_interest",
    "cash_back_amount",
    "discounted_price",
    "custom_label",
)

# Regex to find option indices in form keys
_OPTION_INDEX_RE = re.compile(r"options\[(\d+)\]")


def _try_decimal(value: str) -> Decimal | None:
    """
    Attempt to convert a string to Decimal.

    Args:
        value: The string to convert.

    Returns:
        A Decimal if conversion succeeds, None otherwise.

    """
    if not value or not value.strip():
        return None
    cleaned = value.strip().replace("$", "").replace(",", "").replace(" ", "")
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _clean_monetary(value: str) -> str:
    """
    Strip dollar signs, commas, and spaces from a monetary string.

    Args:
        value: Raw monetary input string.

    Returns:
        Cleaned string suitable for Decimal conversion.

    """
    return value.strip().replace("$", "").replace(",", "").replace(" ", "")


# ---------------------------------------------------------------------------
# Pydantic validation models
# ---------------------------------------------------------------------------


class SettingsInput(BaseModel):
    """
    Validates global settings from form input.

    Custom return rate takes precedence over the preset radio selection.
    """

    return_preset: str = "0.07"
    return_rate_custom: str = ""
    inflation_enabled: bool = False
    inflation_rate: str = "3"
    tax_enabled: bool = False
    tax_rate: str = "22"

    @model_validator(mode="after")
    def validate_return_rate(self) -> Self:
        """Validate the return rate setting."""
        custom = self.return_rate_custom
        if custom and custom.strip():
            val = _try_decimal(custom)
            if val is None:
                msg = "return_rate:Custom return rate must be a number."
                raise ValueError(msg)
            if val < 0 or val > 30:
                msg = "return_rate:Return rate must be between 0% and 30%."
                raise ValueError(msg)
        else:
            preset = self.return_preset
            if preset not in {"0.04", "0.07", "0.10"}:
                msg = "return_rate:Please select a return rate."
                raise ValueError(msg)
        return self


def _validate_apr(opt: OptionInput, errors: list[str]) -> None:
    """
    Validate APR field for option types that require it.

    Checks that APR is present and within the 0-40% range for
    traditional loans, promo cash-back, promo price reduction,
    and custom option types.

    Args:
        opt: The option input being validated.
        errors: List to append error messages to.

    """
    apr_required_types = {
        OptionType.TRADITIONAL_LOAN.value,
        OptionType.PROMO_CASH_BACK.value,
        OptionType.PROMO_PRICE_REDUCTION.value,
        OptionType.CUSTOM.value,
    }
    if opt.type not in apr_required_types:
        return
    apr_val = _try_decimal(opt.apr)
    if apr_val is None:
        errors.append("apr:APR is required.")
    elif apr_val < 0 or apr_val > 40:
        errors.append("apr:APR must be between 0% and 40%.")


def _validate_term_months(opt: OptionInput, errors: list[str]) -> None:
    """
    Validate term_months field for all non-cash option types.

    Ensures term is present, is a whole number, and falls within
    the 1-360 month range.

    Args:
        opt: The option input being validated.
        errors: List to append error messages to.

    """
    term_str = opt.term_months
    if not term_str or not term_str.strip():
        errors.append("term_months:Term is required.")
        return
    try:
        term_val = int(term_str)
    except ValueError:
        errors.append("term_months:Term must be a whole number.")
        return
    if term_val < 1 or term_val > 360:
        errors.append("term_months:Term must be between 1 and 360 months.")


def _validate_down_payment(opt: OptionInput, errors: list[str]) -> None:
    """
    Validate optional down payment field.

    When provided, checks that the value is a valid non-negative number
    that does not exceed the purchase price.

    Args:
        opt: The option input being validated.
        errors: List to append error messages to.

    """
    dp_str = opt.down_payment
    if not dp_str or not dp_str.strip():
        return
    dp_val = _try_decimal(dp_str)
    pp_val = _try_decimal(opt.purchase_price)
    if dp_val is None:
        errors.append("down_payment:Down payment must be a number.")
    elif dp_val < 0:
        errors.append("down_payment:Down payment must not be negative.")
    elif pp_val is not None and dp_val > pp_val:
        errors.append("down_payment:Down payment cannot exceed purchase price.")


def _validate_promo_fields(opt: OptionInput, errors: list[str]) -> None:
    """
    Validate promo-specific fields based on option type.

    Handles post-promo APR for zero-percent promos, cash-back amount
    for cash-back promos, and discounted price for price reduction promos.

    Args:
        opt: The option input being validated.
        errors: List to append error messages to.

    """
    opt_type = opt.type
    if opt_type == OptionType.PROMO_ZERO_PERCENT.value:
        _validate_post_promo_apr(opt, errors)
    elif opt_type == OptionType.PROMO_CASH_BACK.value:
        _validate_cash_back(opt, errors)
    elif opt_type == OptionType.PROMO_PRICE_REDUCTION.value:
        _validate_discounted_price(opt, errors)


def _validate_post_promo_apr(opt: OptionInput, errors: list[str]) -> None:
    """
    Validate optional post-promo APR for zero-percent promo options.

    Args:
        opt: The option input being validated.
        errors: List to append error messages to.

    """
    ppa_str = opt.post_promo_apr
    if not ppa_str or not ppa_str.strip():
        return
    ppa_val = _try_decimal(ppa_str)
    if ppa_val is None:
        errors.append("post_promo_apr:Post-promo APR must be a number.")
    elif ppa_val < 0 or ppa_val > 40:
        errors.append("post_promo_apr:Post-promo APR must be between 0% and 40%.")


def _validate_cash_back(opt: OptionInput, errors: list[str]) -> None:
    """
    Validate cash-back amount for cash-back promo options.

    Args:
        opt: The option input being validated.
        errors: List to append error messages to.

    """
    cb_val = _try_decimal(opt.cash_back_amount)
    if cb_val is None:
        errors.append("cash_back_amount:Cash-back amount is required.")
    elif cb_val <= 0:
        errors.append("cash_back_amount:Cash-back amount must be greater than zero.")


def _validate_discounted_price(opt: OptionInput, errors: list[str]) -> None:
    """
    Validate discounted price for price reduction promo options.

    Args:
        opt: The option input being validated.
        errors: List to append error messages to.

    """
    dp_price_val = _try_decimal(opt.discounted_price)
    pp_val = _try_decimal(opt.purchase_price)
    if dp_price_val is None:
        errors.append("discounted_price:Discounted price is required.")
    elif dp_price_val <= 0:
        errors.append("discounted_price:Discounted price must be greater than zero.")
    elif pp_val is not None and dp_price_val >= pp_val:
        errors.append(
            "discounted_price:Discounted price must be less than purchase price.",
        )


class OptionInput(BaseModel):
    """
    Validates a single financing option from form input.

    All fields stored as raw strings. Type-dependent validation performed
    in the model_validator to replicate existing per-type checks.
    """

    type: str
    label: str = ""
    apr: str = ""
    term_months: str = ""
    down_payment: str = ""
    post_promo_apr: str = ""
    deferred_interest: bool = False
    retroactive_interest: bool = False
    cash_back_amount: str = ""
    discounted_price: str = ""
    custom_label: str = ""
    purchase_price: str = ""

    @model_validator(mode="after")
    def validate_by_type(self) -> Self:
        """
        Type-dependent field validation matching existing rules.

        Collects all field-level errors and raises them together.
        Error messages are prefixed with ``field_name:`` so that
        ``pydantic_errors_to_dict`` can remap the loc correctly.
        """
        opt_type = self.type
        if opt_type == OptionType.CASH.value:
            return self

        errors: list[str] = []
        _validate_apr(self, errors)
        _validate_term_months(self, errors)
        _validate_down_payment(self, errors)
        _validate_promo_fields(self, errors)

        if errors:
            msg = "\n".join(errors)
            raise ValueError(msg)

        # Silently reset retroactive_interest when not applicable
        if self.retroactive_interest and (
            not self.deferred_interest
            or opt_type != OptionType.PROMO_ZERO_PERCENT.value
        ):
            self.retroactive_interest = False

        return self


class FormInput(BaseModel):
    """
    Top-level form validation model.

    Contains purchase price, a list of financing options, and global
    settings. Enforces option count constraints (2-4).
    """

    purchase_price: str
    options: list[OptionInput]
    settings: SettingsInput

    @field_validator("purchase_price")
    @classmethod
    def validate_purchase_price(cls, v: str) -> str:
        """Validate that purchase price is a positive number."""
        val = _try_decimal(v)
        if val is None:
            msg = "Purchase price is required and must be a number."
            raise ValueError(msg)
        if val <= 0:
            msg = "Purchase price must be greater than zero."
            raise ValueError(msg)
        return _clean_monetary(v)

    @field_validator("options")
    @classmethod
    def validate_option_count(cls, v: list[OptionInput]) -> list[OptionInput]:
        """Enforce 2-4 financing options for comparison."""
        if len(v) < 2 or len(v) > 4:
            msg = "Please compare between 2 and 4 financing options."
            raise ValueError(msg)
        return v


# ---------------------------------------------------------------------------
# Error conversion helper
# ---------------------------------------------------------------------------


def pydantic_errors_to_dict(exc: ValidationError) -> dict[str, str]:
    """
    Convert a Pydantic ValidationError to a template-compatible error dict.

    Converts loc tuples to dot-notation strings matching the existing
    error key format (e.g., ``options.0.apr``, ``settings.return_rate``).

    Handles field-prefixed messages from model_validators: messages
    of the form ``field_name:User message`` are remapped so the error
    key includes the field suffix and the user-facing message is clean.

    Args:
        exc: The Pydantic ValidationError to convert.

    Returns:
        A dict mapping field keys to error message strings.

    """
    errors: dict[str, str] = {}
    for err in exc.errors():
        loc_parts = err["loc"]
        base_key = ".".join(str(part) for part in loc_parts)
        msg = err["msg"]
        msg = msg.removeprefix("Value error, ")

        # Handle multi-error messages from model_validators
        # (newline-separated "field:message" pairs)
        if "\n" in msg:
            for raw_line in msg.split("\n"):
                line = raw_line.strip()
                if not line:
                    continue
                if ":" in line:
                    field, field_msg = line.split(":", 1)
                    full_key = f"{base_key}.{field}" if base_key else field
                    errors[full_key] = field_msg
                elif base_key:
                    errors[base_key] = line
        elif ":" in msg and not msg.startswith(("Purchase", "Custom")):
            # Single field-prefixed message from model_validator
            field, field_msg = msg.split(":", 1)
            full_key = f"{base_key}.{field}" if base_key else field
            errors[full_key] = field_msg
        elif base_key:
            errors[base_key] = msg

    return errors


# ---------------------------------------------------------------------------
# Export helper
# ---------------------------------------------------------------------------


def form_data_to_export_dict(parsed: dict) -> dict:
    """
    Build a versioned export dict from parsed form data.

    Adds a ``version`` field for forward compatibility and passes through
    purchase_price, options, and settings unchanged. Booleans from
    ``extract_form_data`` are already native Python bools.

    Args:
        parsed: The structured dict from extract_form_data.

    Returns:
        A dict suitable for JSON serialization with a version field.

    """
    return {
        "version": 1,
        "purchase_price": parsed["purchase_price"],
        "options": parsed["options"],
        "settings": parsed["settings"],
    }


# ---------------------------------------------------------------------------
# Form data extraction (no validation)
# ---------------------------------------------------------------------------


def extract_form_data(form_data: ImmutableMultiDict) -> dict:
    """
    Extract structured data from a Flask form submission without validation.

    Parses purchase_price, a list of financing options (indexed fields),
    and global settings from the submitted form data. Used by add/remove
    routes that need form restructuring without validation.

    Args:
        form_data: The ImmutableMultiDict from request.form.

    Returns:
        A dict with keys ``purchase_price``, ``options``, and ``settings``.

    """
    purchase_price = form_data.get("purchase_price", "")

    indices: set[int] = set()
    for key in form_data:
        match = _OPTION_INDEX_RE.match(key)
        if match:
            indices.add(int(match.group(1)))

    options: list[dict] = []
    for idx in sorted(indices):
        opt: dict = {}
        for field_name in _OPTION_FIELDS:
            key = f"options[{idx}][{field_name}]"
            if field_name in _CHECKBOX_FIELDS:
                opt[field_name] = key in form_data
            else:
                opt[field_name] = form_data.get(key, "")
        options.append(opt)

    settings = {
        "return_preset": form_data.get("return_preset", "0.07"),
        "return_rate_custom": form_data.get("return_rate_custom", ""),
        "inflation_enabled": "inflation_enabled" in form_data,
        "inflation_rate": form_data.get("inflation_rate", "3"),
        "tax_enabled": "tax_enabled" in form_data,
        "tax_rate": form_data.get("tax_rate", "22"),
    }

    return {
        "purchase_price": purchase_price,
        "options": options,
        "settings": settings,
    }


# ---------------------------------------------------------------------------
# Form parsing with Pydantic validation
# ---------------------------------------------------------------------------


def parse_form_data(form_data: ImmutableMultiDict) -> FormInput:
    """
    Extract and validate structured data from a Flask form submission.

    Parses purchase_price, a list of financing options (indexed fields),
    and global settings from the submitted form data. Returns a validated
    FormInput model or raises ``pydantic.ValidationError``.

    Args:
        form_data: The ImmutableMultiDict from request.form.

    Returns:
        A validated FormInput model instance.

    Raises:
        pydantic.ValidationError: If any field fails validation.

    """
    purchase_price = form_data.get("purchase_price", "")

    indices: set[int] = set()
    for key in form_data:
        match = _OPTION_INDEX_RE.match(key)
        if match:
            indices.add(int(match.group(1)))

    options: list[dict[str, object]] = []
    for idx in sorted(indices):
        opt: dict[str, object] = {}
        for field_name in _OPTION_FIELDS:
            key = f"options[{idx}][{field_name}]"
            if field_name in _CHECKBOX_FIELDS:
                opt[field_name] = key in form_data
            else:
                opt[field_name] = form_data.get(key, "")
        opt["purchase_price"] = purchase_price
        options.append(opt)

    settings_data = {
        "return_preset": form_data.get("return_preset", "0.07"),
        "return_rate_custom": form_data.get("return_rate_custom", ""),
        "inflation_enabled": "inflation_enabled" in form_data,
        "inflation_rate": form_data.get("inflation_rate", "3"),
        "tax_enabled": "tax_enabled" in form_data,
        "tax_rate": form_data.get("tax_rate", "22"),
    }

    return FormInput.model_validate(
        {
            "purchase_price": purchase_price,
            "options": options,
            "settings": settings_data,
        },
    )


# ---------------------------------------------------------------------------
# Domain object construction
# ---------------------------------------------------------------------------


def build_domain_objects(
    form: FormInput,
) -> tuple[list[FinancingOption], GlobalSettings]:
    """
    Convert validated form data into domain model instances.

    All monetary and rate values use Decimal arithmetic. Percentage inputs
    from the form (e.g., APR "5.99") are divided by 100 for engine use.

    Args:
        form: The validated FormInput from parse_form_data.

    Returns:
        A tuple of (list of FinancingOption, GlobalSettings).

    """
    purchase_price = Decimal(form.purchase_price)
    options: list[FinancingOption] = []

    for opt in form.options:
        option_type = OptionType(opt.type)
        label = opt.label or option_type.value

        apr = _to_rate(opt.apr)
        term_months = _to_int(opt.term_months)
        down_payment = _to_money(opt.down_payment)
        post_promo_apr = _to_rate(opt.post_promo_apr)
        deferred_interest = bool(opt.deferred_interest)
        retroactive_interest = bool(opt.retroactive_interest) and deferred_interest
        cash_back_amount = _to_money(opt.cash_back_amount)
        discounted_price = _to_money(opt.discounted_price)

        options.append(
            FinancingOption(
                option_type=option_type,
                label=label,
                purchase_price=purchase_price,
                apr=apr,
                term_months=term_months,
                down_payment=down_payment,
                post_promo_apr=post_promo_apr,
                deferred_interest=deferred_interest,
                retroactive_interest=retroactive_interest,
                cash_back_amount=cash_back_amount,
                discounted_price=discounted_price,
            ),
        )

    # Resolve return rate: custom > preset > default 0.07
    settings = form.settings
    custom_rate = settings.return_rate_custom
    if custom_rate and custom_rate.strip():
        return_rate = Decimal(custom_rate.strip()) / Decimal(100)
    else:
        preset = settings.return_preset
        return_rate = Decimal(preset)

    inflation_enabled = bool(settings.inflation_enabled)
    inflation_rate_str = settings.inflation_rate
    inflation_rate = (
        Decimal(inflation_rate_str) / Decimal(100)
        if inflation_rate_str and inflation_rate_str.strip()
        else Decimal(3) / Decimal(100)
    )

    tax_enabled = bool(settings.tax_enabled)
    tax_rate_str = settings.tax_rate
    tax_rate = (
        Decimal(tax_rate_str) / Decimal(100)
        if tax_rate_str and tax_rate_str.strip()
        else Decimal(22) / Decimal(100)
    )

    global_settings = GlobalSettings(
        return_rate=return_rate,
        inflation_enabled=inflation_enabled,
        inflation_rate=inflation_rate,
        tax_enabled=tax_enabled,
        tax_rate=tax_rate,
    )

    return options, global_settings


def _to_rate(value: str) -> Decimal | None:
    """
    Convert a percentage string to a Decimal rate (divided by 100).

    Strips dollar signs, commas, and spaces for consistency.

    Args:
        value: The percentage string (e.g., "5.99").

    Returns:
        Decimal rate or None if empty/invalid.

    """
    if not value or not value.strip():
        return None
    cleaned = _clean_monetary(value)
    if not cleaned:
        return None
    try:
        return Decimal(cleaned) / Decimal(100)
    except InvalidOperation:
        return None


def _to_money(value: str) -> Decimal | None:
    """
    Convert a money string to a Decimal.

    Strips dollar signs, commas, and spaces before conversion.

    Args:
        value: The money string (e.g., "5000", "$5,000", "5,000.99").

    Returns:
        Decimal amount or None if empty/invalid.

    """
    if not value or not value.strip():
        return None
    cleaned = _clean_monetary(value)
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _to_int(value: str) -> int | None:
    """
    Convert a string to an integer.

    Args:
        value: The string (e.g., "36").

    Returns:
        Integer or None if empty/invalid.

    """
    if not value or not value.strip():
        return None
    try:
        return int(value.strip())
    except ValueError:
        return None
