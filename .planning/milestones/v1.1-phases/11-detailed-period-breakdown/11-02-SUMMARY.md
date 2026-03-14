---
phase: 11-detailed-period-breakdown
plan: 02
subsystem: ui
tags: [htmx, jinja2, aria, tablist, css, javascript, detailed-breakdown]

# Dependency graph
requires:
  - phase: 11-detailed-period-breakdown
    provides: "MonthlyDataPoint with per-period cost factors from plan 01"
provides:
  - "HTMX tab UI for per-option detailed period tables"
  - "Compare tab with side-by-side payment and cumulative cost"
  - "Column toggle JS with HTMX afterSwap state persistence"
  - "Monthly/annual granularity toggle"
  - "build_detailed_breakdown, aggregate_annual, build_compare_data functions"
affects: [11-03, browser-verification, accessibility]

# Tech tracking
tech-stack:
  added: []
  patterns: ["HTMX tab pattern with hx-post for lazy loading per-tab content", "CSS class-based column toggle with JS state object"]

key-files:
  created:
    - src/fathom/templates/partials/results/detailed_breakdown.html
    - src/fathom/templates/partials/results/detailed_table.html
    - src/fathom/templates/partials/results/detailed_compare.html
    - src/fathom/static/detail_toggle.js
  modified:
    - src/fathom/results.py
    - src/fathom/routes.py
    - src/fathom/templates/partials/results.html
    - src/fathom/templates/base.html
    - src/fathom/static/style.css
    - tests/test_routes.py
    - tests/test_results_helpers.py

key-decisions:
  - "Used tuple variable pattern for except clause (_detail_parse_errors) to match project convention for Python 3.12 pre-commit hook compatibility"
  - "Computed cumulative_true_total_cost as running sum of (payment + opportunity_cost - tax_savings + inflation_adjustment) per period"
  - "Used HTMX hx-include='#comparison-form' on tab buttons so detail endpoints can reprocess form data without session state"

patterns-established:
  - "HTMX lazy tab loading: tab buttons POST to detail endpoints with form data included, server renders partial"
  - "Column toggle pattern: JS hiddenCols object tracks state, applyHidden() reapplies on afterSwap"

requirements-completed: [DETAIL-02, DETAIL-03, DETAIL-04, DETAIL-05]

# Metrics
duration: 6min
completed: 2026-03-14
---

# Phase 11 Plan 02: Detailed Period Breakdown UI Summary

**Interactive tabbed period breakdown with per-option tables, compare view, column toggles, and monthly/annual granularity via HTMX**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-14T03:10:19Z
- **Completed:** 2026-03-14T03:16:21Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- Three new results.py functions: build_detailed_breakdown, aggregate_annual, build_compare_data for transforming per-period data into table-ready structures
- Two HTMX routes: /partials/detail/<idx> and /partials/detail/compare for lazy tab loading
- Three Jinja2 templates: tab container with ARIA tablist, per-option detail table with promo dual columns, compare table with side-by-side view
- Column toggle JS with HTMX afterSwap persistence, tab keyboard navigation (arrow keys, Home/End), and granularity toggle
- CSS for underline tabs, sticky totals footer, scroll container, and checkbox row (all dark-mode compatible via CSS variables)
- 7 new integration tests and 7 new unit tests (241 total pass)

## Task Commits

Each task was committed atomically:

1. **Task 1: Backend -- results module functions, routes, and templates** - `73f93c5` (feat)
2. **Task 2: Client-side JS and CSS for column toggles, tabs, and sticky totals** - `55c3488` (feat)

## Files Created/Modified
- `src/fathom/results.py` - Added build_detailed_breakdown, aggregate_annual, build_compare_data, helper functions
- `src/fathom/routes.py` - Added /partials/detail/<idx> and /partials/detail/compare HTMX endpoints
- `src/fathom/templates/partials/results/detailed_breakdown.html` - Tab container with ARIA tablist, column toggles, granularity switch
- `src/fathom/templates/partials/results/detailed_table.html` - Per-option period table with promo dual columns
- `src/fathom/templates/partials/results/detailed_compare.html` - Side-by-side compare table
- `src/fathom/static/detail_toggle.js` - Column toggle, tab keyboard nav, granularity switch JS
- `src/fathom/static/style.css` - Tab, sticky totals, scroll container, checkbox row styles
- `src/fathom/templates/partials/results.html` - Added detailed breakdown section include
- `src/fathom/templates/base.html` - Added detail_toggle.js script tag
- `tests/test_routes.py` - Added 7 integration tests for detail endpoints
- `tests/test_results_helpers.py` - Added 7 unit tests for breakdown helper functions

## Decisions Made
- Used tuple variable pattern (_detail_parse_errors) for except clause to match project convention for Python 3.12 pre-commit compatibility
- Computed cumulative_true_total_cost as running sum of per-period net cost (payment + opp_cost - tax_savings + inflation_adj) rather than using the existing cumulative_cost field
- Used HTMX hx-include on tab buttons to reprocess full form data per request (stateless approach matching project architecture)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Full detailed breakdown UI is functional and tested
- Ready for Plan 03 browser verification via Playwright
- All 241 tests pass, linting and formatting clean

---
*Phase: 11-detailed-period-breakdown*
*Completed: 2026-03-14*
