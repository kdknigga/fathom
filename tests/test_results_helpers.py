"""
Unit tests for the results analysis module.

Tests winner detection, savings calculation, breakdown row generation,
options data construction, and recommendation text generation.
"""

from decimal import Decimal

from fathom.models import (
    ComparisonResult,
    FinancingOption,
    GlobalSettings,
    MonthlyDataPoint,
    OptionResult,
    OptionType,
    PromoResult,
)
from fathom.results import (
    aggregate_annual,
    analyze_results,
    build_compare_data,
    build_detailed_breakdown,
    generate_recommendation_text,
)


def _make_option_result(
    true_total_cost: Decimal,
    total_payments: Decimal | None = None,
    total_interest: Decimal = Decimal(0),
    opportunity_cost: Decimal = Decimal(0),
    tax_savings: Decimal = Decimal(0),
    inflation_adjustment: Decimal = Decimal(0),
    rebates: Decimal = Decimal(0),
) -> OptionResult:
    """Build an OptionResult with the given true_total_cost and defaults."""
    return OptionResult(
        total_payments=total_payments
        if total_payments is not None
        else true_total_cost,
        total_interest=total_interest,
        opportunity_cost=opportunity_cost,
        tax_savings=tax_savings,
        inflation_adjustment=inflation_adjustment,
        rebates=rebates,
        true_total_cost=true_total_cost,
        monthly_data=[
            MonthlyDataPoint(
                month=1,
                payment=true_total_cost,
                interest_portion=Decimal(0),
                principal_portion=true_total_cost,
                remaining_balance=Decimal(0),
                investment_balance=Decimal(0),
                cumulative_cost=true_total_cost,
            ),
        ],
    )


def _make_cash_option(label: str, price: Decimal) -> FinancingOption:
    """Build a cash FinancingOption."""
    return FinancingOption(
        option_type=OptionType.CASH,
        label=label,
        purchase_price=price,
    )


def _make_loan_option(
    label: str,
    price: Decimal,
    apr: Decimal = Decimal("0.06"),
    term: int = 36,
) -> FinancingOption:
    """Build a traditional loan FinancingOption."""
    return FinancingOption(
        option_type=OptionType.TRADITIONAL_LOAN,
        label=label,
        purchase_price=price,
        apr=apr,
        term_months=term,
    )


class TestWinnerDetection:
    """Tests for winner detection logic in analyze_results."""

    def test_winner_detection_basic(self):
        """Cash at $25000 vs Loan at $27500 -- cash wins."""
        cash_result = _make_option_result(Decimal(25000))
        loan_result = _make_option_result(
            Decimal(27500),
            total_interest=Decimal(2500),
        )
        comparison = ComparisonResult(
            results={"Cash": cash_result, "Loan": loan_result},
            comparison_period_months=36,
            caveats=[],
        )
        options = [
            _make_cash_option("Cash", Decimal(25000)),
            _make_loan_option("Loan", Decimal(25000)),
        ]

        display = analyze_results(comparison, options)

        assert display["winner_name"] == "Cash"
        assert display["winner_cost"] == Decimal(25000)

    def test_winner_detection_promo(self):
        """PromoResult uses paid_on_time cost for winner detection."""
        paid_on_time = _make_option_result(Decimal(24000))
        not_paid_on_time = _make_option_result(Decimal(30000))
        promo_result = PromoResult(
            paid_on_time=paid_on_time,
            not_paid_on_time=not_paid_on_time,
            required_monthly_payment=Decimal(2000),
            break_even_month=12,
        )
        loan_result = _make_option_result(Decimal(27500))

        comparison = ComparisonResult(
            results={"Promo": promo_result, "Loan": loan_result},
            comparison_period_months=36,
            caveats=[],
        )
        options = [
            FinancingOption(
                option_type=OptionType.PROMO_ZERO_PERCENT,
                label="Promo",
                purchase_price=Decimal(25000),
                term_months=12,
                post_promo_apr=Decimal("0.2499"),
                deferred_interest=True,
            ),
            _make_loan_option("Loan", Decimal(25000)),
        ]

        display = analyze_results(comparison, options)

        assert display["winner_name"] == "Promo"
        assert display["winner_cost"] == Decimal(24000)


class TestSavingsCalculation:
    """Tests for savings calculation."""

    def test_savings_calculation(self):
        """Savings = runner_up cost - winner cost."""
        cash_result = _make_option_result(Decimal(25000))
        loan_result = _make_option_result(Decimal(27500))
        comparison = ComparisonResult(
            results={"Cash": cash_result, "Loan": loan_result},
            comparison_period_months=36,
            caveats=[],
        )
        options = [
            _make_cash_option("Cash", Decimal(25000)),
            _make_loan_option("Loan", Decimal(25000)),
        ]

        display = analyze_results(comparison, options)

        assert display["savings"] == Decimal(2500)

    def test_single_option_no_savings(self):
        """With only 1 option, savings is 0, runner_up_name is None."""
        cash_result = _make_option_result(Decimal(25000))
        comparison = ComparisonResult(
            results={"Cash": cash_result},
            comparison_period_months=0,
            caveats=[],
        )
        options = [_make_cash_option("Cash", Decimal(25000))]

        display = analyze_results(comparison, options)

        assert display["savings"] == Decimal(0)
        assert display["runner_up_name"] is None


