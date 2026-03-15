"""
Engine orchestrator module.

Top-level comparison function that coordinates all calculation modules
to produce a ComparisonResult. The compare() function is the public API
that Phase 2 (web layer) will call.
"""

from decimal import Decimal

from fathom.amortization import amortization_schedule
from fathom.caveats import generate_all_caveats
from fathom.inflation import compute_inflation_adjustment, discount_cash_flows
from fathom.models import (
    ComparisonResult,
    FinancingOption,
    GlobalSettings,
    MonthlyDataPoint,
    OptionResult,
    OptionType,
    PromoResult,
)
from fathom.money import quantize_money
from fathom.opportunity import (
    compute_opportunity_cost,
    compute_opportunity_cost_per_period,
)
from fathom.tax import compute_tax_savings


def _determine_comparison_period(options: list[FinancingOption]) -> int:
    """
    Determine the comparison period from the longest loan term.

    Returns 0 if all options are cash (no investment modeling needed).

    Args:
        options: All financing options being compared.

    Returns:
        The comparison period in months.

    """
    terms = [
        opt.term_months
        for opt in options
        if opt.term_months is not None and opt.option_type != OptionType.CASH
    ]
    if not terms:
        return 0
    return max(terms)


def _build_cash_result(
    option: FinancingOption,
    settings: GlobalSettings,
    comparison_period: int,
) -> OptionResult:
    """
    Build result for a cash purchase option.

    Cash buyer pays full price upfront with no interest. Opportunity cost
    models the returns lost by spending the cash.

    Args:
        option: The cash financing option.
        settings: Global comparison settings.
        comparison_period: Normalized comparison period in months.

    Returns:
        An OptionResult for the cash option.

    """
    total_payments = option.purchase_price
    total_interest = Decimal(0)
    rebates = Decimal(0)

    # Opportunity cost: returns lost on the purchase price
    opp_cost = compute_opportunity_cost(option, settings, comparison_period)

    # Per-period opportunity cost
    opp_per_period = compute_opportunity_cost_per_period(
        option,
        settings,
        comparison_period,
    )

    # Inflation adjustment on cash: single payment at month 1
    inflation_adj = Decimal(0)
    cash_infl_month1 = Decimal(0)
    if settings.inflation_enabled and comparison_period > 0:
        inflation_adj = compute_inflation_adjustment(
            [total_payments],
            settings.inflation_rate,
        )
        # Per-period: only month 1 has a payment, so only month 1 has inflation adj
        cash_infl_month1 = inflation_adj

    # Build monthly data for cash -- single payment in month 1
    monthly_data: list[MonthlyDataPoint] = []
    if comparison_period > 0:
        cumulative = total_payments
        monthly_data.extend(
            MonthlyDataPoint(
                month=month,
                payment=total_payments if month == 1 else Decimal(0),
                interest_portion=Decimal(0),
                principal_portion=total_payments if month == 1 else Decimal(0),
                remaining_balance=Decimal(0),
                investment_balance=Decimal(0),
                cumulative_cost=cumulative,
                opportunity_cost=opp_per_period[month - 1]
                if month - 1 < len(opp_per_period)
                else Decimal(0),
                inflation_adjustment=cash_infl_month1 if month == 1 else Decimal(0),
                tax_savings=Decimal(0),
            )
            for month in range(1, comparison_period + 1)
        )

    tax_savings = Decimal(0)

    true_total_cost = total_payments + opp_cost - rebates - tax_savings + inflation_adj

    return OptionResult(
        total_payments=total_payments,
        total_interest=total_interest,
        opportunity_cost=opp_cost,
        tax_savings=tax_savings,
        inflation_adjustment=inflation_adj,
        rebates=rebates,
        true_total_cost=quantize_money(true_total_cost),
        monthly_data=monthly_data,
    )


