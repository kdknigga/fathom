"""
Tests for the engine orchestrator module.

Covers comparison period normalization, True Total Cost formula,
cash vs loan comparison, all-cash scenarios, and dual-outcome promo.
"""

from decimal import Decimal

from fathom.models import (
    FinancingOption,
    GlobalSettings,
    OptionType,
    PromoResult,
)


def test_normalization_to_longest_term(
    standard_loan: FinancingOption,
    cash_option: FinancingOption,
    default_settings: GlobalSettings,
) -> None:
    """All options are normalized to the longest term (CALC-03)."""
    from fathom.engine import compare

    result = compare(
        options=[standard_loan, cash_option],
        settings=default_settings,
    )
    assert standard_loan.term_months is not None
    assert result.comparison_period_months == standard_loan.term_months


def test_true_total_cost(
    standard_loan: FinancingOption,
    default_settings: GlobalSettings,
) -> None:
    """True Total Cost = payments + opportunity_cost - rebates - tax_savings +/- inflation (CALC-05)."""
    from fathom.engine import compare

    result = compare(
        options=[standard_loan],
        settings=default_settings,
    )
    option_result = result.results[standard_loan.label]
    expected = (
        option_result.total_payments
        + option_result.opportunity_cost
        - option_result.rebates
        - option_result.tax_savings
        + option_result.inflation_adjustment
    )
    assert option_result.true_total_cost == expected


def test_cash_vs_loan_comparison(
    standard_loan: FinancingOption,
    cash_option: FinancingOption,
    default_settings: GlobalSettings,
) -> None:
    """Cash vs loan comparison produces results for both options."""
    from fathom.engine import compare

    result = compare(
        options=[standard_loan, cash_option],
        settings=default_settings,
    )
    assert standard_loan.label in result.results
    assert cash_option.label in result.results


def test_all_cash_instant_comparison() -> None:
    """All-cash comparison is instant with no investment modeling."""
    from fathom.engine import compare

    cash_a = FinancingOption(
        option_type=OptionType.CASH,
        label="Cash A",
        purchase_price=Decimal(10000),
    )
    cash_b = FinancingOption(
        option_type=OptionType.CASH,
        label="Cash B",
        purchase_price=Decimal(9500),
    )
    settings = GlobalSettings(return_rate=Decimal("0.07"))
    result = compare(options=[cash_a, cash_b], settings=settings)
    # All-cash comparison should have zero-length comparison period
    assert result.comparison_period_months == 0


def test_dual_outcome_promo(
    promo_zero_percent: FinancingOption,
    default_settings: GlobalSettings,
) -> None:
    """Zero-percent promo produces a dual-outcome PromoResult."""
    from fathom.engine import compare

    result = compare(
        options=[promo_zero_percent],
        settings=default_settings,
    )
    promo_result = result.results[promo_zero_percent.label]
    assert isinstance(promo_result, PromoResult)
    assert promo_result.required_monthly_payment > Decimal(0)
    assert promo_result.break_even_month > 0


# ---------------------------------------------------------------------------
# DETAIL-01: Per-period cost factors in engine builders
# ---------------------------------------------------------------------------


def test_loan_result_has_per_period_opportunity_cost(
    standard_loan: FinancingOption,
    default_settings: GlobalSettings,
) -> None:
    """_build_loan_result produces MonthlyDataPoint entries with non-zero opportunity_cost."""
    from fathom.engine import _build_loan_result

    result = _build_loan_result(standard_loan, default_settings, 36)
    # At least some months should have non-zero opportunity cost
    opp_costs = [dp.opportunity_cost for dp in result.monthly_data]
    assert any(v > Decimal(0) for v in opp_costs)


def test_loan_result_has_per_period_inflation(
    standard_loan: FinancingOption,
    settings_with_inflation: GlobalSettings,
) -> None:
    """_build_loan_result produces per-period inflation_adjustment when inflation_enabled."""
    from fathom.engine import _build_loan_result

    result = _build_loan_result(standard_loan, settings_with_inflation, 36)
    infl_values = [dp.inflation_adjustment for dp in result.monthly_data]
    # Active loan months should have non-zero inflation adjustment
    assert any(v != Decimal(0) for v in infl_values)