class TestBreakdownRows:
    """Tests for breakdown row generation."""

    def test_breakdown_rows_skip_zero(self):
        """Rows where ALL options have $0 are excluded."""
        # Both options have zero rebates and zero tax_savings
        cash_result = _make_option_result(Decimal(25000))
        loan_result = _make_option_result(Decimal(27500))
        comparison = ComparisonResult(
            results={"Cash": cash_result, "Loan": loan_result},
            comparison_period_months=36,
            caveats=[],
        )
        options = [
            _make_cash_option("Cash", Decimal(25000)),
            _make_loan_option("Loan", Decimal(25000)),
        ]

        display = analyze_results(comparison, options)
        row_labels = [row["label"] for row in display["breakdown_rows"]]

        assert "Rebates" not in row_labels
        assert "Tax Savings" not in row_labels

    def test_breakdown_rows_include_nonzero(self):
        """Rows are shown when at least one option has a nonzero value."""
        cash_result = _make_option_result(Decimal(25000), rebates=Decimal(500))
        loan_result = _make_option_result(Decimal(27500))
        comparison = ComparisonResult(
            results={"Cash": cash_result, "Loan": loan_result},
            comparison_period_months=36,
            caveats=[],
        )
        options = [
            _make_cash_option("Cash", Decimal(25000)),
            _make_loan_option("Loan", Decimal(25000)),
        ]

        display = analyze_results(comparison, options)
        row_labels = [row["label"] for row in display["breakdown_rows"]]

        assert "Rebates" in row_labels


class TestOptionsData:
    """Tests for options_data construction."""

    def test_options_data_promo_flag(self):
        """PromoResult options have is_promo=True."""
        paid_on_time = _make_option_result(Decimal(24000))
        not_paid_on_time = _make_option_result(Decimal(30000))
        promo_result = PromoResult(
            paid_on_time=paid_on_time,
            not_paid_on_time=not_paid_on_time,
            required_monthly_payment=Decimal(2000),
            break_even_month=12,
        )
        loan_result = _make_option_result(Decimal(27500))

        comparison = ComparisonResult(
            results={"Promo": promo_result, "Loan": loan_result},
            comparison_period_months=36,
            caveats=[],
        )
        options = [
            FinancingOption(
                option_type=OptionType.PROMO_ZERO_PERCENT,
                label="Promo",
                purchase_price=Decimal(25000),
                term_months=12,
                post_promo_apr=Decimal("0.2499"),
                deferred_interest=True,
            ),
            _make_loan_option("Loan", Decimal(25000)),
        ]

        display = analyze_results(comparison, options)
        promo_data = next(o for o in display["options_data"] if o["name"] == "Promo")
        loan_data = next(o for o in display["options_data"] if o["name"] == "Loan")

        assert promo_data["is_promo"] is True
        assert loan_data["is_promo"] is False


class TestRecommendationText:
    """Tests for recommendation text generation."""

    def test_recommendation_text_returns_string(self):
        """generate_recommendation_text returns a non-empty string."""
        cash_result = _make_option_result(Decimal(25000))
        loan_result = _make_option_result(Decimal(27500))
        comparison = ComparisonResult(
            results={"Cash": cash_result, "Loan": loan_result},
            comparison_period_months=36,
            caveats=[],
        )

        text = generate_recommendation_text(
            "Cash",
            Decimal(2500),
            comparison,
        )

        assert isinstance(text, str)
        assert len(text) > 0


def _make_multi_month_option_result(
    months: int = 12,
    payment: Decimal = Decimal(100),
) -> OptionResult:
    """Build an OptionResult with multiple monthly data points."""
    monthly_data = [
        MonthlyDataPoint(
            month=m + 1,
            payment=payment,
            interest_portion=Decimal(5),
            principal_portion=Decimal(95),
            remaining_balance=Decimal(1000) - Decimal(95) * (m + 1),
            investment_balance=Decimal(0),
            cumulative_cost=payment * (m + 1),
            opportunity_cost=Decimal(2),
            inflation_adjustment=Decimal(1),
            tax_savings=Decimal(3),
        )
        for m in range(months)
    ]
    return OptionResult(
        total_payments=payment * months,
        total_interest=Decimal(5) * months,
        opportunity_cost=Decimal(2) * months,
        tax_savings=Decimal(3) * months,
        inflation_adjustment=Decimal(1) * months,
        rebates=Decimal(0),
        true_total_cost=payment * months,
        monthly_data=monthly_data,
    )


