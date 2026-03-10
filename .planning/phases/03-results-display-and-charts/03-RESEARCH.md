# Phase 3: Results Display and Charts - Research

**Researched:** 2026-03-10
**Domain:** Server-side SVG charts, HTMX partial rendering, accessible data visualization
**Confidence:** HIGH

## Summary

Phase 3 renders the calculation engine's `ComparisonResult` into three visual components: a recommendation hero card, a cost breakdown table, and two SVG charts (bar + line). All rendering is server-side Python with zero client-side JS for charts. The existing codebase already has HTMX loaded, Pico CSS for styling, Jinja2 partials pattern established, and a `compare_options()` route that calls the engine and passes results to templates.

The primary technical challenge is generating accessible SVG charts server-side with fill patterns (hatched, dotted, crosshatch) for WCAG color-not-only compliance. The recommended approach is hand-rolled SVG via Jinja2 templates rather than a charting library, because: (1) only two simple chart types are needed, (2) full control over SVG `<pattern>` elements and `<title>`/`<desc>` accessibility markup is required, (3) no JS dependencies from charting libraries, and (4) the data shapes are simple and known.

**Primary recommendation:** Generate SVG charts using dedicated Jinja2 template partials that receive pre-computed chart data from Python helper functions. Use `<defs>` with `<pattern>` elements for accessible fill patterns. HTMX partial replacement via `HX-Request` header detection on the existing `/compare` route.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Hero card with callout at top of results area -- large, prominent, visually distinct from breakdown
- Winner name in bold, savings vs next-best in big text, plain-English "why" sentence below
- Conversational insight tone: "Your money earns more invested than you'd pay in interest."
- PromoResult dual outcomes: use paid-on-time result for ranking; penalty scenario shown as caveat
- Caveats displayed as inline warnings below explanation, severity-based styling (amber warning, red critical)
- Only caveats for winning option on hero card; other options' caveats in breakdown section
- Cost breakdown table: one column per option with all engine-computed components
- Zero-value rows hidden when component is $0 for ALL options
- PromoResult options get two sub-columns: "If paid on time" and "If not"
- Winner highlighted with bold + star on True Total Cost cell; winning column header gets subtle background tint
- Mobile: horizontal scroll with sticky row labels pinned on left
- Server-rendered SVG for both bar chart and line chart -- zero client-side JS for charts
- Accessibility: unique SVG fill pattern (solid, hatched, dotted, crosshatch) per option alongside color
- Direct labels on bars/lines (no legend-only identification)
- Line chart: different dash patterns (solid, dashed, dotted) with direct labels at endpoints
- Hidden data table (visually-hidden, sr-only) below each chart for screen readers
- SVG has `<title>` and `<desc>` elements for summary screen reader access
- Line chart X-axis: monthly data from MonthlyDataPoint, labeled at year boundaries (12, 24, 36...)
- Line chart endpoint labels show final True Total Cost per option
- Button-click only: results update when user clicks "Compare Options" -- no debounced auto-update
- Convert existing form to HTMX POST: `hx-post="/compare" hx-target="#results" hx-swap="innerHTML"`
- Progressive enhancement: HX-Request header detection for partial vs full page
- Loading indicator: button text changes to "Calculating..." with spinner, button disabled
- Mobile auto-scroll: first calculation scrolls to #results; subsequent stay in place
- All browser-based verification automated via Playwright MCP

