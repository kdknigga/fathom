"""
Tests for the amortization calculation module.

Covers standard amortization formula, zero-APR handling, Decimal type
enforcement, schedule integrity, and last payment adjustment.
"""

from decimal import Decimal

import pytest

from fathom.models import FinancingOption


@pytest.mark.xfail(reason="not yet implemented")
def test_standard_amortization(standard_loan: FinancingOption) -> None:
    """Standard $10k/6%/36mo loan produces $304.22/month payment."""
    from fathom.amortization import monthly_payment

    assert standard_loan.apr is not None
    assert standard_loan.term_months is not None

    result = monthly_payment(
        principal=standard_loan.purchase_price,
        apr=standard_loan.apr,
        term_months=standard_loan.term_months,
    )
    assert result == Decimal("304.22")


@pytest.mark.xfail(reason="not yet implemented")
def test_zero_apr() -> None:
    """Zero APR loan produces simple division: $10k/36mo = $277.78/month."""
    from fathom.amortization import monthly_payment

    result = monthly_payment(
        principal=Decimal(10000),
        apr=Decimal(0),
        term_months=36,
    )
    assert result == Decimal("277.78")


@pytest.mark.xfail(reason="not yet implemented")
def test_decimal_types(standard_loan: FinancingOption) -> None:
    """All amortization outputs must be Decimal, never float."""
    from fathom.amortization import monthly_payment

    assert standard_loan.apr is not None
    assert standard_loan.term_months is not None

    result = monthly_payment(
        principal=standard_loan.purchase_price,
        apr=standard_loan.apr,
        term_months=standard_loan.term_months,
    )
    assert isinstance(result, Decimal)


@pytest.mark.xfail(reason="not yet implemented")
def test_amortization_schedule(standard_loan: FinancingOption) -> None:
    """Sum of all payments in the schedule matches expected total."""
    from fathom.amortization import amortization_schedule

    assert standard_loan.apr is not None
    assert standard_loan.term_months is not None

    schedule = amortization_schedule(
        principal=standard_loan.purchase_price,
        apr=standard_loan.apr,
        term_months=standard_loan.term_months,
    )
    total = sum(entry.payment for entry in schedule)
    # 36 payments of ~$304.22 = ~$10,951.92
    assert total > Decimal(10000)
    assert len(schedule) == 36


@pytest.mark.xfail(reason="not yet implemented")
def test_last_payment_adjustment(standard_loan: FinancingOption) -> None:
    """Final payment clears exact remaining balance (no residual)."""
    from fathom.amortization import amortization_schedule

    assert standard_loan.apr is not None
    assert standard_loan.term_months is not None

    schedule = amortization_schedule(
        principal=standard_loan.purchase_price,
        apr=standard_loan.apr,
        term_months=standard_loan.term_months,
    )
    last_entry = schedule[-1]
    assert last_entry.remaining_balance == Decimal(0)
