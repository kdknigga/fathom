"""
Results analysis module for display-ready data preparation.

Transforms ComparisonResult into structured data for the recommendation
hero card and cost breakdown table. Handles winner detection, savings
calculation, per-option caveat association, and breakdown row generation.
"""

from __future__ import annotations

from decimal import Decimal

from fathom.caveats import generate_caveats
from fathom.models import (
    ComparisonResult,
    FinancingOption,
    GlobalSettings,
    MonthlyDataPoint,
    OptionResult,
    PromoResult,
)

#: Tooltip explanations for each breakdown row label.
#: Each tooltip: definition, why it matters, concrete example.
_TOOLTIP_TEXT: dict[str, str] = {
    "Total Payments": (
        "The sum of all cash you hand over -- down payment plus every monthly"
        " payment. For example, a $10,000 loan with $1,000 down and 36 payments"
        " of $300 means $11,800 in total payments. This is the simplest measure"
        " of what leaves your bank account."
    ),
    "Total Interest": (
        "The extra cost charged by the lender for borrowing money, calculated"
        " from your APR and remaining balance each month. On a $10,000 loan at"
        " 6% APR over 36 months you would pay about $948 in interest. Lower"
        " rates or shorter terms reduce this amount."
    ),
    "Rebates": (
        "Cash-back or price reductions applied to this option that lower your"
        " effective cost. For instance, a $500 cash-back rebate on a $10,000"
        " purchase reduces your net outlay to $9,500. Rebates are subtracted"
        " from the true total cost."
    ),
    "Opportunity Cost": (
        "The investment return you give up by spending cash now instead of"
        " keeping it invested. If you pay $10,000 cash and your investments"
        " earn 7% annually, you forgo roughly $700 the first year. Financing"
        " lets you keep cash invested longer, potentially offsetting interest."
    ),
    "Tax Savings": (
        "The reduction in your tax bill when loan interest is tax-deductible."
        " At a 24% marginal rate, $1,000 of deductible interest saves you $240"
        " in taxes. This lowers the effective cost of financing. Tax savings"
        " are subtracted from the true total cost."
    ),
    "Inflation Adjustment": (
        "The benefit of repaying a loan with dollars that are worth less over"
        " time due to inflation. At 3% inflation, a $300 payment next year is"
        " worth only about $291 in today's dollars. Longer loan terms amplify"
        " this effect, making financing relatively cheaper."
    ),
    "True Total Cost": (
        "The bottom-line cost after accounting for interest, opportunity cost,"
        " tax savings, inflation, and rebates. This is the number to compare"
        " across options -- the lowest true total cost is the best deal when"
        " all financial factors are considered."
    ),
}

#: Cost component labels and their OptionResult attribute names.
_BREAKDOWN_COMPONENTS: list[tuple[str, str]] = [
    ("Total Payments", "total_payments"),
    ("Total Interest", "total_interest"),
    ("Rebates", "rebates"),
    ("Opportunity Cost", "opportunity_cost"),
    ("Tax Savings", "tax_savings"),
    ("Inflation Adjustment", "inflation_adjustment"),
    ("True Total Cost", "true_total_cost"),
]


def _get_effective_cost(result: OptionResult | PromoResult) -> Decimal:
    """
    Extract the effective true total cost for winner comparison.

    For PromoResult, uses the paid_on_time scenario cost.

    Args:
        result: An OptionResult or PromoResult.

    Returns:
        The Decimal true total cost used for ranking.

    """
    if isinstance(result, PromoResult):
        return result.paid_on_time.true_total_cost
    return result.true_total_cost


def _get_primary_result(result: OptionResult | PromoResult) -> OptionResult:
    """
    Extract the primary OptionResult for component access.

    For PromoResult, returns paid_on_time.

    Args:
        result: An OptionResult or PromoResult.

    Returns:
        The primary OptionResult.

    """
    if isinstance(result, PromoResult):
        return result.paid_on_time
    return result


