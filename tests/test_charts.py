"""Tests for chart data preparation functions."""

from decimal import Decimal

from fathom.charts import NOT_PAID_DASH, prepare_bar_chart, prepare_line_chart
from fathom.models import (
    ComparisonResult,
    MonthlyDataPoint,
    OptionResult,
    PromoResult,
)


def _make_option_result(
    true_total_cost,
    monthly_data=None,
):
    """Create an OptionResult with sensible defaults."""
    return OptionResult(
        total_payments=Decimal(str(true_total_cost)),
        total_interest=Decimal(0),
        opportunity_cost=Decimal(0),
        tax_savings=Decimal(0),
        inflation_adjustment=Decimal(0),
        rebates=Decimal(0),
        true_total_cost=Decimal(str(true_total_cost)),
        monthly_data=monthly_data or [],
    )


def _make_monthly_data(months, cumulative_costs):
    """Create monthly data points from cumulative cost values."""
    return [
        MonthlyDataPoint(
            month=m,
            payment=Decimal(500),
            interest_portion=Decimal(50),
            principal_portion=Decimal(450),
            remaining_balance=Decimal(10000),
            investment_balance=Decimal(0),
            cumulative_cost=Decimal(str(c)),
        )
        for m, c in zip(months, cumulative_costs, strict=False)
    ]


def _make_display_data(options_costs):
    """Create display_data dict with sorted_options."""
    sorted_opts = sorted(options_costs, key=lambda x: x[1])
    return {
        "sorted_options": [(name, Decimal(str(cost))) for name, cost in sorted_opts],
    }


# --- Bar Chart Tests ---


class TestBarChart:
    """Tests for prepare_bar_chart."""

    def test_bar_chart_has_correct_bar_count(self):
        """Verify bar count matches option count."""
        display = _make_display_data([("Cash", 25000), ("Loan", 27500)])
        result = prepare_bar_chart(display)
        assert len(result["bars"]) == 2

    def test_bar_chart_winner_is_first(self):
        """Verify cheapest option is first with is_winner=True."""
        display = _make_display_data(
            [("Loan", 27500), ("Cash", 25000), ("Promo", 26000)],
        )
        result = prepare_bar_chart(display)
        assert result["bars"][0]["is_winner"] is True
        assert result["bars"][0]["name"] == "Cash"
        assert result["bars"][1]["is_winner"] is False
        assert result["bars"][2]["is_winner"] is False

    def test_bar_chart_heights_proportional(self):
        """Verify more expensive option has taller bar."""
        display = _make_display_data([("Cash", 10000), ("Loan", 20000)])
        result = prepare_bar_chart(display)
        bars = result["bars"]
        cash_bar = next(b for b in bars if b["name"] == "Cash")
        loan_bar = next(b for b in bars if b["name"] == "Loan")
        assert loan_bar["height"] > cash_bar["height"]

    def test_bar_chart_pattern_ids_prefixed(self):
        """Verify all pattern IDs start with bar-pattern-."""
        display = _make_display_data([("A", 100), ("B", 200), ("C", 300)])
        result = prepare_bar_chart(display)
        for bar in result["bars"]:
            assert bar["pattern_id"].startswith("bar-pattern-")

    def test_bar_chart_coordinates_are_float(self):
        """Verify all coordinates are float, not Decimal."""
        display = _make_display_data([("Cash", 25000)])
        result = prepare_bar_chart(display)
        bar = result["bars"][0]
        assert isinstance(bar["x"], float)
        assert isinstance(bar["y"], float)
        assert isinstance(bar["width"], float)
        assert isinstance(bar["height"], float)

    def test_bar_chart_has_winner_name(self):
        """Verify winner_name is set to cheapest option."""
        display = _make_display_data([("Cash", 25000), ("Loan", 27500)])
        result = prepare_bar_chart(display)
        assert result["winner_name"] == "Cash"

    def test_bar_chart_value_formatted(self):
        """Verify value is formatted with commas and no decimals."""
        display = _make_display_data([("Cash", 25000)])
        result = prepare_bar_chart(display)
        assert result["bars"][0]["value"] == "25,000"