def _build_loan_result(
    option: FinancingOption,
    settings: GlobalSettings,
    comparison_period: int,
) -> OptionResult:
    """
    Build result for a loan-based financing option.

    Generates the amortization schedule, computes opportunity cost,
    and optionally applies inflation adjustment and tax savings.

    Args:
        option: The loan financing option.
        settings: Global comparison settings.
        comparison_period: Normalized comparison period in months.

    Returns:
        An OptionResult for the loan option.

    """
    apr = option.apr if option.apr is not None else Decimal(0)
    term = option.term_months if option.term_months is not None else comparison_period
    down = option.down_payment if option.down_payment is not None else Decimal(0)
    principal = option.purchase_price - down

    # Generate amortization schedule
    schedule = amortization_schedule(principal, apr, term)

    total_payments = down + sum((dp.payment for dp in schedule), Decimal(0))
    total_interest = sum((dp.interest_portion for dp in schedule), Decimal(0))

    # Rebates
    rebates = Decimal(0)
    if option.option_type == OptionType.PROMO_CASH_BACK and option.cash_back_amount:
        rebates = option.cash_back_amount
    elif (
        option.option_type == OptionType.PROMO_PRICE_REDUCTION
        and option.discounted_price is not None
    ):
        rebates = option.purchase_price - option.discounted_price

    # Opportunity cost
    opp_cost = compute_opportunity_cost(option, settings, comparison_period)

    # Inflation adjustment
    inflation_adj = Decimal(0)
    if settings.inflation_enabled:
        payments_list = [dp.payment for dp in schedule]
        inflation_adj = compute_inflation_adjustment(
            payments_list,
            settings.inflation_rate,
        )

    # Tax savings
    tax_savings = Decimal(0)
    if settings.tax_enabled:
        interest_list = [dp.interest_portion for dp in schedule]
        tax_savings = compute_tax_savings(interest_list, settings.tax_rate)

    true_total_cost = total_payments + opp_cost - rebates - tax_savings + inflation_adj

    # Compute per-period cost factors
    opp_per_period = compute_opportunity_cost_per_period(
        option,
        settings,
        comparison_period,
    )

    # Per-period inflation: difference between nominal and discounted per month
    infl_per_period: list[Decimal] = []
    if settings.inflation_enabled:
        payments_list = [dp.payment for dp in schedule]
        discounted = discount_cash_flows(payments_list, settings.inflation_rate)
        infl_per_period = [
            quantize_money(nom - disc)
            for nom, disc in zip(payments_list, discounted, strict=True)
        ]
    else:
        infl_per_period = [Decimal(0)] * len(schedule)

    # Per-period tax savings
    tax_per_period: list[Decimal] = []
    if settings.tax_enabled:
        tax_per_period = [
            quantize_money(dp.interest_portion * settings.tax_rate) for dp in schedule
        ]
    else:
        tax_per_period = [Decimal(0)] * len(schedule)

    # Build monthly data with cumulative cost and per-period factors
    monthly_data: list[MonthlyDataPoint] = []
    cumulative = down
    for i, dp in enumerate(schedule):
        cumulative = cumulative + dp.payment
        monthly_data.append(
            MonthlyDataPoint(
                month=dp.month,
                payment=dp.payment,
                interest_portion=dp.interest_portion,
                principal_portion=dp.principal_portion,
                remaining_balance=dp.remaining_balance,
                investment_balance=Decimal(0),
                cumulative_cost=quantize_money(cumulative),
                opportunity_cost=opp_per_period[i],
                inflation_adjustment=infl_per_period[i],
                tax_savings=tax_per_period[i],
            ),
        )

    # Pad monthly data to comparison period if loan is shorter
    if term < comparison_period:
        final_cumulative = quantize_money(cumulative)
        for month in range(term + 1, comparison_period + 1):
            pad_idx = month - 1
            monthly_data.append(
                MonthlyDataPoint(
                    month=month,
                    payment=Decimal(0),
                    interest_portion=Decimal(0),
                    principal_portion=Decimal(0),
                    remaining_balance=Decimal(0),
                    investment_balance=Decimal(0),
                    cumulative_cost=final_cumulative,
                    opportunity_cost=opp_per_period[pad_idx]
                    if pad_idx < len(opp_per_period)
                    else Decimal(0),
                    inflation_adjustment=Decimal(0),
                    tax_savings=Decimal(0),
                ),
            )

    return OptionResult(
        total_payments=quantize_money(total_payments),
        total_interest=quantize_money(total_interest),
        opportunity_cost=opp_cost,
        tax_savings=tax_savings,
        inflation_adjustment=inflation_adj,
        rebates=rebates,
        true_total_cost=quantize_money(true_total_cost),
        monthly_data=monthly_data,
    )


