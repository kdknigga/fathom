"""
Tests for the tax savings calculation module.

Covers basic tax savings computation, disabled tax passthrough,
and full-term tax savings accumulation.
"""

from decimal import Decimal


def test_tax_savings_basic() -> None:
    """Tax savings equals total interest times marginal tax rate."""
    from fathom.tax import compute_tax_savings

    interest_payments = [Decimal(50), Decimal(48), Decimal(46)]
    result = compute_tax_savings(
        interest_payments=interest_payments,
        marginal_tax_rate=Decimal("0.22"),
    )
    expected = (Decimal(50) + Decimal(48) + Decimal(46)) * Decimal("0.22")
    assert result == expected


def test_tax_disabled() -> None:
    """When tax rate is zero, tax savings is zero."""
    from fathom.tax import compute_tax_savings

    interest_payments = [Decimal(50), Decimal(48), Decimal(46)]
    result = compute_tax_savings(
        interest_payments=interest_payments,
        marginal_tax_rate=Decimal(0),
    )
    assert result == Decimal(0)


def test_tax_over_full_term() -> None:
    """Tax savings accumulates correctly over a full 36-month term."""
    from fathom.tax import compute_tax_savings

    # Simulated declining interest payments over 36 months
    interest_payments = [Decimal(50) - Decimal(str(i)) for i in range(36)]
    result = compute_tax_savings(
        interest_payments=interest_payments,
        marginal_tax_rate=Decimal("0.22"),
    )
    expected = sum(interest_payments) * Decimal("0.22")
    assert result == expected
    assert isinstance(result, Decimal)
