"""
Route definitions for the Fathom web application.

Provides the main blueprint with the index page route and supporting
constants for option type display names and field templates.
"""

from flask import Blueprint, render_template

from fathom.models import OptionType

bp = Blueprint("main", __name__)

OPTION_TYPE_LABELS: dict[str, str] = {
    OptionType.CASH.value: "Pay in Full (Cash)",
    OptionType.TRADITIONAL_LOAN.value: "Traditional Loan",
    OptionType.PROMO_ZERO_PERCENT.value: "0% Promotional Financing",
    OptionType.PROMO_CASH_BACK.value: "Promo with Cash-Back Rebate",
    OptionType.PROMO_PRICE_REDUCTION.value: "Promo with Price Reduction",
    OptionType.CUSTOM.value: "Custom / Other",
}

OPTION_FIELD_TEMPLATES: dict[str, str] = {
    OptionType.CASH.value: "partials/option_fields/cash.html",
    OptionType.TRADITIONAL_LOAN.value: "partials/option_fields/traditional.html",
    OptionType.PROMO_ZERO_PERCENT.value: "partials/option_fields/promo_zero.html",
    OptionType.PROMO_CASH_BACK.value: "partials/option_fields/promo_cashback.html",
    OptionType.PROMO_PRICE_REDUCTION.value: "partials/option_fields/promo_price.html",
    OptionType.CUSTOM.value: "partials/option_fields/custom.html",
}


def _build_option_types() -> list[dict[str, str]]:
    """
    Build the list of option type choices for template dropdowns.

    Returns:
        A list of dicts with ``value`` and ``label`` keys for each option type.

    """
    return [
        {"value": ot.value, "label": OPTION_TYPE_LABELS[ot.value]} for ot in OptionType
    ]


def _build_default_options() -> list[dict[str, object]]:
    """
    Build the default options shown on initial page load.

    Returns:
        A list of two option dicts: Cash and Traditional Loan.

    """
    return [
        {
            "idx": 0,
            "type": OptionType.CASH.value,
            "label": "Pay in Full",
            "fields": {},
            "template": OPTION_FIELD_TEMPLATES[OptionType.CASH.value],
        },
        {
            "idx": 1,
            "type": OptionType.TRADITIONAL_LOAN.value,
            "label": "Traditional Loan",
            "fields": {},
            "template": OPTION_FIELD_TEMPLATES[OptionType.TRADITIONAL_LOAN.value],
        },
    ]


@bp.route("/")
def index() -> str:
    """
    Render the main comparison form page.

    Serves the complete HTML form with purchase price input, two default
    financing option cards (Cash and Traditional Loan), and collapsed
    global settings with sensible defaults.

    Returns:
        Rendered HTML for the index page.

    """
    return render_template(
        "index.html",
        purchase_price="",
        options=_build_default_options(),
        option_types=_build_option_types(),
        settings={
            "return_preset": "0.07",
            "return_rate_custom": "",
            "inflation_enabled": False,
            "inflation_rate": "3",
            "tax_enabled": False,
            "tax_rate": "22",
        },
        errors={},
    )