def _build_breakdown_rows(
    options_data: list[dict],
) -> list[dict]:
    """
    Build the cost breakdown rows, filtering out all-zero rows.

    Each row contains a label and a list of values per option. For promo
    options, two values are included (paid_on_time and not_paid_on_time).

    Args:
        options_data: List of option dicts with result data.

    Returns:
        List of row dicts with ``label`` and ``values`` keys.

    """
    rows: list[dict] = []

    for label, attr in _BREAKDOWN_COMPONENTS:
        values: list[dict] = []
        all_zero = True

        for opt in options_data:
            if opt["is_promo"]:
                paid_val = getattr(opt["result"], attr)
                not_paid_val = getattr(opt["not_paid_result"], attr)
                values.append(
                    {
                        "paid": paid_val,
                        "not_paid": not_paid_val,
                        "is_promo": True,
                    },
                )
                if paid_val != Decimal(0) or not_paid_val != Decimal(0):
                    all_zero = False
            else:
                val = getattr(opt["result"], attr)
                values.append(
                    {
                        "value": val,
                        "is_promo": False,
                    },
                )
                if val != Decimal(0):
                    all_zero = False

        if not all_zero:
            rows.append(
                {
                    "label": label,
                    "values": values,
                    "tooltip": _TOOLTIP_TEXT.get(label, ""),
                },
            )

    return rows


def analyze_results(
    comparison: ComparisonResult,
    options: list[FinancingOption],
) -> dict:
    """
    Transform a ComparisonResult into display-ready data.

    Identifies the winner (lowest true total cost), computes savings vs
    runner-up, generates per-option caveats, builds the breakdown rows,
    and prepares options_data for template rendering.

    Args:
        comparison: The engine's ComparisonResult.
        options: The original FinancingOption list (needed for caveat generation).

    Returns:
        A dict with keys: winner_name, winner_cost, runner_up_name, savings,
        winner_caveats, sorted_options, all_results, comparison_period_months,
        all_caveats, breakdown_rows, options_data, recommendation_text.

    """
    # Sort options by effective cost ascending
    sorted_names = sorted(
        comparison.results.keys(),
        key=lambda name: _get_effective_cost(comparison.results[name]),
    )

    winner_name = sorted_names[0]
    winner_cost = _get_effective_cost(comparison.results[winner_name])

    runner_up_name: str | None = None
    if len(sorted_names) > 1:
        runner_up = sorted_names[1]
        runner_up_name = runner_up
        runner_up_cost = _get_effective_cost(comparison.results[runner_up])
        savings = runner_up_cost - winner_cost
    else:
        savings = Decimal(0)

    # Build per-option caveats mapping
    option_map = {opt.label: opt for opt in options}
    per_option_caveats: dict[str, list] = {}
    for name, result in comparison.results.items():
        opt = option_map.get(name)
        if opt is not None:
            per_option_caveats[name] = generate_caveats(opt, result)
        else:
            per_option_caveats[name] = []

    winner_caveats = per_option_caveats.get(winner_name, [])

    # General caveats (cross-option, e.g. opportunity cost dominance)
    per_option_caveat_set = set()
    for cavs in per_option_caveats.values():
        for c in cavs:
            per_option_caveat_set.add(id(c))

    general_caveats = [
        c for c in comparison.caveats if id(c) not in per_option_caveat_set
    ]

    # Build options_data
    options_data: list[dict] = []
    for name in sorted_names:
        result = comparison.results[name]
        is_promo = isinstance(result, PromoResult)
        opt_data: dict = {
            "name": name,
            "is_winner": name == winner_name,
            "is_promo": is_promo,
            "result": _get_primary_result(result),
            "caveats": per_option_caveats.get(name, []),
        }
        if isinstance(result, PromoResult):
            opt_data["not_paid_result"] = result.not_paid_on_time
        options_data.append(opt_data)

    # Build breakdown rows
    breakdown_rows = _build_breakdown_rows(options_data)

    # Generate recommendation text
    recommendation_text = generate_recommendation_text(
        winner_name,
        savings,
        comparison,
    )

    return {
        "winner_name": winner_name,
        "winner_cost": winner_cost,
        "runner_up_name": runner_up_name,
        "savings": savings,
        "winner_caveats": winner_caveats,
        "general_caveats": general_caveats,
        "sorted_options": sorted_names,
        "all_results": comparison.results,
        "comparison_period_months": comparison.comparison_period_months,
        "all_caveats": comparison.caveats,
        "breakdown_rows": breakdown_rows,
        "options_data": options_data,
        "recommendation_text": recommendation_text,
        "per_option_caveats": per_option_caveats,
    }


