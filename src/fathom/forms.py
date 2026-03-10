"""
Form parsing, validation, and domain model construction for Fathom.

Handles extraction of POST data from Flask's ImmutableMultiDict into
structured dicts, validates all fields with type-specific range checks,
and converts validated data into domain model instances using Decimal.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING

from fathom.models import FinancingOption, GlobalSettings, OptionType

if TYPE_CHECKING:
    from werkzeug.datastructures import ImmutableMultiDict

# Fields that are checkboxes (present=True, absent=False)
_CHECKBOX_FIELDS = {"deferred_interest"}

# All extractable per-option fields
_OPTION_FIELDS = (
    "type",
    "label",
    "apr",
    "term_months",
    "down_payment",
    "post_promo_apr",
    "deferred_interest",
    "cash_back_amount",
    "discounted_price",
    "custom_label",
)

# Regex to find option indices in form keys
_OPTION_INDEX_RE = re.compile(r"options\[(\d+)\]")


def parse_form_data(form_data: ImmutableMultiDict) -> dict:
    """
    Extract structured data from a Flask form submission.

    Parses purchase_price, a list of financing options (indexed fields),
    and global settings from the submitted form data.

    Args:
        form_data: The ImmutableMultiDict from request.form.

    Returns:
        A dict with keys ``purchase_price``, ``options``, and ``settings``.

    """
    purchase_price = form_data.get("purchase_price", "")

    # Discover which option indices are present
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
    try:
        return Decimal(value.strip())
    except InvalidOperation:
        return None


def validate_form_data(parsed: dict) -> dict[str, str]:
    """
    Validate parsed form data and return a dict of error messages.

    Returns an empty dict when all data is valid. Error keys use dot
    notation (e.g., ``options.0.apr``, ``settings.return_rate``).

    Args:
        parsed: The structured dict from parse_form_data.

    Returns:
        A dict mapping field keys to error message strings.

    """
    errors: dict[str, str] = {}

    # Validate purchase price
    pp_str = parsed["purchase_price"]
    pp_val = _try_decimal(pp_str)
    if pp_val is None:
        errors["purchase_price"] = "Purchase price is required and must be a number."
    elif pp_val <= 0:
        errors["purchase_price"] = "Purchase price must be greater than zero."

    # Validate each option based on its type
    for i, opt in enumerate(parsed["options"]):
        opt_type = opt.get("type", "")
        prefix = f"options.{i}"
        _validate_option(opt, opt_type, prefix, pp_val, errors)

    # Validate return rate
    _validate_return_rate(parsed["settings"], errors)

    return errors


def _validate_option(
    opt: dict,
    opt_type: str,
    prefix: str,
    purchase_price: Decimal | None,
    errors: dict[str, str],
) -> None:
    """
    Validate a single option's fields based on its type.

    Args:
        opt: The option dict from parsed data.
        opt_type: The option type string value.
        prefix: The error key prefix (e.g., "options.0").
        purchase_price: The validated purchase price, or None if invalid.
        errors: The errors dict to populate.

    """
    if opt_type == OptionType.CASH.value:
        return

    # Types that require APR
    apr_required = opt_type in {
        OptionType.TRADITIONAL_LOAN.value,
        OptionType.PROMO_CASH_BACK.value,
        OptionType.PROMO_PRICE_REDUCTION.value,
        OptionType.CUSTOM.value,
    }

    if apr_required:
        apr_val = _try_decimal(opt.get("apr", ""))
        if apr_val is None:
            errors[f"{prefix}.apr"] = "APR is required."
        elif apr_val < 0 or apr_val > 40:
            errors[f"{prefix}.apr"] = "APR must be between 0% and 40%."

    # All non-cash types require term_months
    term_str = opt.get("term_months", "")
    if term_str and term_str.strip():
        try:
            term_val = int(term_str)
        except ValueError:
            errors[f"{prefix}.term_months"] = "Term must be a whole number."
            term_val = None
        else:
            if term_val < 1 or term_val > 360:
                errors[f"{prefix}.term_months"] = (
                    "Term must be between 1 and 360 months."
                )
    else:
        errors[f"{prefix}.term_months"] = "Term is required."

    # Down payment (optional for all types that have it)
    dp_str = opt.get("down_payment", "")
    if dp_str and dp_str.strip():
        dp_val = _try_decimal(dp_str)
        if dp_val is None:
            errors[f"{prefix}.down_payment"] = "Down payment must be a number."
        elif dp_val < 0:
            errors[f"{prefix}.down_payment"] = "Down payment must not be negative."
        elif purchase_price is not None and dp_val > purchase_price:
            errors[f"{prefix}.down_payment"] = (
                "Down payment cannot exceed purchase price."
            )

    # Promo-specific validations
    if opt_type == OptionType.PROMO_ZERO_PERCENT.value:
        ppa_str = opt.get("post_promo_apr", "")
        if ppa_str and ppa_str.strip():
            ppa_val = _try_decimal(ppa_str)
            if ppa_val is None:
                errors[f"{prefix}.post_promo_apr"] = "Post-promo APR must be a number."
            elif ppa_val < 0 or ppa_val > 40:
                errors[f"{prefix}.post_promo_apr"] = (
                    "Post-promo APR must be between 0% and 40%."
                )

    if opt_type == OptionType.PROMO_CASH_BACK.value:
        cb_str = opt.get("cash_back_amount", "")
        cb_val = _try_decimal(cb_str)
        if cb_val is None:
            errors[f"{prefix}.cash_back_amount"] = "Cash-back amount is required."
        elif cb_val <= 0:
            errors[f"{prefix}.cash_back_amount"] = (
                "Cash-back amount must be greater than zero."
            )

    if opt_type == OptionType.PROMO_PRICE_REDUCTION.value:
        dp_price_str = opt.get("discounted_price", "")
        dp_price_val = _try_decimal(dp_price_str)
        if dp_price_val is None:
            errors[f"{prefix}.discounted_price"] = "Discounted price is required."
        elif dp_price_val <= 0:
            errors[f"{prefix}.discounted_price"] = (
                "Discounted price must be greater than zero."
            )
        elif purchase_price is not None and dp_price_val >= purchase_price:
            errors[f"{prefix}.discounted_price"] = (
                "Discounted price must be less than purchase price."
            )


def _validate_return_rate(
    settings: dict,
    errors: dict[str, str],
) -> None:
    """
    Validate the return rate setting.

    Custom rate takes precedence. If provided, it must be a valid number
    between 0 and 30. If no custom rate, the preset must be one of the
    allowed values.

    Args:
        settings: The settings dict from parsed data.
        errors: The errors dict to populate.

    """
    custom = settings.get("return_rate_custom", "")
    if custom and custom.strip():
        val = _try_decimal(custom)
        if val is None:
            errors["settings.return_rate"] = "Custom return rate must be a number."
        elif val < 0 or val > 30:
            errors["settings.return_rate"] = "Return rate must be between 0% and 30%."
    else:
        preset = settings.get("return_preset", "")
        if preset not in {"0.04", "0.07", "0.10"}:
            errors["settings.return_rate"] = "Please select a return rate."


def build_domain_objects(
    parsed: dict,
) -> tuple[list[FinancingOption], GlobalSettings]:
    """
    Convert validated parsed form data into domain model instances.

    All monetary and rate values use Decimal arithmetic. Percentage inputs
    from the form (e.g., APR "5.99") are divided by 100 for engine use.

    Args:
        parsed: The validated structured dict from parse_form_data.

    Returns:
        A tuple of (list of FinancingOption, GlobalSettings).

    """
    purchase_price = Decimal(parsed["purchase_price"])
    options: list[FinancingOption] = []

    for opt in parsed["options"]:
        option_type = OptionType(opt["type"])
        label = opt.get("label", "") or option_type.value

        apr = _to_rate(opt.get("apr", ""))
        term_months = _to_int(opt.get("term_months", ""))
        down_payment = _to_money(opt.get("down_payment", ""))
        post_promo_apr = _to_rate(opt.get("post_promo_apr", ""))
        deferred_interest = bool(opt.get("deferred_interest"))
        cash_back_amount = _to_money(opt.get("cash_back_amount", ""))
        discounted_price = _to_money(opt.get("discounted_price", ""))

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
                cash_back_amount=cash_back_amount,
                discounted_price=discounted_price,
            ),
        )

    # Resolve return rate: custom > preset > default 0.07
    settings_data = parsed["settings"]
    custom_rate = settings_data.get("return_rate_custom", "")
    if custom_rate and custom_rate.strip():
        return_rate = Decimal(custom_rate.strip()) / Decimal(100)
    else:
        preset = settings_data.get("return_preset", "0.07")
        return_rate = Decimal(preset)

    inflation_enabled = bool(settings_data.get("inflation_enabled"))
    inflation_rate_str = settings_data.get("inflation_rate", "3")
    inflation_rate = (
        Decimal(inflation_rate_str) / Decimal(100)
        if inflation_rate_str and inflation_rate_str.strip()
        else Decimal(3) / Decimal(100)
    )

    tax_enabled = bool(settings_data.get("tax_enabled"))
    tax_rate_str = settings_data.get("tax_rate", "22")
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

    Args:
        value: The percentage string (e.g., "5.99").

    Returns:
        Decimal rate or None if empty/invalid.

    """
    if not value or not value.strip():
        return None
    try:
        return Decimal(value.strip()) / Decimal(100)
    except InvalidOperation:
        return None


def _to_money(value: str) -> Decimal | None:
    """
    Convert a money string to a Decimal.

    Args:
        value: The money string (e.g., "5000").

    Returns:
        Decimal amount or None if empty/invalid.

    """
    if not value or not value.strip():
        return None
    try:
        return Decimal(value.strip())
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