# --- Line Chart Tests ---


class TestLineChart:
    """Tests for prepare_line_chart."""

    def test_line_chart_has_correct_line_count(self):
        """Verify line count matches option count."""
        monthly_a = _make_monthly_data(range(25), range(0, 25000, 1000))
        monthly_b = _make_monthly_data(range(25), range(0, 27500, 1100))
        comparison = ComparisonResult(
            results={
                "Cash": _make_option_result(25000, monthly_a),
                "Loan": _make_option_result(27500, monthly_b),
            },
            comparison_period_months=24,
            caveats=[],
        )
        display = _make_display_data([("Cash", 25000), ("Loan", 27500)])
        result = prepare_line_chart(comparison, display)
        assert len(result["lines"]) == 2

    def test_line_chart_path_d_format(self):
        """Verify SVG path starts with M and contains L."""
        monthly = _make_monthly_data(range(13), range(0, 13000, 1000))
        comparison = ComparisonResult(
            results={"Loan": _make_option_result(13000, monthly)},
            comparison_period_months=12,
            caveats=[],
        )
        display = _make_display_data([("Loan", 13000)])
        result = prepare_line_chart(comparison, display)
        path_d = result["lines"][0]["path_d"]
        assert path_d.startswith("M")
        assert "L" in path_d

    def test_line_chart_dash_patterns_assigned(self):
        """Verify dash_pattern is present on each line."""
        monthly = _make_monthly_data(range(13), range(0, 13000, 1000))
        comparison = ComparisonResult(
            results={"Loan": _make_option_result(13000, monthly)},
            comparison_period_months=12,
            caveats=[],
        )
        display = _make_display_data([("Loan", 13000)])
        result = prepare_line_chart(comparison, display)
        assert "dash_pattern" in result["lines"][0]

    def test_line_chart_cash_flat_line(self):
        """Cash option with sparse monthly_data gets a flat line."""
        cash_monthly = _make_monthly_data([0], [25000])
        comparison = ComparisonResult(
            results={
                "Cash": _make_option_result(25000, cash_monthly),
            },
            comparison_period_months=24,
            caveats=[],
        )
        display = _make_display_data([("Cash", 25000)])
        result = prepare_line_chart(comparison, display)
        line = result["lines"][0]
        assert len(line["points"]) >= 2
        assert line["path_d"].startswith("M")

    def test_line_chart_x_labels_at_year_boundaries(self):
        """Verify x-axis labels appear at year boundaries."""
        monthly = _make_monthly_data(range(37), range(0, 37000, 1000))
        comparison = ComparisonResult(
            results={"Loan": _make_option_result(37000, monthly)},
            comparison_period_months=36,
            caveats=[],
        )
        display = _make_display_data([("Loan", 37000)])
        result = prepare_line_chart(comparison, display)
        label_months = [label["month"] for label in result["x_labels"]]
        assert 12 in label_months
        assert 24 in label_months
        assert 36 in label_months

    def test_line_chart_endpoint_labels(self):
        """Verify endpoint labels have x, y, and formatted value."""
        monthly = _make_monthly_data(range(13), range(0, 13000, 1000))
        comparison = ComparisonResult(
            results={"Loan": _make_option_result(13000, monthly)},
            comparison_period_months=12,
            caveats=[],
        )
        display = _make_display_data([("Loan", 13000)])
        result = prepare_line_chart(comparison, display)
        line = result["lines"][0]
        assert "end_x" in line
        assert "end_y" in line
        assert "end_value" in line
        assert isinstance(line["end_x"], float)
        assert isinstance(line["end_y"], float)


# --- Cumulative True Cost & Promo Dual Lines ---