def _build_promo_result(
    option: FinancingOption,
    settings: GlobalSettings,
    comparison_period: int,
) -> PromoResult:
    """
    Build dual-outcome result for a zero-percent promo option.

    Models both scenarios: paid off in time (no interest) and not paid
    off in time (remaining balance + retroactive interest at post-promo APR).

    Args:
        option: The promo zero-percent financing option.
        settings: Global comparison settings.
        comparison_period: Normalized comparison period in months.

    Returns:
        A PromoResult with both paid_on_time and not_paid_on_time outcomes.

    """
    term = option.term_months if option.term_months is not None else comparison_period
    post_apr = (
        option.post_promo_apr if option.post_promo_apr is not None else Decimal(0)
    )
    down = option.down_payment if option.down_payment is not None else Decimal(0)
    principal = option.purchase_price - down

    # Required monthly payment to pay off in time
    required_monthly = quantize_money(principal / term) if term > 0 else Decimal(0)

    # Paid on time: 0% interest for the promo term
    paid_option = FinancingOption(
        option_type=OptionType.TRADITIONAL_LOAN,
        label=option.label,
        purchase_price=option.purchase_price,
        apr=Decimal(0),
        term_months=term,
        down_payment=option.down_payment,
    )
    paid_on_time = _build_loan_result(paid_option, settings, comparison_period)

    # Not paid on time: assume minimum payments don't clear balance,
    # then remaining balance amortized at post-promo APR
    # Model: 0% for promo term, then remaining at post-promo APR
    # For simplicity, assume half the balance remains after promo term
    # and is amortized at post-promo APR for the same term
    remaining_term = comparison_period - term if comparison_period > term else term

    if option.deferred_interest and option.retroactive_interest:
        # Retroactive interest: full principal at post-promo APR from day 1
        not_paid_option = FinancingOption(
            option_type=OptionType.TRADITIONAL_LOAN,
            label=option.label,
            purchase_price=option.purchase_price,
            apr=post_apr,
            term_months=remaining_term if remaining_term > 0 else term,
            down_payment=option.down_payment,
        )
    else:
        # Forward-only: remaining balance at post-promo APR
        not_paid_option = FinancingOption(
            option_type=OptionType.TRADITIONAL_LOAN,
            label=option.label,
            purchase_price=option.purchase_price,
            apr=post_apr,
            term_months=remaining_term if remaining_term > 0 else term,
            down_payment=option.down_payment,
        )

    not_paid_on_time = _build_loan_result(not_paid_option, settings, comparison_period)

    break_even_month = term

    return PromoResult(
        paid_on_time=paid_on_time,
        not_paid_on_time=not_paid_on_time,
        required_monthly_payment=required_monthly,
        break_even_month=break_even_month,
    )


def compare(
    options: list[FinancingOption],
    settings: GlobalSettings,
) -> ComparisonResult:
    """
    Compare multiple financing options and return a comprehensive result.

    This is the top-level public API for the calculation engine. It:
    1. Normalizes the comparison period to the longest loan term
    2. Computes results for each option based on type
    3. Generates risk caveats for all options
    4. Returns a ComparisonResult ready for display

    Args:
        options: List of financing options to compare.
        settings: Global comparison settings.

    Returns:
        A ComparisonResult with per-option results and caveats.

    """
    comparison_period = _determine_comparison_period(options)

    results: dict[str, OptionResult | PromoResult] = {}

    for option in options:
        if option.option_type == OptionType.CASH:
            results[option.label] = _build_cash_result(
                option,
                settings,
                comparison_period,
            )
        elif option.option_type == OptionType.PROMO_ZERO_PERCENT:
            results[option.label] = _build_promo_result(
                option,
                settings,
                comparison_period,
            )
        else:
            results[option.label] = _build_loan_result(
                option,
                settings,
                comparison_period,
            )

    # Generate caveats for all options
    caveats = generate_all_caveats(options, results, settings, comparison_period)

    return ComparisonResult(
        results=results,
        comparison_period_months=comparison_period,
        caveats=caveats,
    )
