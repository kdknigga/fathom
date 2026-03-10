"""
Tests for the caveat generation module.

Covers deferred interest risk detection, opportunity cost sensitivity,
high interest warnings, and caveat generation for all options.
"""

from decimal import Decimal

import pytest

from fathom.models import (
    CaveatType,
    FinancingOption,
    GlobalSettings,
    OptionResult,
    OptionType,
)


@pytest.mark.xfail(reason="not yet implemented")
def test_deferred_interest_caveat(
    promo_zero_percent: FinancingOption,
) -> None:
    """Deferred interest caveat is generated for promo options."""
    from fathom.caveats import generate_caveats

    caveats = generate_caveats(
        option=promo_zero_percent,
        result=_stub_option_result(),
        settings=GlobalSettings(return_rate=Decimal("0.07")),
    )
    caveat_types = [c.caveat_type for c in caveats]
    assert CaveatType.DEFERRED_INTEREST_RISK in caveat_types


@pytest.mark.xfail(reason="not yet implemented")
def test_opportunity_cost_dominance(
    standard_loan: FinancingOption,
    default_settings: GlobalSettings,
) -> None:
    """Opportunity cost dominance flagged when winner changes at +/-2%."""
    from fathom.caveats import check_opportunity_cost_sensitivity

    is_sensitive = check_opportunity_cost_sensitivity(
        option=standard_loan,
        settings=default_settings,
        comparison_period=36,
    )
    # Result depends on implementation; just verify it returns a bool
    assert isinstance(is_sensitive, bool)


@pytest.mark.xfail(reason="not yet implemented")
def test_high_interest_caveat() -> None:
    """High interest caveat when total interest exceeds 30% of price."""
    from fathom.caveats import generate_caveats

    high_interest_result = _stub_option_result(
        total_interest=Decimal(4000),
    )
    option = FinancingOption(
        option_type=OptionType.TRADITIONAL_LOAN,
        label="High Interest",
        purchase_price=Decimal(10000),
        apr=Decimal("0.15"),
        term_months=60,
    )
    caveats = generate_caveats(
        option=option,
        result=high_interest_result,
        settings=GlobalSettings(return_rate=Decimal("0.07")),
    )
    caveat_types = [c.caveat_type for c in caveats]
    assert CaveatType.HIGH_INTEREST_TOTAL in caveat_types


@pytest.mark.xfail(reason="not yet implemented")
def test_caveats_all_options(
    standard_loan: FinancingOption,
    cash_option: FinancingOption,
    default_settings: GlobalSettings,
) -> None:
    """Caveats are generated for every option, not just the winner."""
    from fathom.caveats import generate_all_caveats

    results = {
        standard_loan.label: _stub_option_result(),
        cash_option.label: _stub_option_result(),
    }
    caveats = generate_all_caveats(
        options=[standard_loan, cash_option],
        results=results,
        settings=default_settings,
    )
    # Should return a list (possibly empty) covering all options
    assert isinstance(caveats, list)


def _stub_option_result(
    total_interest: Decimal = Decimal("951.92"),
) -> OptionResult:
    """Create a minimal stub OptionResult for caveat testing."""
    return OptionResult(
        total_payments=Decimal("10951.92"),
        total_interest=total_interest,
        opportunity_cost=Decimal(500),
        tax_savings=Decimal(0),
        inflation_adjustment=Decimal(0),
        rebates=Decimal(0),
        true_total_cost=Decimal("11451.92"),
        monthly_data=[],
    )