def test_loan_result_has_per_period_tax_savings(
    standard_loan: FinancingOption,
    settings_with_tax: GlobalSettings,
) -> None:
    """_build_loan_result produces per-period tax_savings when tax_enabled."""
    from fathom.engine import _build_loan_result

    result = _build_loan_result(standard_loan, settings_with_tax, 36)
    tax_values = [dp.tax_savings for dp in result.monthly_data]
    # Months with interest should have non-zero tax savings
    assert any(v > Decimal(0) for v in tax_values)


def test_cash_result_has_per_period_opportunity_cost(
    cash_option: FinancingOption,
    default_settings: GlobalSettings,
) -> None:
    """_build_cash_result produces MonthlyDataPoint entries with per-period opportunity_cost."""
    from fathom.engine import _build_cash_result

    result = _build_cash_result(cash_option, default_settings, 36)
    opp_costs = [dp.opportunity_cost for dp in result.monthly_data]
    assert all(v > Decimal(0) for v in opp_costs)


def test_promo_result_has_per_period_values(
    promo_zero_percent: FinancingOption,
    default_settings: GlobalSettings,
) -> None:
    """_build_promo_result produces per-period values for both outcomes."""
    from fathom.engine import _build_promo_result

    result = _build_promo_result(promo_zero_percent, default_settings, 12)
    # paid_on_time should have per-period opportunity costs
    paid_opp = [dp.opportunity_cost for dp in result.paid_on_time.monthly_data]
    assert any(v > Decimal(0) for v in paid_opp)
    # not_paid_on_time should also have per-period opportunity costs
    not_paid_opp = [dp.opportunity_cost for dp in result.not_paid_on_time.monthly_data]
    assert any(v > Decimal(0) for v in not_paid_opp)


def test_per_period_opp_cost_sums_to_aggregate(
    standard_loan: FinancingOption,
    default_settings: GlobalSettings,
) -> None:
    """Sum of per-period opportunity_cost equals OptionResult.opportunity_cost (within 0.05)."""
    from fathom.engine import _build_loan_result

    result = _build_loan_result(standard_loan, default_settings, 36)
    per_period_sum = sum(dp.opportunity_cost for dp in result.monthly_data)
    assert abs(per_period_sum - result.opportunity_cost) <= Decimal("0.05")


def test_per_period_tax_savings_sums_to_aggregate(
    standard_loan: FinancingOption,
    settings_with_tax: GlobalSettings,
) -> None:
    """Sum of per-period tax_savings equals OptionResult.tax_savings (within 0.05)."""
    from fathom.engine import _build_loan_result

    result = _build_loan_result(standard_loan, settings_with_tax, 36)
    per_period_sum = sum(dp.tax_savings for dp in result.monthly_data)
    assert abs(per_period_sum - result.tax_savings) <= Decimal("0.05")


def test_per_period_inflation_sums_to_aggregate(
    standard_loan: FinancingOption,
    settings_with_inflation: GlobalSettings,
) -> None:
    """Sum of per-period inflation_adjustment equals OptionResult.inflation_adjustment (within 0.05)."""
    from fathom.engine import _build_loan_result

    result = _build_loan_result(standard_loan, settings_with_inflation, 36)
    per_period_sum = sum(dp.inflation_adjustment for dp in result.monthly_data)
    assert abs(per_period_sum - result.inflation_adjustment) <= Decimal("0.05")


def test_padded_months_have_zero_inflation_and_tax() -> None:
    """MonthlyDataPoint entries padded beyond loan term have Decimal(0) for inflation/tax."""
    from fathom.engine import _build_loan_result

    short_loan = FinancingOption(
        option_type=OptionType.TRADITIONAL_LOAN,
        label="Short Loan",
        purchase_price=Decimal(10000),
        apr=Decimal("0.06"),
        term_months=24,
    )
    settings = GlobalSettings(
        return_rate=Decimal("0.07"),
        inflation_enabled=True,
        inflation_rate=Decimal("0.03"),
        tax_enabled=True,
        tax_rate=Decimal("0.22"),
    )
    result = _build_loan_result(short_loan, settings, 36)
    # Months 25-36 are padded (beyond loan term)
    for dp in result.monthly_data[24:]:
        assert dp.inflation_adjustment == Decimal(0)
        assert dp.tax_savings == Decimal(0)
