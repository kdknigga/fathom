"""
Inflation adjustment module.

Applies present value discounting to future cash flows using
user-specified inflation rates. All calculations use Decimal
arithmetic to maintain financial precision.
"""

from decimal import Decimal

from fathom.money import quantize_money


def present_value(
    future_value: Decimal,
    annual_inflation: Decimal,
    month: int,
) -> Decimal:
    """
    Discount a future value to its present value using monthly inflation.

    Uses the formula: PV = FV / (1 + r_monthly)^month
    where r_monthly = annual_inflation / 12.

    Returns the original value unchanged when month is 0 or inflation
    rate is zero.

    Args:
        future_value: The nominal future cash amount.
        annual_inflation: Annual inflation rate as a decimal (e.g. 0.03 for 3%).
        month: The month number (0-based or 1-based depending on caller).

    Returns:
        The present value, rounded to the nearest cent.

    """
    if month == 0 or annual_inflation == Decimal(0):
        return future_value

    monthly_rate = annual_inflation / 12
    discounted = future_value / (1 + monthly_rate) ** month
    return quantize_money(discounted)


def discount_cash_flows(
    payments: list[Decimal],
    annual_inflation: Decimal,
) -> list[Decimal]:
    """
    Apply present value discounting to a series of monthly payments.

    Each payment is discounted by its month index (1-based), so
    the first payment is at month 1, second at month 2, etc.

    Args:
        payments: List of nominal monthly payment amounts.
        annual_inflation: Annual inflation rate as a decimal.

    Returns:
        A list of discounted payment values.

    """
    return [
        present_value(payment, annual_inflation, month + 1)
        for month, payment in enumerate(payments)
    ]


def discount_payment_series(
    payments: list[Decimal],
    annual_inflation: Decimal,
) -> Decimal:
    """
    Compute the total present value of a series of monthly payments.

    Discounts each payment to its present value and returns the sum.

    Args:
        payments: List of nominal monthly payment amounts.
        annual_inflation: Annual inflation rate as a decimal.

    Returns:
        The total discounted value of all payments.

    """
    discounted = discount_cash_flows(payments, annual_inflation)
    return quantize_money(sum(discounted, Decimal(0)))


def compute_inflation_adjustment(
    nominal_payments: list[Decimal],
    annual_inflation: Decimal,
) -> Decimal:
    """
    Compute the inflation adjustment for a payment series.

    Returns the difference between total nominal payments and total
    discounted payments. A positive result means inflation reduces the
    real cost of the payments.

    Args:
        nominal_payments: List of nominal monthly payment amounts.
        annual_inflation: Annual inflation rate as a decimal.

    Returns:
        The inflation adjustment amount (nominal total minus discounted total).

    """
    nominal_total = sum(nominal_payments, Decimal(0))
    discounted_total = discount_payment_series(nominal_payments, annual_inflation)
    return quantize_money(nominal_total - discounted_total)
