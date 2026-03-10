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
    OptionResult,
    PromoResult,
)

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
            rows.append({"label": label, "values": values})

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
        if is_promo and isinstance(result, PromoResult):
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