### Claude's Discretion
- SVG chart dimensions, colors, and exact pattern definitions
- Exact CSS styling for hero card, table, and charts (within Pico CSS framework)
- How caveats for non-winning options are displayed in breakdown section
- Loading spinner implementation details
- SVG generation approach (template-based vs string building vs library)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| RSLT-01 | Summary recommendation card naming winning option with plain-English explanation | Hero card template partial with ComparisonResult winner logic |
| RSLT-02 | Savings amount compared to next-best option in plain English | Python helper to compute winner, runner-up, and delta from ComparisonResult |
| RSLT-03 | Caveats flagged on recommendation (e.g., deferred interest risk) | Caveat filtering by winning option, severity-based CSS classes |
| RSLT-04 | Cost breakdown table with all components per option | Jinja2 table partial with PromoResult sub-column handling |
| RSLT-05 | True Total Cost bar chart with winner highlighted | SVG bar chart template with pattern fills and direct labels |
| RSLT-06 | Cumulative cost over time line chart month-by-month | SVG line chart template using MonthlyDataPoint data |
| RSLT-07 | Results update via HTMX partial page replacement | HX-Request header detection, results partial template |
| RSLT-08 | Visible "Calculate" button always present as fallback | Form already has button; enhance with hx-post attributes |
| A11Y-02 | Charts include accessible text alternatives | Hidden data tables, SVG title/desc, aria-labelledby |
| A11Y-03 | Color not sole differentiator in charts | SVG pattern fills (solid, hatched, dotted, crosshatch) + direct labels |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Flask | >=3.1.3 | Web framework (already installed) | Project standard |
| Jinja2 | (bundled with Flask) | Templating for HTML + SVG | Already in use, perfect for SVG generation |
| HTMX | 2.0.8 (CDN) | Partial page updates | Already loaded in base.html |
| Pico CSS | v2 (CDN) | Base styling framework | Already loaded in base.html |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| markupsafe | (bundled with Flask) | `Markup()` for safe SVG strings | When passing pre-built SVG fragments to templates |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Jinja2 SVG templates | Pygal library | Pygal generates interactive SVG with JS tooltips; we need static SVG with custom patterns. Pygal's pattern/accessibility support is limited. Extra dependency for less control. |
| Jinja2 SVG templates | matplotlib SVG export | Heavyweight dependency, complex output, hard to customize accessibility markup |
| Hand-coded SVG | svg.py library | Adds dependency; our charts are simple enough that template-based SVG is cleaner |
| No new dependencies | flask-htmx | Only adds `request.htmx` convenience; checking `request.headers.get("HX-Request")` directly is one line |

**Installation:**
```bash
# No new dependencies needed -- all tools already available
```

## Architecture Patterns

### Recommended Project Structure
```
src/fathom/
  templates/
    partials/
      results/
        recommendation.html    # Hero card partial
        breakdown_table.html   # Cost breakdown table partial
        bar_chart.html         # SVG bar chart partial
        line_chart.html        # SVG line chart partial
        data_table_bar.html    # Hidden accessible data table for bar chart
        data_table_line.html   # Hidden accessible data table for line chart
      results.html             # Composite results partial (includes all above)
  charts.py                    # Chart data preparation (scales, coordinates, labels)
  results.py                   # Result analysis (winner, savings, caveats filtering)
  static/
    style.css                  # Extended with results, chart, table styles
```

### Pattern 1: Results Data Preparation Layer
**What:** Python module that transforms `ComparisonResult` into template-ready display data
**When to use:** Before passing results to any template
**Example:**
```python
# results.py
from fathom.models import ComparisonResult, PromoResult, Severity

def analyze_results(comparison: ComparisonResult) -> dict:
    """Transform ComparisonResult into display-ready data."""
    # For PromoResult, use paid_on_time for ranking
    costs = {}
    for name, result in comparison.results.items():
        if isinstance(result, PromoResult):
            costs[name] = result.paid_on_time.true_total_cost
        else:
            costs[name] = result.true_total_cost

    sorted_options = sorted(costs.items(), key=lambda x: x[1])
    winner_name = sorted_options[0][0]
    runner_up_name = sorted_options[1][0] if len(sorted_options) > 1 else None
    savings = costs[runner_up_name] - costs[winner_name] if runner_up_name else Decimal(0)

    # Filter caveats for winner only (hero card)
    winner_caveats = [c for c in comparison.caveats if winner_name.lower() in c.message.lower()]

    return {
        "winner_name": winner_name,
        "winner_cost": costs[winner_name],
        "runner_up_name": runner_up_name,
        "savings": savings,
        "winner_caveats": winner_caveats,
        "sorted_options": sorted_options,
        "all_results": comparison.results,
        "comparison_period_months": comparison.comparison_period_months,
        "all_caveats": comparison.caveats,
    }
```

