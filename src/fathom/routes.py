"""
Route definitions for the Fathom web application.

Provides the main blueprint with the index page route, HTMX partial
endpoints for option type switching and add/remove, and the form
submission handler that validates and calls the calculation engine.
"""

from __future__ import annotations

from flask import Blueprint, current_app, render_template, request
from pydantic import ValidationError

from fathom.charts import prepare_charts
from fathom.engine import compare
from fathom.forms import (
    build_domain_objects,
    extract_form_data,
    parse_form_data,
    pydantic_errors_to_dict,
)
from fathom.models import OptionType
from fathom.results import analyze_results

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


def _build_template_context(
    parsed_data: dict,
    errors: dict[str, str],
    results: object = None,
) -> dict:
    """
    Construct the full template context from parsed form data.

    Ensures every option has its template path set and all values are
    passed through for repopulation after form submission.

    Args:
        parsed_data: The structured dict from extract_form_data.
        errors: Validation errors dict (may be empty).
        results: Optional ComparisonResult from the engine.

    Returns:
        A dict suitable for passing to render_template as kwargs.

    """
    options = []
    for i, opt in enumerate(parsed_data["options"]):
        opt_type = opt.get("type", OptionType.CASH.value)
        template = OPTION_FIELD_TEMPLATES.get(
            opt_type,
            OPTION_FIELD_TEMPLATES[OptionType.CASH.value],
        )
        # Build fields dict from option data for template repopulation
        fields = {k: v for k, v in opt.items() if k not in ("type", "label")}
        options.append(
            {
                "idx": i,
                "type": opt_type,
                "label": opt.get("label", ""),
                "fields": fields,
                "template": template,
            },
        )

    ctx: dict = {
        "purchase_price": parsed_data["purchase_price"],
        "options": options,
        "option_types": _build_option_types(),
        "settings": parsed_data["settings"],
        "errors": errors,
    }
    if results is not None:
        ctx["results"] = results
    return ctx


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
    fathom_settings = current_app.config["FATHOM_SETTINGS"]
    return render_template(
        "index.html",
        purchase_price="",
        options=_build_default_options(),
        option_types=_build_option_types(),
        settings={
            "return_preset": str(fathom_settings.default_return_rate),
            "return_rate_custom": "",
            "inflation_enabled": False,
            "inflation_rate": str(int(fathom_settings.default_inflation_rate * 100)),
            "tax_enabled": False,
            "tax_rate": str(int(fathom_settings.default_tax_rate * 100)),
        },
        errors={},
    )


@bp.route("/partials/option-fields/<int:idx>")
def option_fields(idx: int) -> str:
    """
    Return rendered field template for a given option type (HTMX type switch).

    Reads the selected type from query parameters and renders the
    corresponding field partial with empty values (clean slate).

    Args:
        idx: The option index in the form.

    Returns:
        Rendered HTML for the type-specific fields.

    """
    selected_type = request.args.get(
        f"options[{idx}][type]",
        OptionType.CASH.value,
    )
    template = OPTION_FIELD_TEMPLATES.get(
        selected_type,
        OPTION_FIELD_TEMPLATES[OptionType.CASH.value],
    )
    return render_template(
        template,
        opt={"idx": idx, "fields": {}},
        errors={},
    )


@bp.route("/partials/option/add", methods=["POST"])
def add_option() -> str:
    """
    Add a new financing option to the form (HTMX endpoint).

    Extracts the current form state from hx-include data, appends a new
    Traditional Loan option, and returns the updated option list partial.

    Returns:
        Rendered HTML for the full option list with the new option appended.

    """
    parsed = extract_form_data(request.form)
    next_idx = len(parsed["options"])

    parsed["options"].append(
        {
            "type": OptionType.TRADITIONAL_LOAN.value,
            "label": OPTION_TYPE_LABELS[OptionType.TRADITIONAL_LOAN.value],
            "apr": "",
            "term_months": "",
            "down_payment": "",
            "post_promo_apr": "",
            "deferred_interest": False,
            "cash_back_amount": "",
            "discounted_price": "",
            "custom_label": "",
        },
    )

    options = []
    for i, opt in enumerate(parsed["options"]):
        opt_type = opt.get("type", OptionType.CASH.value)
        template = OPTION_FIELD_TEMPLATES.get(
            opt_type,
            OPTION_FIELD_TEMPLATES[OptionType.CASH.value],
        )
        fields = {k: v for k, v in opt.items() if k not in ("type", "label")}
        options.append(
            {
                "idx": i,
                "type": opt_type,
                "label": opt.get("label", ""),
                "fields": fields,
                "template": template,
            },
        )

    _ = next_idx  # used implicitly via append
    return render_template(
        "partials/option_list.html",
        options=options,
        option_types=_build_option_types(),
        errors={},
    )


@bp.route("/partials/option/<int:idx>/remove", methods=["POST"])
def remove_option(idx: int) -> str:
    """
    Remove a financing option from the form (HTMX endpoint).

    Extracts current form state, removes the option at the given index,
    re-indexes remaining options sequentially, and returns the updated
    option list partial.

    Args:
        idx: The option index to remove.

    Returns:
        Rendered HTML for the full option list without the removed option.

    """
    parsed = extract_form_data(request.form)

    # Remove the option at the given index (idx maps to parsed list position)
    if 0 <= idx < len(parsed["options"]):
        parsed["options"].pop(idx)

    options = []
    for i, opt in enumerate(parsed["options"]):
        opt_type = opt.get("type", OptionType.CASH.value)
        template = OPTION_FIELD_TEMPLATES.get(
            opt_type,
            OPTION_FIELD_TEMPLATES[OptionType.CASH.value],
        )
        fields = {k: v for k, v in opt.items() if k not in ("type", "label")}
        options.append(
            {
                "idx": i,
                "type": opt_type,
                "label": opt.get("label", ""),
                "fields": fields,
                "template": template,
            },
        )

    return render_template(
        "partials/option_list.html",
        options=options,
        option_types=_build_option_types(),
        errors={},
    )


@bp.route("/compare", methods=["POST"])
def compare_options() -> str:
    """
    Handle form submission for comparing financing options.

    Parses and validates the form data. If validation fails, re-renders
    the page with inline errors and repopulated values. If valid, calls
    the calculation engine and renders results.

    Returns:
        Rendered HTML for the full index page with results or errors.

    """
    is_htmx = request.headers.get("HX-Request") == "true"

    try:
        form_input = parse_form_data(request.form)
    except ValidationError as exc:
        errors = pydantic_errors_to_dict(exc)
        parsed = extract_form_data(request.form)
        ctx = _build_template_context(parsed, errors)
        ctx["has_errors"] = True
        if is_htmx:
            return render_template("partials/results.html", **ctx)
        return render_template("index.html", **ctx)

    parsed = extract_form_data(request.form)
    financing_options, global_settings = build_domain_objects(form_input)
    results = compare(financing_options, global_settings)

    ctx = _build_template_context(parsed, errors={}, results=results)
    display_data = analyze_results(results, financing_options)
    # Charts expect sorted_options as (name, cost) tuples
    chart_display = dict(display_data)
    chart_display["sorted_options"] = [
        (opt["name"], opt["result"].true_total_cost)
        for opt in display_data["options_data"]
    ]
    chart_data = prepare_charts(results, chart_display)
    ctx["display"] = display_data
    ctx["charts"] = chart_data
    if is_htmx:
        return render_template("partials/results.html", **ctx)
    return render_template("index.html", **ctx)
