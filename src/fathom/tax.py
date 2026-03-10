"""
Tax savings calculation module.

Computes tax savings from deductible interest payments at the user's
marginal tax rate. All calculations use Decimal arithmetic.
"""

from decimal import Decimal

CENTS = Decimal("0.01")


def quantize_money(value: Decimal) -> Decimal:
    """Round a Decimal value to the nearest cent (two decimal places)."""
    return value.quantize(CENTS)


def compute_tax_savings(
    interest_payments: list[Decimal],
    marginal_tax_rate: Decimal,
) -> Decimal:
    """
    Compute tax savings from deductible interest payments.

    Calculates the total tax benefit by multiplying the sum of all
    interest payments by the marginal tax rate.

    Returns zero when the tax rate is zero.

    Args:
        interest_payments: List of monthly interest payment amounts.
        marginal_tax_rate: The marginal tax rate as a decimal (e.g. 0.22 for 22%).

    Returns:
        The total tax savings, rounded to the nearest cent.

    """
    if marginal_tax_rate == Decimal(0):
        return Decimal(0)

    total_interest = sum(interest_payments, Decimal(0))
    return quantize_money(total_interest * marginal_tax_rate)