### Pattern 2: SVG Chart via Jinja2 Templates
**What:** SVG markup generated entirely in Jinja2 templates with pre-computed coordinates
**When to use:** For both bar chart and line chart
**Example:**
```html
{# bar_chart.html #}
<svg role="img" aria-labelledby="bar-chart-title bar-chart-desc"
     xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 {{ chart.width }} {{ chart.height }}"
     class="chart-bar">
  <title id="bar-chart-title">True Total Cost Comparison</title>
  <desc id="bar-chart-desc">Bar chart comparing true total cost of {{ chart.options|length }} financing options. {{ chart.winner_name }} has the lowest cost.</desc>

  <defs>
    {# Solid fill - option 1 #}
    <pattern id="pattern-solid" width="10" height="10" patternUnits="userSpaceOnUse">
      <rect width="10" height="10" fill="{{ chart.colors[0] }}"/>
    </pattern>
    {# Diagonal hatching - option 2 #}
    <pattern id="pattern-hatched" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <rect width="8" height="8" fill="white"/>
      <line x1="0" y1="0" x2="0" y2="8" stroke="{{ chart.colors[1] }}" stroke-width="4"/>
    </pattern>
    {# Dotted - option 3 #}
    <pattern id="pattern-dotted" width="6" height="6" patternUnits="userSpaceOnUse">
      <rect width="6" height="6" fill="white"/>
      <circle cx="3" cy="3" r="2" fill="{{ chart.colors[2] }}"/>
    </pattern>
    {# Crosshatch - option 4 #}
    <pattern id="pattern-crosshatch" width="8" height="8" patternUnits="userSpaceOnUse">
      <rect width="8" height="8" fill="white"/>
      <path d="M 0 0 L 8 8 M 8 0 L 0 8" stroke="{{ chart.colors[3] }}" stroke-width="1.5"/>
    </pattern>
  </defs>

  {% for bar in chart.bars %}
  <g>
    <rect x="{{ bar.x }}" y="{{ bar.y }}" width="{{ bar.width }}" height="{{ bar.height }}"
          fill="url(#{{ bar.pattern_id }})"
          stroke="{{ bar.color }}" stroke-width="1.5"
          {% if bar.is_winner %}class="winner-bar"{% endif %}/>
    <text x="{{ bar.label_x }}" y="{{ bar.label_y }}" text-anchor="middle"
          font-size="13" fill="#333">
      {{ bar.label }}
    </text>
    <text x="{{ bar.value_x }}" y="{{ bar.value_y }}" text-anchor="middle"
          font-size="12" font-weight="{% if bar.is_winner %}bold{% else %}normal{% endif %}"
          fill="#333">
      ${{ bar.value }}
    </text>
  </g>
  {% endfor %}

  {# X-axis labels #}
  {% for bar in chart.bars %}
  <text x="{{ bar.label_x }}" y="{{ chart.axis_y }}" text-anchor="middle" font-size="11">
    {{ bar.name }}
  </text>
  {% endfor %}
</svg>
```

### Pattern 3: HTMX Partial Response with Progressive Enhancement
**What:** Detect HX-Request header to return partial or full page
**When to use:** On the `/compare` POST route
**Example:**
```python
@bp.route("/compare", methods=["POST"])
def compare_options() -> str:
    parsed = parse_form_data(request.form)
    errors = validate_form_data(parsed)

    if errors:
        ctx = _build_template_context(parsed, errors)
        ctx["has_errors"] = True
        if request.headers.get("HX-Request"):
            # Return error display in results area
            return render_template("partials/results.html", **ctx)
        return render_template("index.html", **ctx)

    financing_options, global_settings = build_domain_objects(parsed)
    comparison = compare(financing_options, global_settings)
    display_data = analyze_results(comparison)
    chart_data = prepare_charts(comparison, display_data)

    ctx = _build_template_context(parsed, errors={}, results=comparison)
    ctx["display"] = display_data
    ctx["charts"] = chart_data

    if request.headers.get("HX-Request"):
        return render_template("partials/results.html", **ctx)
    return render_template("index.html", **ctx)
```

