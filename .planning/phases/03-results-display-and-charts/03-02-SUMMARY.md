---
phase: 03-results-display-and-charts
plan: 02
subsystem: ui
tags: [svg, charts, accessibility, jinja2, wcag]

# Dependency graph
requires:
  - phase: 01-calculation-engine
    provides: ComparisonResult, OptionResult, PromoResult, MonthlyDataPoint models
provides:
  - prepare_bar_chart function for bar chart coordinate computation
  - prepare_line_chart function for line chart path computation
  - prepare_charts convenience function combining both
  - SVG bar chart template with pattern fills and direct labels
  - SVG line chart template with dash patterns and endpoint labels
  - Hidden accessible data tables for screen reader access
affects: [03-results-display-and-charts, 04-integration]

# Tech tracking
tech-stack:
  added: []
  patterns: [server-rendered SVG charts, pattern fill accessibility, TYPE_CHECKING import for Decimal]

key-files:
  created:
    - src/fathom/charts.py
    - src/fathom/templates/partials/results/bar_chart.html
    - src/fathom/templates/partials/results/line_chart.html
    - src/fathom/templates/partials/results/data_table_bar.html
    - src/fathom/templates/partials/results/data_table_line.html
    - tests/test_charts.py
  modified:
    - src/fathom/templates/partials/results.html

key-decisions:
  - "Used TYPE_CHECKING block for Decimal import to satisfy TC003 lint rule"
  - "Pattern IDs prefixed per chart type (bar-pattern-*, line-pattern-*) to avoid SVG document-scope collisions"
  - "Cash options with sparse monthly_data generate 2-point flat line at true_total_cost"
  - "Line chart samples every Nth point when comparison period exceeds 60 months"

patterns-established:
  - "Chart data prep returns plain dicts with float coordinates for Jinja2 template consumption"
  - "SVG accessibility: role=img, aria-labelledby, title, desc elements, plus hidden data tables with visually-hidden class"

requirements-completed: [RSLT-05, RSLT-06, A11Y-02, A11Y-03]

# Metrics
duration: 5min
completed: 2026-03-10
---

# Phase 3 Plan 02: SVG Charts Summary

**Server-rendered SVG bar and line charts with pattern fills, dash patterns, direct labels, and hidden accessible data tables**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-10T21:45:25Z
- **Completed:** 2026-03-10T21:50:45Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Chart data preparation module computing bar positions, line SVG paths, and scale coordinates
- SVG bar chart with 4 pattern fills (solid, hatched, dotted, crosshatch), winner highlighting, and direct value labels
- SVG line chart with dash patterns, grid lines, year boundary X-axis labels, and endpoint cost labels
- Hidden data tables below each chart for screen reader access (WCAG 2.1 AA)
- 13 unit tests covering bar count, winner detection, proportional heights, pattern prefixes, coordinate types, path format, dash patterns, cash flat lines, year boundaries, endpoint labels

## Task Commits

Each task was committed atomically:

1. **Task 1: Chart data preparation module and tests** - `0bd2290` (feat, TDD)
2. **Task 2: SVG chart templates and accessible data tables** - `4159951` (feat)

## Files Created/Modified
- `src/fathom/charts.py` - Chart coordinate computation (prepare_bar_chart, prepare_line_chart, prepare_charts)
- `tests/test_charts.py` - 13 unit tests for chart data preparation
- `src/fathom/templates/partials/results/bar_chart.html` - SVG bar chart with pattern fills and direct labels
- `src/fathom/templates/partials/results/line_chart.html` - SVG line chart with dash patterns and endpoint labels
- `src/fathom/templates/partials/results/data_table_bar.html` - Hidden accessible data table for bar chart
- `src/fathom/templates/partials/results/data_table_line.html` - Hidden accessible data table for line chart
- `src/fathom/templates/partials/results.html` - Updated to conditionally include chart partials

## Decisions Made
- Used TYPE_CHECKING block for Decimal import to satisfy TC003 ruff rule while keeping runtime performance
- Pattern IDs prefixed per chart type (bar-pattern-*, line-pattern-*) to avoid SVG document-scope ID collisions when both charts render on the same page
- Cash options with sparse monthly_data (only month 0) generate a 2-point flat line spanning the full comparison period
- Line chart applies downsampling when more than 60 data points for rendering performance

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Chart data preparation and templates ready for integration with routes
- Plan 03 (HTMX wiring) will connect charts.prepare_charts to the template context
- results.html already includes conditional chart section (`{% if charts is defined %}`)

## Self-Check: PASSED

All 6 created files verified on disk. Both task commits (0bd2290, 4159951) verified in git log.

---
*Phase: 03-results-display-and-charts*
*Completed: 2026-03-10*
