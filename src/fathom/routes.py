"""
Route definitions for the Fathom web application.

Provides the main blueprint with the index page route, HTMX partial
endpoints for option type switching and add/remove, and the form
submission handler that validates and calls the calculation engine.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from flask import Blueprint, Response, current_app, render_template, request
from pydantic import ValidationError

from fathom.charts import prepare_charts
from fathom.engine import compare

if TYPE_CHECKING:
    from werkzeug.datastructures import ImmutableMultiDict

    from fathom.config import Settings
from fathom.forms import (
    FormInput,
    build_domain_objects,
    extract_form_data,
    form_data_to_export_dict,
    parse_form_data,
    pydantic_errors_to_dict,
)
from fathom.models import GlobalSettings, OptionType
from fathom.results import analyze_results, build_compare_data, build_detailed_breakdown
from fathom.tax_brackets import TAX_BRACKETS_2025

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
            "return_preset": f"{fathom_settings.default_return_rate:.2f}",
            "return_rate_custom": "",
            "inflation_enabled": False,
            "inflation_rate": str(int(fathom_settings.default_inflation_rate * 100)),
            "tax_enabled": False,
            "tax_rate": str(int(fathom_settings.default_tax_rate * 100)),
        },
        errors={},
        tax_brackets=TAX_BRACKETS_2025,
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
        ctx["tax_brackets"] = TAX_BRACKETS_2025
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
    ctx["tax_brackets"] = TAX_BRACKETS_2025
    # Build detailed breakdown for initial tab render
    detail_breakdown = build_detailed_breakdown(
        display_data["options_data"],
        results.comparison_period_months,
        global_settings,
    )
    ctx["detail_breakdown"] = detail_breakdown
    ctx["global_settings"] = global_settings
    if is_htmx:
        return render_template("partials/results.html", **ctx)
    return render_template("index.html", **ctx)


_detail_parse_errors = (ValidationError, ValueError)


def _process_form_for_detail(
    form: ImmutableMultiDict,
) -> tuple[list[dict], int, GlobalSettings]:
    """
    Parse form data and run the comparison engine for detail endpoints.

    Shared logic for the detail tab and compare HTMX endpoints.

    Args:
        form: The request form data.

    Returns:
        Tuple of (options_data, comparison_period_months, global_settings).

    """
    form_input = parse_form_data(form)
    financing_options, global_settings = build_domain_objects(form_input)
    results = compare(financing_options, global_settings)
    display_data = analyze_results(results, financing_options)
    return (
        display_data["options_data"],
        results.comparison_period_months,
        global_settings,
    )


@bp.route("/partials/detail/<int:idx>", methods=["POST"])
def detail_tab(idx: int) -> str:
    """
    Return the detailed period table for a specific option (HTMX).

    Parses form data, runs the engine, and renders the detailed
    table partial for the option at the given index.

    Args:
        idx: The option index (0-based).

    Returns:
        Rendered HTML for the detailed table partial, or error message.

    """
    granularity = request.args.get("granularity", "monthly")
    try:
        options_data, period_months, settings = _process_form_for_detail(request.form)
    except _detail_parse_errors:
        return "<p>Unable to load detail view. Please submit the form first.</p>"

    if idx < 0 or idx >= len(options_data):
        return "<p>Option not found.</p>"

    breakdown = build_detailed_breakdown(
        options_data,
        period_months,
        settings,
        granularity,
    )
    return render_template(
        "partials/results/detailed_table.html",
        detail=breakdown[idx],
        granularity=granularity,
        global_settings=settings,
    )


@bp.route("/partials/detail/compare", methods=["POST"])
def detail_compare() -> str:
    """
    Return the compare tab table for side-by-side option comparison (HTMX).

    Parses form data, runs the engine, and renders the compare
    table partial with payment and cumulative cost per option.

    Returns:
        Rendered HTML for the compare table partial.

    """
    granularity = request.args.get("granularity", "monthly")
    try:
        options_data, period_months, settings = _process_form_for_detail(request.form)
    except _detail_parse_errors:
        return "<p>Unable to load compare view. Please submit the form first.</p>"

    _ = settings  # not needed for compare
    compare_data = build_compare_data(options_data, period_months, granularity)
    # Compute per-option payment totals for footer
    compare_totals: list[dict] = []
    if compare_data:
        num_options = len(compare_data[0]["options"])
        for oi in range(num_options):
            total_payment = sum(
                row["options"][oi]["payment"]
                for row in compare_data
                if oi < len(row["options"])
            )
            last_cumulative = compare_data[-1]["options"][oi]["cumulative"]
            compare_totals.append(
                {"payment": total_payment, "cumulative": last_cumulative},
            )
    return render_template(
        "partials/results/detailed_compare.html",
        compare_rows=compare_data,
        compare_totals=compare_totals,
        options_data=options_data,
        granularity=granularity,
    )


@bp.route("/export", methods=["POST"])
def export_data() -> Response:
    """
    Export current form inputs as a downloadable JSON file.

    Reads form data from the POST request, builds a versioned export
    dict, and returns it as a JSON file attachment with a date-stamped
    filename.

    Returns:
        A Flask Response with the JSON file as an attachment.

    """
    parsed = extract_form_data(request.form)
    export = form_data_to_export_dict(parsed)
    json_str = json.dumps(export, separators=(",", ":"))
    filename = f"fathom-{datetime.now(tz=UTC).date().isoformat()}.json"
    return Response(
        json_str,
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


_MAX_IMPORT_SIZE = 65536  # 64 KB


@bp.route("/import", methods=["POST"])
def import_data() -> str:
    """
    Import form inputs from an uploaded JSON file.

    Validates the uploaded file, parses the JSON, validates field values
    via the Pydantic FormInput model, and re-renders the form with the
    imported values populated. Shows appropriate errors for missing files,
    malformed JSON, or invalid field values.

    Returns:
        Rendered HTML for the full index page with imported values or errors.

    """
    fathom_settings = current_app.config["FATHOM_SETTINGS"]
    import_file = request.files.get("import_file")

    if not import_file or not import_file.filename:
        return _render_import_error(
            "Please select a JSON file to import.",
            fathom_settings,
        )

    content_length = request.content_length or 0
    if content_length > _MAX_IMPORT_SIZE:
        return _render_import_error(
            "The selected file is too large. Maximum size is 64 KB.",
            fathom_settings,
        )

    _json_parse_errors = (json.JSONDecodeError, UnicodeDecodeError)
    try:
        data = json.load(import_file.stream)
    except _json_parse_errors:
        return _render_import_error(
            "The selected file is not a valid Fathom export. "
            "Please select a .json file previously exported from Fathom.",
            fathom_settings,
        )

    if not isinstance(data, dict):
        return _render_import_error(
            "The selected file is not a valid Fathom export. "
            "Please select a .json file previously exported from Fathom.",
            fathom_settings,
        )

    # Remove version key (used for future migration, not for validation)
    data.pop("version", None)

    # Inject purchase_price into each option (same as parse_form_data does)
    purchase_price = data.get("purchase_price", "")
    for opt in data.get("options", []):
        opt["purchase_price"] = purchase_price

    try:
        FormInput.model_validate(data)
    except ValidationError as exc:
        errors = pydantic_errors_to_dict(exc)
        ctx = _build_template_context(data, errors)
        ctx["has_errors"] = True
        ctx["tax_brackets"] = TAX_BRACKETS_2025
        return render_template("index.html", **ctx)

    ctx = _build_template_context(data, {})
    ctx["tax_brackets"] = TAX_BRACKETS_2025
    return render_template("index.html", **ctx)


def _render_import_error(message: str, fathom_settings: Settings) -> str:
    """
    Re-render the index page with an import error and default form state.

    Args:
        message: The error message to display.
        fathom_settings: The application's FATHOM_SETTINGS config object.

    Returns:
        Rendered HTML for the index page with the import error.

    """
    return render_template(
        "index.html",
        purchase_price="",
        options=_build_default_options(),
        option_types=_build_option_types(),
        settings={
            "return_preset": f"{fathom_settings.default_return_rate:.2f}",
            "return_rate_custom": "",
            "inflation_enabled": False,
            "inflation_rate": str(int(fathom_settings.default_inflation_rate * 100)),
            "tax_enabled": False,
            "tax_rate": str(int(fathom_settings.default_tax_rate * 100)),
        },
        errors={},
        import_error=message,
        tax_brackets=TAX_BRACKETS_2025,
    )