class TestBuildDetailedBreakdown:
    """Tests for build_detailed_breakdown function."""

    def test_returns_correct_structure(self):
        """build_detailed_breakdown returns list of dicts with required keys."""
        result = _make_multi_month_option_result(months=3)
        options_data = [
            {
                "name": "Loan",
                "is_promo": False,
                "is_winner": True,
                "result": result,
            },
        ]
        settings = GlobalSettings(return_rate=Decimal("0.07"))

        breakdown = build_detailed_breakdown(options_data, 3, settings)

        assert len(breakdown) == 1
        entry = breakdown[0]
        assert entry["name"] == "Loan"
        assert entry["is_winner"] is True
        assert len(entry["rows"]) == 3
        assert "totals" in entry

    def test_monthly_rows_have_required_fields(self):
        """Each row dict has all required period data fields."""
        result = _make_multi_month_option_result(months=2)
        options_data = [
            {
                "name": "Loan",
                "is_promo": False,
                "is_winner": True,
                "result": result,
            },
        ]
        settings = GlobalSettings(return_rate=Decimal("0.07"))

        breakdown = build_detailed_breakdown(options_data, 2, settings)
        row = breakdown[0]["rows"][0]

        assert "period" in row
        assert "payment" in row
        assert "cumulative_true_total_cost" in row

    def test_annual_granularity(self):
        """build_detailed_breakdown with annual granularity groups by year."""
        result = _make_multi_month_option_result(months=24)
        options_data = [
            {
                "name": "Loan",
                "is_promo": False,
                "is_winner": True,
                "result": result,
            },
        ]
        settings = GlobalSettings(return_rate=Decimal("0.07"))

        breakdown = build_detailed_breakdown(
            options_data,
            24,
            settings,
            granularity="annual",
        )

        assert len(breakdown[0]["rows"]) == 2
        assert breakdown[0]["rows"][0]["period"] == "Year 1"
        assert breakdown[0]["rows"][1]["period"] == "Year 2"


class TestAggregateAnnual:
    """Tests for aggregate_annual function."""

    def test_groups_12_month_chunks(self):
        """aggregate_annual groups 12 months into Year 1, remainder into Year 2."""
        monthly_rows = [
            {
                "period": m + 1,
                "payment": Decimal(100),
                "interest_portion": Decimal(5),
                "principal_portion": Decimal(95),
                "opportunity_cost": Decimal(2),
                "inflation_adjustment": Decimal(1),
                "tax_savings": Decimal(3),
                "cumulative_true_total_cost": Decimal(100) * (m + 1),
            }
            for m in range(15)
        ]

        annual = aggregate_annual(monthly_rows)

        assert len(annual) == 2
        assert annual[0]["period"] == "Year 1"
        assert annual[1]["period"] == "Year 2"
        # Year 1 sums 12 months of $100 payment
        assert annual[0]["payment"] == Decimal(1200)
        # Year 2 sums 3 months
        assert annual[1]["payment"] == Decimal(300)

    def test_cumulative_uses_last_month(self):
        """aggregate_annual cumulative uses last month value in each group."""
        monthly_rows = [
            {
                "period": m + 1,
                "payment": Decimal(100),
                "interest_portion": Decimal(0),
                "principal_portion": Decimal(0),
                "opportunity_cost": Decimal(0),
                "inflation_adjustment": Decimal(0),
                "tax_savings": Decimal(0),
                "cumulative_true_total_cost": Decimal(100) * (m + 1),
            }
            for m in range(12)
        ]

        annual = aggregate_annual(monthly_rows)

        assert annual[0]["cumulative_true_total_cost"] == Decimal(1200)


class TestBuildCompareData:
    """Tests for build_compare_data function."""

    def test_returns_per_option_columns(self):
        """build_compare_data returns rows with per-option payment and cumulative."""
        result1 = _make_multi_month_option_result(months=3, payment=Decimal(100))
        result2 = _make_multi_month_option_result(months=3, payment=Decimal(200))
        options_data = [
            {
                "name": "Cash",
                "is_promo": False,
                "is_winner": True,
                "result": result1,
            },
            {
                "name": "Loan",
                "is_promo": False,
                "is_winner": False,
                "result": result2,
            },
        ]

        compare_data = build_compare_data(options_data, 3)

        assert len(compare_data) == 3
        assert len(compare_data[0]["options"]) == 2
        assert compare_data[0]["options"][0]["name"] == "Cash"
        assert compare_data[0]["options"][0]["payment"] == Decimal(100)
        assert compare_data[0]["options"][1]["name"] == "Loan"
        assert compare_data[0]["options"][1]["payment"] == Decimal(200)
