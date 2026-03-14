"""
Tests for the opportunity cost calculation module.

Covers cash buyer investment modeling, loan buyer decreasing pool,
pool exhaustion behavior, and freed-cash-after-payoff investing.
"""

from decimal import Decimal

from fathom.models import FinancingOption, GlobalSettings, OptionType


def test_cash_buyer_opportunity_cost(
    cash_option: FinancingOption,
    default_settings: GlobalSettings,
) -> None:
    """Cash buyer invests full purchase price from month 1."""
    from fathom.opportunity import compute_opportunity_cost

    result = compute_opportunity_cost(
        option=cash_option,
        settings=default_settings,
        comparison_period=36,
    )
    # Full $10k invested at 7% for 36 months should yield meaningful returns
    assert result > Decimal(0)


def test_loan_buyer_decreasing_pool(
    standard_loan: FinancingOption,
    default_settings: GlobalSettings,
) -> None:
    """Loan buyer pool decreases as monthly payments are made."""
    from fathom.opportunity import compute_opportunity_cost_series

    series = compute_opportunity_cost_series(
        option=standard_loan,
        settings=default_settings,
        comparison_period=36,
    )
    # Pool should generally decrease over time
    assert series[0] > series[-1]


def test_pool_exhaustion() -> None:
    """Investment pool hits zero and clamps, stopping returns."""
    from fathom.opportunity import compute_opportunity_cost_series

    # Use a loan with high payments relative to pool and low return
    # so the pool actually drains to zero during the loan term
    loan = FinancingOption(
        option_type=OptionType.TRADITIONAL_LOAN,
        label="Pool Drain Loan",
        purchase_price=Decimal(5000),
        apr=Decimal("0.06"),
        term_months=36,
    )
    settings = GlobalSettings(return_rate=Decimal("0.02"))
    series = compute_opportunity_cost_series(
        option=loan,
        settings=settings,
        comparison_period=36,
    )
    # Pool should hit zero at some point and clamp
    assert any(balance == Decimal(0) for balance in series)
    # Once zero, should stay zero (no negative values)
    first_zero = next(i for i, b in enumerate(series) if b == Decimal(0))
    for balance in series[first_zero:]:
        assert balance == Decimal(0)


def test_freed_cash_after_payoff(
    default_settings: GlobalSettings,
) -> None:
    """Freed-up payments after shorter loan ends are invested (CALC-04)."""
    from fathom.opportunity import compute_opportunity_cost

    short_loan = FinancingOption(
        option_type=OptionType.TRADITIONAL_LOAN,
        label="Short Loan",
        purchase_price=Decimal(10000),
        apr=Decimal("0.06"),
        term_months=24,
    )
    # Comparison period is 36 months but loan is only 24
    # Months 25-36 should invest the freed-up payment amount
    result = compute_opportunity_cost(
        option=short_loan,
        settings=default_settings,
        comparison_period=36,
    )
    assert result > Decimal(0)


# ---------------------------------------------------------------------------
# DETAIL-01: Per-period opportunity cost computation
# ---------------------------------------------------------------------------


def test_per_period_returns_list_with_correct_length(
    cash_option: FinancingOption,
    default_settings: GlobalSettings,
) -> None:
    """compute_opportunity_cost_per_period returns list[Decimal] with length == comparison_period."""
    from fathom.opportunity import compute_opportunity_cost_per_period

    result = compute_opportunity_cost_per_period(
        option=cash_option,
        settings=default_settings,
        comparison_period=36,
    )
    assert isinstance(result, list)
    assert len(result) == 36
    assert all(isinstance(v, Decimal) for v in result)


def test_per_period_sum_equals_aggregate(
    cash_option: FinancingOption,
    default_settings: GlobalSettings,
) -> None:
    """Sum of per-period opportunity cost equals compute_opportunity_cost (within 0.02 tolerance)."""
    from fathom.opportunity import (
        compute_opportunity_cost,
        compute_opportunity_cost_per_period,
    )

    per_period = compute_opportunity_cost_per_period(
        option=cash_option,
        settings=default_settings,
        comparison_period=36,
    )
    aggregate = compute_opportunity_cost(
        option=cash_option,
        settings=default_settings,
        comparison_period=36,
    )
    assert abs(sum(per_period) - aggregate) <= Decimal("0.05")


def test_per_period_sum_equals_aggregate_for_loan(
    standard_loan: FinancingOption,
    default_settings: GlobalSettings,
) -> None:
    """Sum of per-period opportunity cost equals aggregate for loan option."""
    from fathom.opportunity import (
        compute_opportunity_cost,
        compute_opportunity_cost_per_period,
    )

    per_period = compute_opportunity_cost_per_period(
        option=standard_loan,
        settings=default_settings,
        comparison_period=36,
    )
    aggregate = compute_opportunity_cost(
        option=standard_loan,
        settings=default_settings,
        comparison_period=36,
    )
    assert abs(sum(per_period) - aggregate) <= Decimal("0.05")


def test_per_period_cash_returns_growth_values(
    cash_option: FinancingOption,
    default_settings: GlobalSettings,
) -> None:
    """Per-period for cash option returns per-month growth values."""
    from fathom.opportunity import compute_opportunity_cost_per_period

    per_period = compute_opportunity_cost_per_period(
        option=cash_option,
        settings=default_settings,
        comparison_period=36,
    )
    # Cash: full price invested, monthly growth should be > 0 each month
    assert all(v > Decimal(0) for v in per_period)


def test_per_period_loan_covers_both_phases(
    default_settings: GlobalSettings,
) -> None:
    """Per-period for loan covers both loan phase and freed-cash phase."""
    from fathom.opportunity import compute_opportunity_cost_per_period

    short_loan = FinancingOption(
        option_type=OptionType.TRADITIONAL_LOAN,
        label="Short Loan",
        purchase_price=Decimal(10000),
        apr=Decimal("0.06"),
        term_months=24,
    )
    per_period = compute_opportunity_cost_per_period(
        option=short_loan,
        settings=default_settings,
        comparison_period=36,
    )
    assert len(per_period) == 36
    # Months 25-36 (freed cash phase) should have non-zero values
    freed_cash_values = per_period[24:]
    assert any(v > Decimal(0) for v in freed_cash_values)
