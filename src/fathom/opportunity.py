"""
Opportunity cost calculation module.

Models investment returns on cash that could be invested instead of
being spent on purchases or loan payments. Uses a decreasing investment
pool model where the pool grows by monthly returns then has payments
deducted.
"""

from decimal import Decimal

from fathom.amortization import monthly_payment
from fathom.models import FinancingOption, GlobalSettings, OptionType

CENTS = Decimal("0.01")


def quantize_money(value: Decimal) -> Decimal:
    """Round a Decimal value to the nearest cent (two decimal places)."""
    return value.quantize(CENTS)


def _compute_pool_series(
    initial_pool: Decimal,
    monthly_deduction: Decimal,
    annual_return: Decimal,
    months: int,
) -> list[Decimal]:
    """
    Compute the monthly investment pool balances.

    Each month the pool grows by the monthly return rate, then the
    monthly deduction is subtracted. The pool clamps to zero and
    stays there once exhausted.

    Args:
        initial_pool: Starting investment amount.
        monthly_deduction: Amount deducted each month (e.g. loan payment).
        annual_return: Annual investment return rate as a decimal.
        months: Number of months to simulate.

    Returns:
        A list of monthly pool balances (length = months).

    """
    monthly_rate = annual_return / 12
    pool = initial_pool
    balances: list[Decimal] = []

    for _month in range(months):
        pool = pool * (1 + monthly_rate)
        pool = pool - monthly_deduction
        if pool < Decimal(0):
            pool = Decimal(0)
        balances.append(quantize_money(pool))

    return balances


def _compute_freed_cash_series(
    monthly_contribution: Decimal,
    annual_return: Decimal,
    months: int,
) -> list[Decimal]:
    """
    Compute investment balances from monthly contributions.

    Models investing the freed-up payment amount after a loan ends,
    for the remaining months of the comparison period.

    Args:
        monthly_contribution: Amount invested each month.
        annual_return: Annual investment return rate as a decimal.
        months: Number of months of contributions.

    Returns:
        A list of monthly balances (length = months).

    """
    monthly_rate = annual_return / 12
    pool = Decimal(0)
    balances: list[Decimal] = []

    for _month in range(months):
        pool = pool + monthly_contribution
        pool = pool * (1 + monthly_rate)
        balances.append(quantize_money(pool))

    return balances


def compute_opportunity_cost(
    option: FinancingOption,
    settings: GlobalSettings,
    comparison_period: int,
) -> Decimal:
    """
    Compute the total opportunity cost for a financing option.

    Opportunity cost represents the investment returns earned from cash
    that is available for investing. The calculation tracks:
    - Initial pool value and its growth via returns
    - Deductions for loan payments (which reduce the pool)
    - Freed-cash contributions after a shorter loan ends

    The total opportunity cost equals the sum of all investment returns
    (pool growth) across the comparison period.

    Args:
        option: The financing option to analyze.
        settings: Global settings including investment return rate.
        comparison_period: Total comparison period in months.

    Returns:
        The total opportunity cost (investment returns earned) as a Decimal.

    """
    if option.option_type == OptionType.CASH:
        initial_pool = option.purchase_price
        monthly_deduction = Decimal(0)
        term = comparison_period
    else:
        apr = option.apr if option.apr is not None else Decimal(0)
        term = (
            option.term_months if option.term_months is not None else comparison_period
        )
        down = option.down_payment if option.down_payment is not None else Decimal(0)
        initial_pool = option.purchase_price - down
        monthly_deduction = monthly_payment(initial_pool, apr, term)

    monthly_rate = settings.return_rate / 12
    pool = initial_pool
    total_returns = Decimal(0)
    loan_months = min(term, comparison_period)

    # Phase 1: pool decreasing during loan payments
    for _month in range(loan_months):
        growth = pool * monthly_rate
        total_returns += growth
        pool = pool + growth - monthly_deduction
        if pool < Decimal(0):
            pool = Decimal(0)

    # Phase 2: freed-cash investment after loan ends
    remaining_months = comparison_period - loan_months
    if remaining_months > 0 and option.option_type != OptionType.CASH:
        freed_pool = Decimal(0)
        for _month in range(remaining_months):
            freed_pool = freed_pool + monthly_deduction
            growth = freed_pool * monthly_rate
            total_returns += growth
            freed_pool = freed_pool + growth

    return quantize_money(total_returns)


def compute_opportunity_cost_series(
    option: FinancingOption,
    settings: GlobalSettings,
    comparison_period: int,
) -> list[Decimal]:
    """
    Compute the monthly investment pool balances for an option.

    Combines the decreasing pool during the loan term with any
    freed-cash investment after the loan ends.

    Args:
        option: The financing option to analyze.
        settings: Global settings including investment return rate.
        comparison_period: Total comparison period in months.

    Returns:
        A list of monthly investment pool balances.

    """
    if option.option_type == OptionType.CASH:
        # Cash buyer: full price invested, no deductions
        return _compute_pool_series(
            initial_pool=option.purchase_price,
            monthly_deduction=Decimal(0),
            annual_return=settings.return_rate,
            months=comparison_period,
        )

    # Loan buyer
    apr = option.apr if option.apr is not None else Decimal(0)
    term = option.term_months if option.term_months is not None else comparison_period
    down = option.down_payment if option.down_payment is not None else Decimal(0)

    initial_pool = option.purchase_price - down
    payment = monthly_payment(initial_pool, apr, term)

    loan_months = min(term, comparison_period)
    loan_series = _compute_pool_series(
        initial_pool=initial_pool,
        monthly_deduction=payment,
        annual_return=settings.return_rate,
        months=loan_months,
    )

    remaining_months = comparison_period - loan_months
    if remaining_months > 0:
        freed_series = _compute_freed_cash_series(
            monthly_contribution=payment,
            annual_return=settings.return_rate,
            months=remaining_months,
        )
        loan_series.extend(freed_series)

    return loan_series