def generate_recommendation_text(
    winner_name: str,
    savings: Decimal,
    comparison: ComparisonResult,
) -> str:
    """
    Generate a plain-English recommendation sentence.

    Uses simple heuristics based on the winner's option type to produce
    conversational insight text for the hero card.

    Args:
        winner_name: The label of the winning option.
        savings: The savings amount vs runner-up.
        comparison: The ComparisonResult for context.

    Returns:
        A conversational recommendation string.

    """
    result = comparison.results.get(winner_name)
    if result is None:
        return f"{winner_name} is the most cost-effective option."

    is_promo = isinstance(result, PromoResult)

    # Determine option characteristics from cost components
    primary = _get_primary_result(result)

    if primary.total_interest == Decimal(0) and not is_promo:
        # Cash-like option (no interest)
        if primary.opportunity_cost > Decimal(0):
            return (
                f"Paying in full with {winner_name} avoids interest charges, "
                f"even after accounting for the opportunity cost of tying up your cash."
            )
        return (
            f"{winner_name} avoids all interest charges, "
            f"making it the most straightforward and affordable choice."
        )

    if is_promo:
        return (
            f"{winner_name} offers promotional terms that keep your total cost low, "
            f"provided you pay on time to avoid deferred interest penalties."
        )

    # Loan option won (interest charges but still cheapest overall)
    if savings > Decimal(0):
        return (
            f"Financing with {winner_name} keeps your cash invested longer, "
            f"and the investment returns more than offset the interest charges."
        )

    return f"{winner_name} is the most cost-effective option for this purchase."


def _monthly_data_to_rows(
    monthly_data: list[MonthlyDataPoint],
) -> list[dict]:
    """
    Convert monthly data points to row dicts for the detailed table.

    Computes cumulative true total cost as a running sum of per-period
    net cost factors (payment + opportunity_cost - tax_savings +
    inflation_adjustment).

    Args:
        monthly_data: List of MonthlyDataPoint from an OptionResult.

    Returns:
        List of row dicts with period, payment, interest_portion, etc.

    """
    rows: list[dict] = []
    cumulative = Decimal(0)
    for dp in monthly_data:
        net = (
            dp.payment + dp.opportunity_cost - dp.tax_savings + dp.inflation_adjustment
        )
        cumulative += net
        rows.append(
            {
                "period": dp.month,
                "payment": dp.payment,
                "interest_portion": dp.interest_portion,
                "principal_portion": dp.principal_portion,
                "opportunity_cost": dp.opportunity_cost,
                "inflation_adjustment": dp.inflation_adjustment,
                "tax_savings": dp.tax_savings,
                "cumulative_true_total_cost": cumulative,
            },
        )
    return rows


def aggregate_annual(monthly_rows: list[dict]) -> list[dict]:
    """
    Group monthly row dicts into annual chunks.

    Sums payment, interest, principal, opportunity cost, inflation, and
    tax savings per 12-month group. Cumulative true total cost uses the
    last month's value in each group.

    Args:
        monthly_rows: List of monthly row dicts (from _monthly_data_to_rows).

    Returns:
        List of annual row dicts with period as "Year 1", "Year 2", etc.

    """
    if not monthly_rows:
        return []

    annual: list[dict] = []
    year_num = 1
    chunk: list[dict] = []

    for row in monthly_rows:
        chunk.append(row)
        if len(chunk) == 12:
            annual.append(_sum_chunk(chunk, year_num))
            year_num += 1
            chunk = []

    # Handle remaining partial year
    if chunk:
        annual.append(_sum_chunk(chunk, year_num))

    return annual


def _sum_chunk(chunk: list[dict], year_num: int) -> dict:
    """
    Sum a chunk of monthly rows into a single annual row.

    Args:
        chunk: List of monthly row dicts forming one year.
        year_num: The year number (1-based).

    Returns:
        A single annual row dict.

    """
    return {
        "period": f"Year {year_num}",
        "payment": sum(r["payment"] for r in chunk),
        "interest_portion": sum(r["interest_portion"] for r in chunk),
        "principal_portion": sum(r["principal_portion"] for r in chunk),
        "opportunity_cost": sum(r["opportunity_cost"] for r in chunk),
        "inflation_adjustment": sum(r["inflation_adjustment"] for r in chunk),
        "tax_savings": sum(r["tax_savings"] for r in chunk),
        "cumulative_true_total_cost": chunk[-1]["cumulative_true_total_cost"],
    }