### Pattern 4: Chart Data Preparation (Python coordinates)
**What:** Python module computes all SVG coordinates, scales, and labels; templates just render
**When to use:** Keep math in Python, keep markup in Jinja2
**Example:**
```python
# charts.py
PATTERNS = ["pattern-solid", "pattern-hatched", "pattern-dotted", "pattern-crosshatch"]
COLORS = ["#2563eb", "#dc2626", "#059669", "#d97706"]
DASH_PATTERNS = ["none", "8,4", "3,3", "12,4,3,4"]
CHART_WIDTH = 600
CHART_HEIGHT = 350
PADDING = 60

def prepare_bar_chart(display_data: dict) -> dict:
    """Compute bar positions, heights, labels for the bar chart SVG."""
    options = display_data["sorted_options"]
    max_cost = float(max(cost for _, cost in options))
    bar_count = len(options)
    usable_width = CHART_WIDTH - 2 * PADDING
    usable_height = CHART_HEIGHT - 2 * PADDING
    bar_width = usable_width / (bar_count * 2)

    bars = []
    for i, (name, cost) in enumerate(options):
        cost_float = float(cost)
        height = (cost_float / max_cost) * usable_height if max_cost > 0 else 0
        x = PADDING + i * (usable_width / bar_count) + bar_width / 2
        y = PADDING + usable_height - height
        bars.append({
            "name": name,
            "x": x, "y": y,
            "width": bar_width, "height": height,
            "pattern_id": PATTERNS[i % len(PATTERNS)],
            "color": COLORS[i % len(COLORS)],
            "is_winner": i == 0,
            "label": name,
            "value": f"{cost_float:,.0f}",
            "label_x": x + bar_width / 2,
            "label_y": PADDING + usable_height + 20,
            "value_x": x + bar_width / 2,
            "value_y": y - 8,
        })
    return {
        "width": CHART_WIDTH, "height": CHART_HEIGHT,
        "bars": bars, "colors": COLORS,
        "winner_name": display_data["winner_name"],
        "options": options,
        "axis_y": PADDING + usable_height + 20,
    }
```

### Anti-Patterns to Avoid
- **Building SVG strings in Python code:** Concatenating SVG markup in Python is error-prone and hard to maintain. Use Jinja2 templates for markup, Python for data.
- **Client-side chart rendering fallback:** The decision is zero client-side JS for charts. Do not add Chart.js or similar as "enhancement."
- **Putting coordinate math in Jinja2:** Keep all scaling, positioning, and numerical calculations in Python. Templates should only loop and insert values.
- **Using `aria-label` instead of `<title>` + `aria-labelledby`:** The `<title>` + `<desc>` + `aria-labelledby` pattern has better cross-browser/screen-reader support for SVG.
- **Legend-only color identification:** Every bar and line must have direct text labels, not just a color legend.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Decimal formatting for display | Custom format function | Python's `f"{val:,.2f}"` or `locale.currency()` | Edge cases with negative values, thousands separators |
| SVG escaping in templates | Manual XML escaping | Jinja2 autoescaping (already enabled by Flask) | Jinja2 handles XML entity escaping correctly |
| HTMX request detection | Custom middleware | `request.headers.get("HX-Request")` | One-liner, no library needed |
| Responsive table scroll | Custom JS scrolling | CSS `overflow-x: auto` + `position: sticky` | Pure CSS solution works across browsers |
| Visually-hidden class | New utility class | Existing `.visually-hidden` in style.css | Already defined in Phase 2 |

**Key insight:** This phase adds no new Python dependencies. Flask, Jinja2, HTMX, and Pico CSS already provide everything needed. The complexity is in template design and data preparation, not in library integration.

## Common Pitfalls

### Pitfall 1: Decimal Values in SVG Coordinates
**What goes wrong:** Python `Decimal` objects cannot be used directly in SVG coordinate attributes; Jinja2 renders them with full precision creating overly long numbers.
**Why it happens:** The engine returns `Decimal` for all monetary values, but SVG needs float-like coordinate values.
**How to avoid:** Convert to `float` in the chart data preparation layer (`charts.py`), not in templates. Format monetary display values as strings with `f"${float(val):,.0f}"`.
**Warning signs:** SVG rendering errors, bars with tiny fractions of a pixel offset.

