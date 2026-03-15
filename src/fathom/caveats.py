"""
Caveat generation module.

Generates structured risk warnings for financing options based on
deferred interest, opportunity cost sensitivity, and high interest totals.
All caveats are generated for every option, not just the winner.
"""

from decimal import Decimal

from fathom.models import (
    Caveat,
    CaveatType,
    FinancingOption,
    GlobalSettings,
    OptionResult,
    OptionType,
    PromoResult,
    Severity,
)
from fathom.money import quantize_money
from fathom.opportunity import compute_opportunity_cost


def generate_caveats(
    option: FinancingOption,
    result: OptionResult | PromoResult,
) -> list[Caveat]:
    """
    Generate caveats for a single financing option.

    Checks for deferred interest risk and high interest total conditions
    based on the option type and computed results.

    Args:
        option: The financing option being analyzed.
        result: The computed result for this option.

    Returns:
        A list of Caveat objects for this option.

    """
    caveats: list[Caveat] = []

    # Deferred interest risk for promo zero-percent options
    if option.option_type == OptionType.PROMO_ZERO_PERCENT and option.deferred_interest:
        term = option.term_months if option.term_months is not None else 0
        required_payment = (
            quantize_money(option.purchase_price / term) if term > 0 else Decimal(0)
        )
        break_even = term

        severity = Severity.CRITICAL if term <= 12 else Severity.WARNING
        caveats.append(
            Caveat(
                caveat_type=CaveatType.DEFERRED_INTEREST_RISK,
                message=(
                    f"Deferred interest: pay at least ${required_payment}/month "
                    f"to avoid penalty. Break-even month: {break_even}."
                ),
                severity=severity,
            ),
        )

    # High interest total when interest > 30% of purchase price
    option_result = result.paid_on_time if isinstance(result, PromoResult) else result
    threshold = Decimal("0.30") * option.purchase_price
    if option_result.total_interest > threshold:
        caveats.append(
            Caveat(
                caveat_type=CaveatType.HIGH_INTEREST_TOTAL,
                message=(
                    f"Total interest (${option_result.total_interest}) exceeds "
                    f"30% of purchase price (${threshold})."
                ),
                severity=Severity.WARNING,
            ),
        )

    return caveats


def check_opportunity_cost_sensitivity(
    option: FinancingOption,
    settings: GlobalSettings,
    comparison_period: int,
) -> bool:
    """
    Check if opportunity cost ranking is sensitive to return rate changes.

    Tests whether a +/-2% shift in the assumed return rate would change
    the relative ranking of this option's opportunity cost.

    Args:
        option: The financing option to test.
        settings: Global comparison settings with baseline return rate.
        comparison_period: The normalized comparison period in months.

    Returns:
        True if the opportunity cost changes significantly at +/-2%.

    """
    base_cost = compute_opportunity_cost(option, settings, comparison_period)

    settings_up = GlobalSettings(
        return_rate=settings.return_rate + Decimal("0.02"),
        inflation_enabled=settings.inflation_enabled,
        inflation_rate=settings.inflation_rate,
        tax_enabled=settings.tax_enabled,
        tax_rate=settings.tax_rate,
    )
    cost_up = compute_opportunity_cost(option, settings_up, comparison_period)

    settings_down = GlobalSettings(
        return_rate=settings.return_rate - Decimal("0.02"),
        inflation_enabled=settings.inflation_enabled,
        inflation_rate=settings.inflation_rate,
        tax_enabled=settings.tax_enabled,
        tax_rate=settings.tax_rate,
    )
    cost_down = compute_opportunity_cost(option, settings_down, comparison_period)

    # Sensitive if the cost changes by more than 10% in either direction
    if base_cost == Decimal(0):
        return cost_up != Decimal(0) or cost_down != Decimal(0)

    change_up = abs(cost_up - base_cost) / base_cost
    change_down = abs(cost_down - base_cost) / base_cost
    return change_up > Decimal("0.10") or change_down > Decimal("0.10")