def build_detailed_breakdown(
    options_data: list[dict],
    comparison_period_months: int,
    settings: GlobalSettings,
    granularity: str = "monthly",
) -> list[dict]:
    """
    Build detailed period breakdown data for all options.

    Transforms per-option monthly data into structured row dicts
    suitable for the detailed period table. Supports monthly and
    annual granularity.

    Args:
        options_data: List of option dicts from analyze_results.
        comparison_period_months: The comparison period length in months.
        settings: GlobalSettings for feature flag checks.
        granularity: "monthly" or "annual".

    Returns:
        List of per-option dicts with name, is_promo, is_winner, rows,
        totals, and optional not_paid_rows/not_paid_totals.

    """
    _ = comparison_period_months  # reserved for future use
    result_list: list[dict] = []

    for opt in options_data:
        primary_result: OptionResult = opt["result"]
        rows = _monthly_data_to_rows(primary_result.monthly_data)

        if granularity == "annual":
            rows = aggregate_annual(rows)

        totals = _compute_totals(rows)

        entry: dict = {
            "name": opt["name"],
            "is_promo": opt["is_promo"],
            "is_winner": opt["is_winner"],
            "rows": rows,
            "totals": totals,
            "settings": settings,
        }

        if opt["is_promo"] and "not_paid_result" in opt:
            not_paid_result: OptionResult = opt["not_paid_result"]
            not_paid_rows = _monthly_data_to_rows(not_paid_result.monthly_data)
            if granularity == "annual":
                not_paid_rows = aggregate_annual(not_paid_rows)
            entry["not_paid_rows"] = not_paid_rows
            entry["not_paid_totals"] = _compute_totals(not_paid_rows)

        result_list.append(entry)

    return result_list


def _compute_totals(rows: list[dict]) -> dict:
    """
    Compute column totals from a list of row dicts.

    Args:
        rows: List of period row dicts.

    Returns:
        A dict with summed values for each numeric column.

    """
    if not rows:
        return {
            "payment": Decimal(0),
            "interest_portion": Decimal(0),
            "principal_portion": Decimal(0),
            "opportunity_cost": Decimal(0),
            "inflation_adjustment": Decimal(0),
            "tax_savings": Decimal(0),
            "cumulative_true_total_cost": Decimal(0),
        }
    return {
        "payment": sum(r["payment"] for r in rows),
        "interest_portion": sum(r["interest_portion"] for r in rows),
        "principal_portion": sum(r["principal_portion"] for r in rows),
        "opportunity_cost": sum(r["opportunity_cost"] for r in rows),
        "inflation_adjustment": sum(r["inflation_adjustment"] for r in rows),
        "tax_savings": sum(r["tax_savings"] for r in rows),
        "cumulative_true_total_cost": rows[-1]["cumulative_true_total_cost"],
    }


def build_compare_data(
    options_data: list[dict],
    comparison_period_months: int,
    granularity: str = "monthly",
) -> list[dict]:
    """
    Build side-by-side comparison data for the compare tab.

    Each row contains the period label and per-option payment and
    cumulative true total cost values.

    Args:
        options_data: List of option dicts from analyze_results.
        comparison_period_months: The comparison period in months.
        granularity: "monthly" or "annual".

    Returns:
        List of row dicts with period and per-option payment/cumulative data.

    """
    _ = comparison_period_months  # reserved for future use

    # Build rows for each option (use paid_on_time for promo)
    all_option_rows: list[tuple[str, list[dict]]] = []
    for opt in options_data:
        primary_result: OptionResult = opt["result"]
        rows = _monthly_data_to_rows(primary_result.monthly_data)
        if granularity == "annual":
            rows = aggregate_annual(rows)
        all_option_rows.append((opt["name"], rows))

    # Determine max periods across all options
    max_periods = max((len(rows) for _, rows in all_option_rows), default=0)

    compare_rows: list[dict] = []
    for i in range(max_periods):
        # Use period label from first option that has this period
        period_label = None
        for _, rows in all_option_rows:
            if i < len(rows):
                period_label = rows[i]["period"]
                break

        options_col: list[dict] = []
        for name, rows in all_option_rows:
            if i < len(rows):
                options_col.append(
                    {
                        "name": name,
                        "payment": rows[i]["payment"],
                        "cumulative": rows[i]["cumulative_true_total_cost"],
                    },
                )
            else:
                options_col.append(
                    {
                        "name": name,
                        "payment": Decimal(0),
                        "cumulative": Decimal(0),
                    },
                )

        compare_rows.append(
            {
                "period": period_label,
                "options": options_col,
            },
        )

    return compare_rows
