"""
Engine orchestrator module.

Top-level comparison function that coordinates all calculation modules
to produce a ComparisonResult. The compare() function is the public API
that Phase 2 (web layer) will call.
"""

from dataclasses import dataclass
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
    Determine the comparison period from the longest effective term.

    For promo options with a post-promo APR, the not-paid-on-time scenario
    spans 2x the promo term (promo period + post-promo amortization). This
    ensures charts, padding, and opportunity cost calculations cover the
    full timeline.

    Returns 0 if all options are cash (no investment modeling needed).

    Args:
        options: All financing options being compared.

    Returns:
        The comparison period in months.

    """
    terms: list[int] = []
    for opt in options:
        if opt.term_months is None or opt.option_type == OptionType.CASH:
            continue
        if (
            opt.option_type == OptionType.PROMO_ZERO_PERCENT
            and opt.post_promo_apr is not None
            and opt.post_promo_apr > Decimal(0)
        ):
            # Not-paid-on-time spans promo period + post-promo amortization
            terms.append(opt.term_months * 2)
        else:
            terms.append(opt.term_months)
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


@dataclass
class _PromoContext:
    """Bundle of promo calculation parameters passed between helpers."""

    principal: Decimal
    down: Decimal
    min_payment: Decimal
    term: int
    post_promo_balance: Decimal
    post_apr: Decimal


def _build_promo_phases(ctx: _PromoContext) -> list[MonthlyDataPoint]:
    """
    Build the two-phase MonthlyDataPoint series for a not-paid promo scenario.

    Phase 1: minimum payments during the promo period at 0% interest.
    Phase 2: amortization of the post-promo balance at the post-promo APR.

    Args:
        ctx: Promo calculation context with all required parameters.

    Returns:
        A list of MonthlyDataPoint entries covering months 1 through 2*term.

    """
    data: list[MonthlyDataPoint] = []
    balance = ctx.principal
    cumulative = ctx.down

    # Phase 1: promo period (months 1 to term)
    for month in range(1, ctx.term + 1):
        balance = balance - ctx.min_payment
        cumulative = cumulative + ctx.min_payment
        data.append(
            MonthlyDataPoint(
                month=month,
                payment=ctx.min_payment,
                interest_portion=Decimal(0),
                principal_portion=ctx.min_payment,
                remaining_balance=quantize_money(balance),
                investment_balance=Decimal(0),
                cumulative_cost=quantize_money(cumulative),
            ),
        )

    # Phase 2: post-promo amortization (months term+1 to 2*term)
    post_schedule = amortization_schedule(
        ctx.post_promo_balance,
        ctx.post_apr,
        ctx.term,
    )
    for dp in post_schedule:
        cumulative = cumulative + dp.payment
        data.append(
            MonthlyDataPoint(
                month=dp.month + ctx.term,
                payment=dp.payment,
                interest_portion=dp.interest_portion,
                principal_portion=dp.principal_portion,
                remaining_balance=dp.remaining_balance,
                investment_balance=Decimal(0),
                cumulative_cost=quantize_money(cumulative),
            ),
        )

    return data


def _compute_promo_opp_cost(
    all_data: list[MonthlyDataPoint],
    ctx: _PromoContext,
    settings: GlobalSettings,
    comparison_period: int,
) -> tuple[Decimal, list[Decimal]]:
    """
    Compute opportunity cost for a two-phase promo payment stream.

    Uses a pool model where the investment pool grows by monthly returns
    then has payments deducted. Pads with freed-cash contributions if
    the comparison period exceeds the total timeline.

    Args:
        all_data: Combined phase 1 + phase 2 MonthlyDataPoint list.
        ctx: Promo calculation context.
        settings: Global comparison settings.
        comparison_period: Total comparison period in months.

    Returns:
        A tuple of (total_opp_cost, per_period_opp_cost_list).

    """
    total_timeline = ctx.term * 2
    monthly_rate = settings.return_rate / 12
    pool = ctx.principal
    total_opp = Decimal(0)
    opp_per_period: list[Decimal] = []

    for dp in all_data:
        growth = pool * monthly_rate
        total_opp += growth
        opp_per_period.append(quantize_money(growth))
        pool = pool + growth - dp.payment
        pool = max(pool, Decimal(0))

    # Pad opportunity cost to comparison period
    remaining_cp = comparison_period - total_timeline
    if remaining_cp > 0:
        freed_pool = Decimal(0)
        for _m in range(remaining_cp):
            freed_pool = freed_pool + ctx.min_payment
            growth = freed_pool * monthly_rate
            total_opp += growth
            opp_per_period.append(quantize_money(growth))
            freed_pool = freed_pool + growth

    return quantize_money(total_opp), opp_per_period


def _compute_promo_inflation(
    all_data: list[MonthlyDataPoint],
    settings: GlobalSettings,
) -> tuple[Decimal, list[Decimal]]:
    """
    Compute inflation adjustment for a promo payment stream.

    Args:
        all_data: Combined phase 1 + phase 2 MonthlyDataPoint list.
        settings: Global comparison settings.

    Returns:
        A tuple of (aggregate_inflation_adj, per_period_inflation_list).

    """
    if settings.inflation_enabled:
        payments_list = [dp.payment for dp in all_data]
        inflation_adj = compute_inflation_adjustment(
            payments_list,
            settings.inflation_rate,
        )
        discounted = discount_cash_flows(payments_list, settings.inflation_rate)
        infl_per_period = [
            quantize_money(nom - disc)
            for nom, disc in zip(payments_list, discounted, strict=True)
        ]
        return inflation_adj, infl_per_period
    return Decimal(0), [Decimal(0)] * len(all_data)


def _compute_promo_tax(
    all_data: list[MonthlyDataPoint],
    settings: GlobalSettings,
) -> tuple[Decimal, list[Decimal]]:
    """
    Compute tax savings for a promo payment stream.

    Args:
        all_data: Combined phase 1 + phase 2 MonthlyDataPoint list.
        settings: Global comparison settings.

    Returns:
        A tuple of (aggregate_tax_savings, per_period_tax_list).

    """
    if settings.tax_enabled:
        interest_list = [dp.interest_portion for dp in all_data]
        tax_savings = compute_tax_savings(interest_list, settings.tax_rate)
        tax_per_period = [
            quantize_money(dp.interest_portion * settings.tax_rate) for dp in all_data
        ]
        return tax_savings, tax_per_period
    return Decimal(0), [Decimal(0)] * len(all_data)


def _build_not_paid_result(
    ctx: _PromoContext,
    all_data: list[MonthlyDataPoint],
    settings: GlobalSettings,
    comparison_period: int,
) -> OptionResult:
    """
    Build the not-paid-on-time OptionResult from a two-phase schedule.

    Computes aggregates (totals, opportunity cost, inflation, tax), enriches
    the MonthlyDataPoint entries with per-period cost factors, pads to the
    comparison period, and returns the assembled OptionResult.

    Args:
        ctx: Promo calculation context.
        all_data: Combined phase 1 + phase 2 MonthlyDataPoint list.
        settings: Global comparison settings.
        comparison_period: Total comparison period in months.

    Returns:
        An OptionResult for the not-paid-on-time scenario.

    """
    total_timeline = ctx.term * 2

    # Aggregates
    total_payments = ctx.down + sum(dp.payment for dp in all_data)
    total_interest = sum((dp.interest_portion for dp in all_data), Decimal(0))

    opp_cost, opp_per_period = _compute_promo_opp_cost(
        all_data,
        ctx,
        settings,
        comparison_period,
    )
    inflation_adj, infl_per_period = _compute_promo_inflation(all_data, settings)
    tax_savings, tax_per_period = _compute_promo_tax(all_data, settings)

    rebates = Decimal(0)
    true_total_cost = total_payments + opp_cost - rebates - tax_savings + inflation_adj

    # Enrich with per-period cost factors
    monthly_data: list[MonthlyDataPoint] = [
        MonthlyDataPoint(
            month=dp.month,
            payment=dp.payment,
            interest_portion=dp.interest_portion,
            principal_portion=dp.principal_portion,
            remaining_balance=dp.remaining_balance,
            investment_balance=Decimal(0),
            cumulative_cost=dp.cumulative_cost,
            opportunity_cost=opp_per_period[i]
            if i < len(opp_per_period)
            else Decimal(0),
            inflation_adjustment=infl_per_period[i],
            tax_savings=tax_per_period[i],
        )
        for i, dp in enumerate(all_data)
    ]

    # Pad to comparison period if needed
    if total_timeline < comparison_period:
        final_cumulative = (
            monthly_data[-1].cumulative_cost if monthly_data else ctx.down
        )
        for month in range(total_timeline + 1, comparison_period + 1):
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


# Worked numeric example for _build_promo_result:
#
#   $10K purchase, 24.99% APR, 12-month promo, no down payment
#   required_monthly = $10,000 / 12 = $833.33
#   min_payment = $833.33 / 2 = $416.67
#
#   Phase 1 (promo, months 1-12): pay $416.67/mo at 0% interest
#     Remaining at month 12: $10,000 - (12 * $416.67) = $4,999.96
#
#   Retroactive scenario (deferred_interest + retroactive_interest):
#     Retroactive interest = $10,000 * 24.99% * 1yr = $2,499.00
#     Post-promo balance = $4,999.96 + $2,499.00 = $7,498.96
#     Amortized at 24.99% for 12 months
#
#   Forward-only scenario:
#     Post-promo balance = $4,999.96 (no retroactive interest)
#     Amortized at 24.99% for 12 months
#
#   Paid on time scenario:
#     $10,000 at 0% for 12 months = $833.33/mo, total $10,000
#
#   Invariant: retroactive cost > forward-only cost > paid-on-time cost


def _build_promo_result(
    option: FinancingOption,
    settings: GlobalSettings,
    comparison_period: int,
) -> PromoResult:
    """
    Build dual-outcome result for a zero-percent promo option.

    Models both scenarios: paid off in time (no interest) and not paid off
    in time (two-phase schedule with minimum payments during promo then
    amortization at post-promo APR).

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

    # Not paid on time: two-phase schedule
    min_payment = quantize_money(required_monthly / 2)

    # Compute post-promo balance
    remaining_principal = quantize_money(principal - term * min_payment)
    if option.deferred_interest and option.retroactive_interest:
        retro_interest = quantize_money(
            principal * post_apr * Decimal(term) / Decimal(12)
        )
        post_promo_balance = remaining_principal + retro_interest
    else:
        post_promo_balance = remaining_principal

    ctx = _PromoContext(
        principal=principal,
        down=down,
        min_payment=min_payment,
        term=term,
        post_promo_balance=post_promo_balance,
        post_apr=post_apr,
    )

    not_paid_on_time = _build_not_paid_result(
        ctx,
        all_data=_build_promo_phases(ctx),
        settings=settings,
        comparison_period=comparison_period,
    )

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