### Pitfall 2: PromoResult vs OptionResult Type Branching
**What goes wrong:** Templates crash or show wrong data when encountering `PromoResult` (which has `paid_on_time` and `not_paid_on_time` sub-results) vs plain `OptionResult`.
**Why it happens:** The results dict maps names to `OptionResult | PromoResult`. Template logic must handle both.
**How to avoid:** Use `isinstance()` checks in the Python data preparation layer to normalize data before passing to templates. In Jinja2, use a flag like `is_promo` on each option's display data.
**Warning signs:** AttributeError on `true_total_cost` for PromoResult (it's on the sub-objects).

### Pitfall 3: SVG Pattern IDs Must Be Unique Per Chart
**What goes wrong:** If both bar chart and line chart use `<pattern id="pattern-hatched">`, the second chart's patterns reference the first chart's definitions (or vice versa), causing visual glitches.
**Why it happens:** SVG `id` attributes are document-scoped, not SVG-scoped.
**How to avoid:** Prefix pattern IDs with chart type: `bar-pattern-hatched`, `line-pattern-hatched`.
**Warning signs:** Charts showing wrong colors/patterns, especially when both charts are on the same page.

### Pitfall 4: HTMX Form Submission Replacing Wrong Target
**What goes wrong:** HTMX replaces the entire page or wrong element instead of just the results area.
**Why it happens:** The form currently does `action="/compare"` with no HTMX attributes. Adding `hx-post` on the form while keeping `action` means non-JS fallback still works, but `hx-target` must point to `#results`.
**How to avoid:** Add `hx-post="/compare" hx-target="#results" hx-swap="innerHTML"` to the form element. Keep the `action="/compare"` for progressive enhancement.
**Warning signs:** Full page reload on submit instead of partial update; results appearing inside the form.

### Pitfall 5: Mobile Table Sticky Column Z-Index
**What goes wrong:** Sticky row labels scroll under other content or don't stick properly.
**Why it happens:** CSS `position: sticky` requires the parent to have `overflow: visible` on the sticky axis, but `overflow-x: auto` on the scroll container conflicts.
**How to avoid:** The sticky column must be on `<th>` / `<td>` elements inside the scroll container, with explicit `background-color` (not transparent) and `z-index` to layer above scrolling cells.
**Warning signs:** Row labels disappearing during horizontal scroll, transparent background showing content behind.

### Pitfall 6: Empty Monthly Data for Cash Options
**What goes wrong:** Line chart crashes or shows nothing for Cash options because `MonthlyDataPoint` list may be empty or have only month-0 data.
**Why it happens:** Cash options have no payment schedule -- they pay everything upfront.
**How to avoid:** In chart data prep, ensure Cash options get a flat line at their `true_total_cost` value for the full comparison period. Check the engine's actual output for cash monthly_data.
**Warning signs:** Line chart with missing lines, JavaScript errors (though we have no JS), or SVG path with no coordinates.

## Code Examples

### HTMX Form Enhancement
```html
{# Modified form tag in index.html #}
<form method="post" action="/compare" id="comparison-form"
      hx-post="/compare"
      hx-target="#results"
      hx-swap="innerHTML"
      hx-indicator="#compare-indicator"
      hx-disabled-elt="find button[type='submit']">
```

### Loading Indicator Button
```html
<button type="submit" id="compare-btn">
  <span class="btn-text">Compare Options</span>
  <span class="htmx-indicator" id="compare-indicator" aria-hidden="true">
    Calculating...
  </span>
</button>
```
```css
/* Loading indicator styles */
.htmx-indicator { display: none; }
.htmx-request .htmx-indicator { display: inline; }
.htmx-request .btn-text { display: none; }
```

### Accessible Hidden Data Table
```html
<div class="visually-hidden">
  <table>
    <caption>True Total Cost comparison data</caption>
    <thead>
      <tr>
        <th scope="col">Option</th>
        <th scope="col">True Total Cost</th>
      </tr>
    </thead>
    <tbody>
      {% for bar in chart.bars %}
      <tr>
        <td>{{ bar.name }}</td>
        <td>${{ bar.value }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
```

### SVG Line Chart Dash Patterns
```html
{# Line paths with different dash patterns #}
{% for line in chart.lines %}
<path d="{{ line.path_d }}"
      fill="none"
      stroke="{{ line.color }}"
      stroke-width="2.5"
      stroke-dasharray="{{ line.dash_pattern }}"
      stroke-linecap="round"/>
{# Direct label at endpoint #}
<text x="{{ line.end_x + 5 }}" y="{{ line.end_y }}"
      font-size="11" fill="{{ line.color }}">
  {{ line.name }}: ${{ line.end_value }}
</text>
{% endfor %}
```

### Caveat Severity Styling
```css
.caveat-warning {
  background-color: #fef3c7;
  border-left: 4px solid #f59e0b;
  padding: 0.5rem 1rem;
}
.caveat-critical {
  background-color: #fee2e2;
  border-left: 4px solid #ef4444;
  padding: 0.5rem 1rem;
}
```

### Winner Detection Helper
```python
def find_winner(comparison: ComparisonResult) -> tuple[str, Decimal]:
    """Find the option with lowest true total cost."""
    costs: dict[str, Decimal] = {}
    for name, result in comparison.results.items():
        if isinstance(result, PromoResult):
            costs[name] = result.paid_on_time.true_total_cost
        else:
            costs[name] = result.true_total_cost
    winner = min(costs, key=lambda k: costs[k])
    return winner, costs[winner]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Chart.js / D3 client-side | Server-rendered SVG | Project decision | Zero JS dependency for charts |
| `aria-label` on SVG | `<title>` + `<desc>` + `aria-labelledby` | WCAG best practice 2024+ | Better screen reader support |
| Color-only chart differentiation | Patterns + direct labels + color | WCAG 1.4.1 | Accessible to colorblind users |
| Full-page form POST | HTMX partial replacement | HTMX 2.x standard | Smoother UX, progressive enhancement |
| Flask-HTMX extension | Direct header check | Simplification | No extra dependency for one-line check |

## Open Questions

1. **Cash option monthly_data shape**
   - What we know: Cash options pay upfront with no amortization schedule
   - What's unclear: Does the engine generate MonthlyDataPoint entries for the full comparison period, or just month 0?
   - Recommendation: Check engine output during implementation; if sparse, generate flat-line data in charts.py

2. **Caveat-to-option association**
   - What we know: `ComparisonResult.caveats` is a flat list of `Caveat` objects with `message` strings
   - What's unclear: Whether caveats contain the option name in the message text, or need separate association logic
   - Recommendation: Inspect actual caveat messages from the engine; may need to match by keyword or add option_name field

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already configured) |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/ -x -q` |
| Full suite command | `uv run pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RSLT-01 | Recommendation card shows winner name | integration | `uv run pytest tests/test_results_display.py::test_recommendation_card_shows_winner -x` | Wave 0 |
| RSLT-02 | Savings vs next-best displayed | integration | `uv run pytest tests/test_results_display.py::test_savings_displayed -x` | Wave 0 |
| RSLT-03 | Caveats on recommendation | integration | `uv run pytest tests/test_results_display.py::test_caveats_on_hero -x` | Wave 0 |
| RSLT-04 | Breakdown table with all components | integration | `uv run pytest tests/test_results_display.py::test_breakdown_table -x` | Wave 0 |
| RSLT-05 | Bar chart SVG present with winner highlight | integration | `uv run pytest tests/test_results_display.py::test_bar_chart_svg -x` | Wave 0 |
| RSLT-06 | Line chart SVG with monthly data | integration | `uv run pytest tests/test_results_display.py::test_line_chart_svg -x` | Wave 0 |
| RSLT-07 | HTMX partial replacement | integration | `uv run pytest tests/test_results_display.py::test_htmx_partial -x` | Wave 0 |
| RSLT-08 | Calculate button present as fallback | integration | `uv run pytest tests/test_results_display.py::test_calculate_button_fallback -x` | Wave 0 |
| A11Y-02 | Charts have text alternatives | integration | `uv run pytest tests/test_results_display.py::test_chart_accessibility -x` | Wave 0 |
| A11Y-03 | Color not sole differentiator | integration | `uv run pytest tests/test_results_display.py::test_chart_patterns -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/ -x -q`
- **Per wave merge:** `uv run pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_results_display.py` -- covers RSLT-01 through RSLT-08, A11Y-02, A11Y-03
- [ ] `tests/test_charts.py` -- unit tests for charts.py coordinate computation
- [ ] `tests/test_results_helpers.py` -- unit tests for results.py winner/savings logic

## Sources

### Primary (HIGH confidence)
- Existing codebase: `models.py`, `routes.py`, `engine.py`, `templates/`, `style.css` -- direct inspection
- HTMX official docs (htmx.org) -- hx-indicator, hx-disabled-elt, HX-Request header
- SVG specification -- `<pattern>`, `<defs>`, `<title>`, `<desc>` elements
- Pico CSS docs (picocss.com) -- table styling, overflow-auto

### Secondary (MEDIUM confidence)
- A11Y Collective, Deque, data.europa.eu -- SVG accessibility patterns with `role="img"` + `aria-labelledby`
- CSS-Tricks, patternfills -- SVG pattern fill definitions (hatched, crosshatch, dotted)
- Flask-HTMX docs -- confirmed one-line header check is sufficient

### Tertiary (LOW confidence)
- None -- all findings verified against official sources or existing codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, everything already in the project
- Architecture: HIGH -- patterns follow established codebase conventions (partials, Jinja2, routes)
- Pitfalls: HIGH -- identified from direct codebase inspection and known SVG/HTMX behavior
- SVG patterns: MEDIUM -- pattern definitions need visual testing during implementation
- Chart coordinate math: MEDIUM -- specific numbers will need tuning during implementation

**Research date:** 2026-03-10
**Valid until:** 2026-04-10 (stable domain, no fast-moving dependencies)
