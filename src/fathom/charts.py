"""
Chart data preparation for SVG rendering.

Computes bar positions, line coordinates, scales, and pattern assignments
for server-rendered SVG charts. All coordinate values are float (not Decimal)
for direct use in SVG templates.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from fathom.models import ComparisonResult, OptionResult, PromoResult

if TYPE_CHECKING:
    from decimal import Decimal

_ScaleFn = Callable[[int | float], float]

CHART_WIDTH = 600
CHART_HEIGHT = 350
LINE_CHART_WIDTH = 700
LINE_CHART_HEIGHT = 350
PADDING = 60

COLORS = ["#2563eb", "#dc2626", "#059669", "#d97706"]

BAR_PATTERNS = [
    "bar-pattern-solid",
    "bar-pattern-hatched",
    "bar-pattern-dotted",
    "bar-pattern-crosshatch",
]

LINE_PATTERNS = [
    "line-pattern-solid",
    "line-pattern-hatched",
    "line-pattern-dotted",
    "line-pattern-crosshatch",
]

DASH_PATTERNS = ["none", "8,4", "3,3", "12,4,3,4"]


def _to_float(value: Decimal | float | int) -> float:
    """Convert a numeric value to float."""
    return float(value)


def _format_cost(value: Decimal | float) -> str:
    """Format a cost value as a comma-separated string without decimals."""
    return f"{float(value):,.0f}"


def prepare_bar_chart(display_data: dict) -> dict:
    """
    Prepare bar chart data from display_data.

    Takes the output of analyze_results (has sorted_options as list of
    (name, cost) tuples sorted ascending by cost). Returns a dict with
    width, height, bars, colors, winner_name, and axis_y for SVG rendering.

    Args:
        display_data: Dict with sorted_options as list of (name, cost) tuples.

    Returns:
        Dict with bar chart rendering data including bar positions and labels.

    """
    sorted_options: list[tuple[str, Decimal]] = display_data["sorted_options"]

    if not sorted_options:
        return {
            "width": CHART_WIDTH,
            "height": CHART_HEIGHT,
            "bars": [],
            "colors": COLORS,
            "winner_name": "",
            "axis_y": _to_float(CHART_HEIGHT - PADDING),
        }

    max_cost = max(_to_float(cost) for _, cost in sorted_options)
    if max_cost == 0:
        max_cost = 1.0

    usable_width = CHART_WIDTH - 2 * PADDING
    usable_height = CHART_HEIGHT - 2 * PADDING
    num_bars = len(sorted_options)
    bar_gap = 20.0
    bar_width = (usable_width - bar_gap * (num_bars - 1)) / num_bars
    bar_width = min(bar_width, 120.0)

    total_bars_width = bar_width * num_bars + bar_gap * (num_bars - 1)
    start_x = PADDING + (usable_width - total_bars_width) / 2

    axis_y = _to_float(CHART_HEIGHT - PADDING)
    bars = []

    for i, (name, cost) in enumerate(sorted_options):
        cost_f = _to_float(cost)
        height = (cost_f / max_cost) * usable_height
        x = start_x + i * (bar_width + bar_gap)
        y = axis_y - height

        label_x = x + bar_width / 2
        label_y = axis_y + 16.0
        value_x = x + bar_width / 2
        value_y = y - 8.0

        bars.append(
            {
                "name": name,
                "x": _to_float(x),
                "y": _to_float(y),
                "width": _to_float(bar_width),
                "height": _to_float(height),
                "pattern_id": BAR_PATTERNS[i % len(BAR_PATTERNS)],
                "color": COLORS[i % len(COLORS)],
                "is_winner": i == 0,
                "label": name,
                "value": _format_cost(cost),
                "label_x": _to_float(label_x),
                "label_y": _to_float(label_y),
                "value_x": _to_float(value_x),
                "value_y": _to_float(value_y),
            },
        )

    return {
        "width": CHART_WIDTH,
        "height": CHART_HEIGHT,
        "bars": bars,
        "colors": COLORS,
        "winner_name": sorted_options[0][0],
        "axis_y": axis_y,
    }


def _get_option_result(
    result: OptionResult | PromoResult,
) -> OptionResult:
    """Extract OptionResult from either OptionResult or PromoResult."""
    if isinstance(result, PromoResult):
        return result.paid_on_time
    return result


def _collect_option_points(
    comparison: ComparisonResult,
    sorted_options: list[tuple[str, Decimal]],
    max_months: int,
) -> list[list[tuple[int, float]]]:
    """
    Collect monthly cost data points for each financing option.

    Handles sparse data (cash options with <=1 data point) by generating
    flat lines at true_total_cost. Downsamples dense series to at most
    60 points for SVG rendering performance.

    Args:
        comparison: The full ComparisonResult with monthly data.
        sorted_options: List of (name, cost) tuples in display order.
        max_months: The comparison period length in months.

    Returns:
        A list of point lists, one per option, each containing (month, cost) tuples.

    """
    all_points: list[list[tuple[int, float]]] = []

    for name, _cost in sorted_options:
        result = comparison.results.get(name)
        if result is None:
            all_points.append([])
            continue

        option_result = _get_option_result(result)
        monthly_data = option_result.monthly_data

        if len(monthly_data) <= 1:
            cost_val = _to_float(option_result.true_total_cost)
            points = [(0, cost_val), (max_months, cost_val)]
        else:
            points = [(dp.month, _to_float(dp.cumulative_cost)) for dp in monthly_data]
            if len(points) > 60:
                step = max(1, len(points) // 60)
                sampled = points[::step]
                if sampled[-1] != points[-1]:
                    sampled.append(points[-1])
                points = sampled

        all_points.append(points)

    return all_points


def _build_line_dataset(
    name: str,
    index: int,
    pts: list[tuple[int, float]],
    scale_x: _ScaleFn,
    scale_y: _ScaleFn,
) -> dict:
    """
    Build a single line dataset dict for SVG rendering.

    Constructs the SVG path string, endpoint coordinates, and interactive
    point data for one financing option's line.

    Args:
        name: The option display name.
        index: The option index (for color/pattern assignment).
        pts: The (month, cost) data points for this option.
        scale_x: Function mapping month to x coordinate.
        scale_y: Function mapping cost to y coordinate.

    Returns:
        A dict with path_d, color, dash_pattern, endpoint data, and points.

    """
    path_parts = [f"M {scale_x(pts[0][0]):.1f} {scale_y(pts[0][1]):.1f}"]
    for month, cost_val in pts[1:]:
        path_parts.append(f"L {scale_x(month):.1f} {scale_y(cost_val):.1f}")

    end_month, end_cost = pts[-1]
    end_x = scale_x(end_month)
    end_y = scale_y(end_cost)

    return {
        "name": name,
        "path_d": " ".join(path_parts),
        "color": COLORS[index % len(COLORS)],
        "dash_pattern": DASH_PATTERNS[index % len(DASH_PATTERNS)],
        "pattern_id": LINE_PATTERNS[index % len(LINE_PATTERNS)],
        "end_x": _to_float(end_x),
        "end_y": _to_float(end_y),
        "end_value": _format_cost(end_cost),
        "points": [
            {
                "month": m,
                "x": _to_float(scale_x(m)),
                "y": _to_float(scale_y(c)),
                "cost": _format_cost(c),
            }
            for m, c in pts
        ],
    }


def _build_axis_labels(
    max_months: int,
    max_cost: float,
    scale_x: _ScaleFn,
    scale_y: _ScaleFn,
) -> tuple[list[dict], list[dict]]:
    """
    Build x-axis and y-axis label data for the line chart.

    X-axis labels appear at year boundaries. Y-axis labels are 5 evenly
    spaced cost values from zero to the chart maximum.

    Args:
        max_months: The comparison period length in months.
        max_cost: The maximum cost value (with headroom) for y-axis scaling.
        scale_x: Function mapping month to x coordinate.
        scale_y: Function mapping cost to y coordinate.

    Returns:
        A tuple of (x_labels, y_labels) lists.

    """
    x_labels = []
    year = 1
    while year * 12 <= max_months:
        month = year * 12
        x_labels.append(
            {"month": month, "x": _to_float(scale_x(month)), "label": f"Year {year}"},
        )
        year += 1

    y_labels = []
    num_y_labels = 5
    for j in range(num_y_labels):
        val = (max_cost / (num_y_labels - 1)) * j
        y_labels.append({"value": _format_cost(val), "y": _to_float(scale_y(val))})

    return x_labels, y_labels


def prepare_line_chart(
    comparison: ComparisonResult,
    display_data: dict,
) -> dict:
    """
    Prepare line chart data from comparison results.

    Computes SVG path coordinates for cumulative cost over time. Handles
    cash options with sparse monthly_data by generating flat lines at
    true_total_cost for the full comparison period.

    Args:
        comparison: The full ComparisonResult with monthly data.
        display_data: Dict with sorted_options for ordering.

    Returns:
        Dict with line chart rendering data including paths and labels.

    """
    sorted_options: list[tuple[str, Decimal]] = display_data["sorted_options"]
    max_months = comparison.comparison_period_months
    width = LINE_CHART_WIDTH
    height = LINE_CHART_HEIGHT

    if not sorted_options:
        return {
            "width": width,
            "height": height,
            "lines": [],
            "x_labels": [],
            "y_labels": [],
            "max_months": max_months,
        }

    all_points = _collect_option_points(comparison, sorted_options, max_months)

    # Compute max cost across all options with 10% headroom
    max_cost = 1.0
    for pts in all_points:
        for _month, cost_val in pts:
            max_cost = max(max_cost, cost_val)
    max_cost *= 1.1

    def scale_x(month: int | float) -> float:
        """Scale month to x coordinate."""
        if max_months == 0:
            return _to_float(PADDING)
        return PADDING + (month / max_months) * (width - 2 * PADDING)

    def scale_y(cost_val: int | float) -> float:
        """Scale cost value to y coordinate (inverted)."""
        return height - PADDING - (cost_val / max_cost) * (height - 2 * PADDING)

    lines = [
        _build_line_dataset(name, i, all_points[i], scale_x, scale_y)
        for i, (name, _cost) in enumerate(sorted_options)
        if all_points[i]
    ]

    x_labels, y_labels = _build_axis_labels(max_months, max_cost, scale_x, scale_y)

    return {
        "width": width,
        "height": height,
        "lines": lines,
        "x_labels": x_labels,
        "y_labels": y_labels,
        "max_months": max_months,
    }


def prepare_charts(
    comparison: ComparisonResult,
    display_data: dict,
) -> dict:
    """
    Prepare all chart data for template rendering.

    Convenience function combining bar and line chart preparation.

    Args:
        comparison: The full ComparisonResult with monthly data.
        display_data: Dict with sorted_options for ordering.

    Returns:
        Dict with 'bar' and 'line' keys containing chart rendering data.

    """
    return {
        "bar": prepare_bar_chart(display_data),
        "line": prepare_line_chart(comparison, display_data),
    }