def _make_promo_comparison(
    paid_costs: list[int],
    not_paid_costs: list[int],
) -> tuple[ComparisonResult, dict]:
    """Create a ComparisonResult with a PromoResult for testing dual lines."""
    months = list(range(1, len(paid_costs) + 1))
    paid_data = _make_monthly_data(months, paid_costs)
    not_paid_data = _make_monthly_data(
        list(range(1, len(not_paid_costs) + 1)),
        not_paid_costs,
    )

    paid_result = _make_option_result(paid_costs[-1], paid_data)
    not_paid_result = _make_option_result(not_paid_costs[-1], not_paid_data)

    promo = PromoResult(
        paid_on_time=paid_result,
        not_paid_on_time=not_paid_result,
        required_monthly_payment=Decimal(500),
        break_even_month=12,
    )

    comparison = ComparisonResult(
        results={"Promo": promo},
        comparison_period_months=len(not_paid_costs),
        caveats=[],
    )

    display = {
        "sorted_options": [
            ("Promo", Decimal(str(paid_costs[-1]))),
            ("Promo (not paid on time)", Decimal(str(not_paid_costs[-1]))),
        ],
    }

    return comparison, display


class TestLineTrueCost:
    """Tests for cumulative true cost chart data."""

    def test_line_chart_uses_true_cost(self):
        """Chart data points match cumulative_cost from MonthlyDataPoint."""
        # Create monthly data with known cumulative true cost values
        true_costs = [550, 1120, 1710, 2320, 2950]
        monthly = _make_monthly_data(range(1, 6), true_costs)
        comparison = ComparisonResult(
            results={"Loan": _make_option_result(2950, monthly)},
            comparison_period_months=5,
            caveats=[],
        )
        display = {"sorted_options": [("Loan", Decimal(2950))]}
        result = prepare_line_chart(comparison, display)
        line_pts = result["lines"][0]["points"]
        for pt, expected in zip(line_pts, true_costs, strict=True):
            assert pt["cost"] == f"{expected:,.0f}"

    def test_line_chart_promo_dual_lines(self):
        """Promo options produce two line datasets (paid and not-paid)."""
        paid_costs = list(range(500, 6500, 500))
        not_paid_costs = list(range(300, 7500, 300))
        comparison, display = _make_promo_comparison(paid_costs, not_paid_costs)
        result = prepare_line_chart(comparison, display)
        assert len(result["lines"]) == 2
        names = [line["name"] for line in result["lines"]]
        assert "Promo" in names
        assert "Promo (not paid on time)" in names

    def test_line_chart_not_paid_is_dashed(self):
        """Not-paid-on-time line uses a dashed stroke pattern."""
        paid_costs = list(range(500, 6500, 500))
        not_paid_costs = list(range(300, 7500, 300))
        comparison, display = _make_promo_comparison(paid_costs, not_paid_costs)
        result = prepare_line_chart(comparison, display)
        not_paid_line = next(
            ln for ln in result["lines"] if "(not paid on time)" in ln["name"]
        )
        assert not_paid_line["dash_pattern"] == NOT_PAID_DASH

    def test_line_chart_not_paid_same_color_as_paid(self):
        """Not-paid line uses the same color as its paid counterpart."""
        paid_costs = list(range(500, 6500, 500))
        not_paid_costs = list(range(300, 7500, 300))
        comparison, display = _make_promo_comparison(paid_costs, not_paid_costs)
        result = prepare_line_chart(comparison, display)
        paid_line = next(ln for ln in result["lines"] if ln["name"] == "Promo")
        not_paid_line = next(
            ln for ln in result["lines"] if "(not paid on time)" in ln["name"]
        )
        assert paid_line["color"] == not_paid_line["color"]

    def test_line_chart_title(self):
        """Chart title is 'Cumulative True Cost Over Time'."""
        monthly = _make_monthly_data(range(1, 6), range(500, 3000, 500))
        comparison = ComparisonResult(
            results={"Loan": _make_option_result(2500, monthly)},
            comparison_period_months=5,
            caveats=[],
        )
        display = {"sorted_options": [("Loan", Decimal(2500))]}
        result = prepare_line_chart(comparison, display)
        assert result["title"] == "Cumulative True Cost Over Time"
