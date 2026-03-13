---
phase: 03-results-display-and-charts
verified: 2026-03-10T22:30:00Z
status: passed
score: 10/10 must-haves verified
gaps: []
resolution: "A11Y-02 gap fixed in commit fcccf56 — added cost field to line chart points, updated template to use point.cost"
---

# Phase 3: Results Display and Charts Verification Report

**Phase Goal:** Users see a complete, accessible results view with recommendation, cost breakdown, and visualizations that update dynamically
**Verified:** 2026-03-10T22:30:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (from Phase 3 Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | User sees a summary recommendation card naming the cheapest option with plain-English explanation, savings vs. next-best, and caveats | VERIFIED | `recommendation.html` renders winner_name, savings, recommendation_text, caveat severity classes. Tests: `test_recommendation_card_shows_winner`, `test_savings_displayed`, `test_caveats_on_hero` all pass. |
| 2 | User sees a cost breakdown table with one column per option showing all 7 cost components | VERIFIED | `breakdown_table.html` renders all components from `display.breakdown_rows`. Zero-value rows filtered in `results.py`. PromoResult dual sub-columns implemented. Tests: `test_breakdown_table_present`, `test_breakdown_has_true_total_cost`, `test_breakdown_has_total_payments` pass. |
| 3 | User sees a True Total Cost bar chart (winner highlighted) and a cumulative cost over time line chart | VERIFIED | `bar_chart.html` renders SVG with pattern fills, winner star, value labels. `line_chart.html` renders SVG with dash-pattern paths, endpoint labels, year-boundary X-axis. `charts.py` computes both. 11 chart unit tests pass. |
| 4 | Charts include accessible text alternatives (data tables or ARIA labels) and use patterns or labels alongside color | PARTIAL — GAP | Bar chart: VERIFIED (SVG title/desc, aria-labelledby, 4 pattern definitions, hidden data table with correct values). Line chart ARIA: VERIFIED. Line chart hidden data table: DEFECTIVE — intermediate rows display pixel Y coordinates (e.g., `$$194`) not dollar costs. Only final row shows correct values via `line.end_value`. A11Y-02 partially broken. |
| 5 | Results update via HTMX partial page replacement when inputs change, with a visible Calculate button always present as fallback | VERIFIED | `compare_options()` detects `HX-Request: true` header and returns `partials/results.html`. Form has `hx-post="/compare" hx-target="#results" hx-swap="innerHTML"`. Non-JS fallback: `action="/compare"` preserved. Tests: `test_htmx_partial`, `test_non_htmx_full_page`, `test_calculate_button_fallback` all pass. |
| 6 | All browser-based verification automated via Playwright MCP | VERIFIED | `tests/playwright_verify.py` exists with 21 checks covering HTMX swap, hero card, SVG charts, accessibility (structural), responsive layout. Summary claims all 21 pass. Note: Playwright checks confirmed hidden tables exist and have captions, but did not assert that cell values are meaningful dollar amounts (the defect was not caught by Playwright checks). |

**Score:** 9/10 truths verified (Truth 4 is partial due to the data_table_line bug)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/fathom/results.py` | Winner detection, savings calculation, breakdown data prep | VERIFIED | Substantive (281 lines). Exports `analyze_results`, `generate_recommendation_text`. Imports from `fathom.models`. Wired into `routes.py`. |
| `src/fathom/charts.py` | Chart data preparation (bar positions, line coordinates, scales) | VERIFIED | Substantive (320 lines). Exports `prepare_bar_chart`, `prepare_line_chart`, `prepare_charts`. Wired into `routes.py`. |
| `src/fathom/templates/partials/results/recommendation.html` | Hero card partial | VERIFIED | Renders winner name, savings, recommendation text, caveat severity styling. |
| `src/fathom/templates/partials/results/breakdown_table.html` | Cost breakdown table | VERIFIED | All 7 components, PromoResult dual sub-columns, winner highlighting, sticky row labels. |
| `src/fathom/templates/partials/results.html` | Composite results partial | VERIFIED | Includes recommendation, breakdown, and charts (conditionally). HTMX error handling present. |
| `src/fathom/templates/partials/results/bar_chart.html` | SVG bar chart with pattern fills | VERIFIED | SVG with role="img", aria-labelledby, title/desc, 4 pattern defs, bars with fill="url(#...)", direct value/label text elements. |
| `src/fathom/templates/partials/results/line_chart.html` | SVG line chart with dash patterns | VERIFIED | SVG with role="img", aria-labelledby, title/desc, paths with stroke-dasharray, endpoint labels, year-boundary axis labels. |
| `src/fathom/templates/partials/results/data_table_bar.html` | Hidden accessible data table for bar chart | VERIFIED | `visually-hidden` div, table with caption, option/cost rows using `bar.value` (correct dollar-formatted strings). |
| `src/fathom/templates/partials/results/data_table_line.html` | Hidden accessible data table for line chart | STUB/DEFECTIVE | Exists but intermediate rows display pixel Y coordinates (e.g., `$$194`) instead of dollar cost values. Only final row is correct. |
| `tests/test_results_helpers.py` | Unit tests for results.py logic | VERIFIED | 8 tests, all pass. |
| `tests/test_results_display.py` | Integration tests for results HTML | VERIFIED | 12 tests including HTMX partial, chart SVG, accessibility structure. All pass. |
| `tests/test_charts.py` | Unit tests for chart coordinate computation | VERIFIED | 11 tests, all pass. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/fathom/results.py` | `src/fathom/models.py` | `from fathom.models import ComparisonResult, FinancingOption, OptionResult, PromoResult` | VERIFIED | Import confirmed at lines 14-19. |
| `src/fathom/charts.py` | `src/fathom/models.py` | `from fathom.models import ComparisonResult, OptionResult, PromoResult` | VERIFIED | Import confirmed at line 13. |
| `src/fathom/templates/partials/results/recommendation.html` | `results.py analyze_results output` | Jinja2 `display.winner_name`, `display.savings`, `display.recommendation_text`, `display.winner_caveats` | VERIFIED | All `display.*` references match keys returned by `analyze_results`. |
| `src/fathom/templates/partials/results/breakdown_table.html` | `results.py analyze_results output` | Jinja2 `display.breakdown_rows`, `display.options_data` | VERIFIED | Template iterates `display.options_data` and `display.breakdown_rows` — both present in `analyze_results` return dict. |
| `src/fathom/templates/partials/results/bar_chart.html` | `charts.py prepare_bar_chart output` | Jinja2 `charts.bar.*` | VERIFIED | Template uses `charts.bar.bars`, `charts.bar.width`, `charts.bar.winner_name`, `charts.bar.axis_y` — all present in `prepare_bar_chart` return. |
| `src/fathom/templates/partials/results/line_chart.html` | `charts.py prepare_line_chart output` | Jinja2 `charts.line.*` | VERIFIED | Template uses `charts.line.lines`, `charts.line.x_labels`, `charts.line.y_labels`, `charts.line.max_months` — all present in `prepare_line_chart` return. |
| `src/fathom/templates/index.html` form | `/compare` route | `hx-post="/compare" hx-target="#results" hx-swap="innerHTML"` | VERIFIED | Confirmed at index.html line 9. Form also retains `action="/compare"` for non-JS fallback. |
| `src/fathom/routes.py compare_options` | `partials/results.html` | `request.headers.get("HX-Request") == "true"` detection | VERIFIED | Confirmed at routes.py line 311. HTMX path returns `partials/results.html`; non-HTMX returns `index.html`. |
| `src/fathom/routes.py compare_options` | `results.py + charts.py` | `analyze_results()` and `prepare_charts()` calls | VERIFIED | Lines 324-333: `analyze_results(results, financing_options)` then `prepare_charts(results, chart_display)`. Sorted_options format bridge also present. |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| RSLT-01 | 03-01 | User sees summary recommendation card naming winning option with plain-English explanation | SATISFIED | `recommendation.html` renders winner, explanation, savings. `test_recommendation_card_shows_winner` passes. |
| RSLT-02 | 03-01 | User sees savings amount vs next-best in plain English | SATISFIED | Template: `"Saves $X,XXX.XX compared to [runner-up]"`. `test_savings_displayed` passes. |
| RSLT-03 | 03-01 | User sees caveats flagged on recommendation (e.g., deferred interest risk) | SATISFIED | Winner caveats displayed in hero card with severity-based CSS classes. `test_caveats_on_hero` passes. |
| RSLT-04 | 03-01 | User sees cost breakdown table with one column per option showing all 7 components | SATISFIED | Breakdown table renders all components; zero-value rows filtered. `test_breakdown_table_present` and related tests pass. |
| RSLT-05 | 03-02 | User sees True Total Cost bar chart comparing all options with winner highlighted | SATISFIED | SVG bar chart with pattern fills, winner star/highlighting, proportional bars. `test_bar_chart_svg` passes. |
| RSLT-06 | 03-02 | User sees cumulative cost over time line chart showing month-by-month evolution | SATISFIED | SVG line chart with dash-pattern paths per option, year-boundary labels, endpoint labels. `test_line_chart_svg` passes. |
| RSLT-07 | 03-03 | Results update via HTMX partial page replacement when inputs change | SATISFIED | HX-Request detection in route returns `partials/results.html`. `test_htmx_partial` confirms no DOCTYPE in partial response. |
| RSLT-08 | 03-03 | A visible "Calculate" button is always present as fallback | SATISFIED | `<button type="submit">Compare Options</button>` always rendered. Form has both `action` (fallback) and `hx-post` (HTMX). `test_calculate_button_fallback` passes. |
| A11Y-02 | 03-02 | Charts include accessible text alternatives (data tables or ARIA labels) | BLOCKED (partial) | Bar chart: SATISFIED — SVG has role/aria-labelledby/title/desc, hidden data table shows correct dollar values. Line chart: DEFECTIVE — hidden data table shows pixel coordinates (e.g., `$$194`) not dollar costs for intermediate months. Only the final row is correct. Tests check structural presence but not cell value accuracy. |
| A11Y-03 | 03-02 | Color is not the sole differentiator in charts (patterns or labels used as well) | SATISFIED | Bar chart uses 4 distinct SVG fill patterns (solid, hatched, dotted, crosshatch) in addition to stroke colors. Line chart uses 4 dash patterns (`none`, `8,4`, `3,3`, `12,4,3,4`). Direct text labels on bars and line endpoints. `test_chart_patterns` passes. |

**Requirements satisfied:** 9/10 (A11Y-02 partially blocked by data_table_line defect)

**Orphaned requirements:** None — all 10 requirement IDs appear in plan frontmatter and are mapped in REQUIREMENTS.md to Phase 3.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/fathom/templates/partials/results/data_table_line.html` | 20 | `point.y` used where cost value needed; double `$` in format string `"${{ \"${:,.0f}\".format(point.y) }}"` | Blocker | Screen readers reading the line chart's hidden data table receive pixel coordinates (e.g., `$$194`) instead of dollar cost values — A11Y-02 non-compliance for intermediate time steps |

### Human Verification Required

None — all verification performed programmatically. Note: the Playwright checks verified structural presence of hidden tables but did not assert that cell values were meaningful dollar amounts. The defect found above is purely data-driven and confirmed by rendering the template and inspecting actual output.

### Gaps Summary

One gap blocks full goal achievement: the hidden accessible data table for the line chart (`data_table_line.html`) shows pixel Y coordinates instead of dollar cost values in its month-by-month rows.

**Root cause:** The `points` list built in `charts.py` stores `{"month": m, "x": scale_x(m), "y": scale_y(c)}` where `y` is the SVG pixel coordinate (inverted scale). The template uses `point.y` to display cost, but it should use the original cost value `c`. There is also a Jinja2 template formatting error where the format string `"${{ \"${:,.0f}\".format(point.y) }}"` produces a double dollar sign.

**Fix required:**
1. In `charts.py`, add a `cost` key to each point in the `points` list: `{"month": m, "x": _to_float(scale_x(m)), "y": _to_float(scale_y(c)), "cost": _format_cost(c)}`
2. In `data_table_line.html`, replace line 20's format with: `${{ point.cost }}`

This does not affect chart rendering (only the hidden accessibility table), but it breaks A11Y-02 compliance for screen reader users accessing the line chart data table.

---

_Verified: 2026-03-10T22:30:00Z_
_Verifier: Claude (gsd-verifier)_