def _compute_ttc_at_rate(
    options: list[FinancingOption],
    results: dict[str, OptionResult | PromoResult],
    settings: GlobalSettings,
    comparison_period: int,
    return_rate: Decimal,
) -> dict[str, Decimal]:
    """
    Compute simplified True Total Cost for each option at a given return rate.

    Used for sensitivity analysis to check if the winner changes at
    different return rates.

    Args:
        options: All financing options being compared.
        results: Precomputed results for each option.
        settings: Global comparison settings.
        comparison_period: Normalized comparison period.
        return_rate: The return rate to use for opportunity cost.

    Returns:
        A mapping of option label to True Total Cost.

    """
    adjusted_settings = GlobalSettings(
        return_rate=return_rate,
        inflation_enabled=settings.inflation_enabled,
        inflation_rate=settings.inflation_rate,
        tax_enabled=settings.tax_enabled,
        tax_rate=settings.tax_rate,
    )

    ttc_map: dict[str, Decimal] = {}
    for option in options:
        result = results[option.label]
        base_result = result.paid_on_time if isinstance(result, PromoResult) else result
        opp_cost = compute_opportunity_cost(
            option,
            adjusted_settings,
            comparison_period,
        )
        ttc = (
            base_result.total_payments
            + opp_cost
            - base_result.rebates
            - base_result.tax_savings
            + base_result.inflation_adjustment
        )
        ttc_map[option.label] = ttc

    return ttc_map


def _check_winner_changes(
    options: list[FinancingOption],
    results: dict[str, OptionResult | PromoResult],
    settings: GlobalSettings,
    comparison_period: int,
) -> str | None:
    """
    Check if the winner changes at +/-2% return rate.

    Args:
        options: All financing options being compared.
        results: Precomputed results for each option.
        settings: Global comparison settings.
        comparison_period: Normalized comparison period.

    Returns:
        A description of the rate shift that changes the winner, or None.

    """
    if len(options) < 2:
        return None

    base_ttc = _compute_ttc_at_rate(
        options,
        results,
        settings,
        comparison_period,
        settings.return_rate,
    )
    base_winner = min(base_ttc, key=lambda k: base_ttc[k])

    for shift_label, shift in [
        ("+2%", Decimal("0.02")),
        ("-2%", Decimal("-0.02")),
    ]:
        shifted_rate = settings.return_rate + shift
        shifted_rate = max(shifted_rate, Decimal(0))
        shifted_ttc = _compute_ttc_at_rate(
            options,
            results,
            settings,
            comparison_period,
            shifted_rate,
        )
        shifted_winner = min(shifted_ttc, key=lambda k: shifted_ttc[k])
        if shifted_winner != base_winner:
            return shift_label

    return None


def generate_all_caveats(
    options: list[FinancingOption],
    results: dict[str, OptionResult | PromoResult],
    settings: GlobalSettings,
    comparison_period: int = 0,
) -> list[Caveat]:
    """
    Generate caveats for all options in a comparison.

    Runs per-option caveat checks on every option, then runs cross-option
    checks like opportunity cost dominance sensitivity.

    Args:
        options: All financing options being compared.
        results: Precomputed results keyed by option label.
        settings: Global comparison settings.
        comparison_period: Normalized comparison period in months.

    Returns:
        A list of all generated caveats across all options.

    """
    all_caveats: list[Caveat] = []

    # Per-option caveats
    for option in options:
        result = results[option.label]
        all_caveats.extend(generate_caveats(option, result))

    # Cross-option: opportunity cost dominance
    shift = _check_winner_changes(options, results, settings, comparison_period)
    if shift is not None:
        all_caveats.append(
            Caveat(
                caveat_type=CaveatType.OPPORTUNITY_COST_DOMINANCE,
                message=(
                    f"Winner changes at {shift} return rate shift. "
                    f"Opportunity cost assumptions significantly affect ranking."
                ),
                severity=Severity.INFO,
            ),
        )

    return all_caveats
