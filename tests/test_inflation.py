"""
Tests for the inflation adjustment module.

Covers present value discounting at various inflation rates, zero
inflation passthrough, and full-term discounting behavior.
"""

from decimal import Decimal

import pytest


@pytest.mark.xfail(reason="not yet implemented")
def test_present_value_discounting() -> None:
    """$304.22 at month 12 with 3% inflation discounts to ~$295.24."""
    from fathom.inflation import present_value

    result = present_value(
        future_value=Decimal("304.22"),
        annual_inflation=Decimal("0.03"),
        month=12,
    )
    # Should be approximately $295.24
    assert Decimal("295.00") < result < Decimal("296.00")


@pytest.mark.xfail(reason="not yet implemented")
def test_zero_inflation() -> None:
    """Zero inflation rate returns the original value unchanged."""
    from fathom.inflation import present_value

    result = present_value(
        future_value=Decimal("304.22"),
        annual_inflation=Decimal(0),
        month=12,
    )
    assert result == Decimal("304.22")


@pytest.mark.xfail(reason="not yet implemented")
def test_full_term_discounting() -> None:
    """Discounting 36 months of payments produces meaningful adjustment."""
    from fathom.inflation import discount_payment_series

    payments = [Decimal("304.22")] * 36
    result = discount_payment_series(
        payments=payments,
        annual_inflation=Decimal("0.03"),
    )
    # Total should be less than nominal sum (36 * 304.22 = 10951.92)
    nominal_total = Decimal("304.22") * 36
    assert result < nominal_total
    assert result > Decimal(0)
