"""
Tests for the engine orchestrator module.

Covers comparison period normalization, True Total Cost formula,
cash vs loan comparison, all-cash scenarios, and dual-outcome promo.
"""

from decimal import Decimal

import pytest

from fathom.models import (
    FinancingOption,
    GlobalSettings,
    OptionType,
    PromoResult,
)


@pytest.mark.xfail(reason="not yet implemented")
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


@pytest.mark.xfail(reason="not yet implemented")
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


@pytest.mark.xfail(reason="not yet implemented")
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


@pytest.mark.xfail(reason="not yet implemented")
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


@pytest.mark.xfail(reason="not yet implemented")
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
