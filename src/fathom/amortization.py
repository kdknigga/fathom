"""
Amortization and payment calculation module.

Provides standard amortization formula, amortization schedule generation,
and related payment computations. All monetary values use Decimal to avoid
floating-point precision errors.
"""

from decimal import Decimal

from fathom.models import MonthlyDataPoint

CENTS = Decimal("0.01")


def quantize_money(value: Decimal) -> Decimal:
    """Round a Decimal value to the nearest cent (two decimal places)."""
    return value.quantize(CENTS)


def monthly_payment(
    principal: Decimal,
    apr: Decimal,
    term_months: int,
) -> Decimal:
    """
    Compute the fixed monthly payment for a standard amortizing loan.

    Uses the standard amortization formula:
        M = P * r * (1+r)^n / ((1+r)^n - 1)

    where P = principal, r = monthly rate, n = number of months.
    Handles zero APR as simple division to avoid division by zero.

    Args:
        principal: The loan principal amount.
        apr: The annual percentage rate as a decimal (e.g. 0.06 for 6%).
        term_months: The number of monthly payments.

    Returns:
        The fixed monthly payment amount, rounded to the nearest cent.

    """
    if apr == Decimal(0):
        return quantize_money(principal / term_months)

    monthly_rate = apr / 12
    factor = (1 + monthly_rate) ** term_months
    payment = principal * monthly_rate * factor / (factor - 1)
    return quantize_money(payment)


def amortization_schedule(
    principal: Decimal,
    apr: Decimal,
    term_months: int,
) -> list[MonthlyDataPoint]:
    """
    Generate a full month-by-month amortization schedule.

    Each month computes interest on the remaining balance, deducts
    principal, and tracks all components. The final payment is adjusted
    to clear the exact remaining balance, avoiding any residual.

    Args:
        principal: The loan principal amount.
        apr: The annual percentage rate as a decimal.
        term_months: The number of monthly payments.

    Returns:
        A list of MonthlyDataPoint entries, one per month.

    """
    payment = monthly_payment(principal, apr, term_months)
    monthly_rate = apr / 12
    balance = principal
    schedule: list[MonthlyDataPoint] = []

    for month in range(1, term_months + 1):
        interest = quantize_money(balance * monthly_rate)

        if month == term_months:
            # Final payment clears exact remaining balance
            principal_portion = balance
            actual_payment = interest + principal_portion
        else:
            principal_portion = payment - interest
            actual_payment = payment

        balance = balance - principal_portion

        schedule.append(
            MonthlyDataPoint(
                month=month,
                payment=quantize_money(actual_payment),
                interest_portion=interest,
                principal_portion=quantize_money(principal_portion),
                remaining_balance=quantize_money(balance),
                investment_balance=Decimal(0),
                cumulative_cost=Decimal(0),
            ),
        )

    return schedule
