"""
Centralized monetary rounding utilities.

Provides a single canonical definition of two-decimal-place (cent) precision
rounding for all monetary calculations throughout the application.
"""

from decimal import Decimal

CENTS = Decimal("0.01")


def quantize_money(value: Decimal) -> Decimal:
    """Round a Decimal value to the nearest cent (two decimal places)."""
    return value.quantize(CENTS)
