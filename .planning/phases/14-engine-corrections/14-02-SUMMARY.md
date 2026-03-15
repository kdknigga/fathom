---
phase: 14-engine-corrections
plan: 02
subsystem: engine, charts
tags: [cumulative-cost, true-cost, line-chart, promo, dual-lines, svg]

# Dependency graph
requires:
  - phase: 14-engine-corrections/01
    provides: Promo penalty modeling with two-phase schedule
provides:
  - Cumulative true cost computation in all engine builders
  - Dual promo lines on line chart (paid-on-time solid, not-paid dashed)
  - Chart title "Cumulative True Cost Over Time"
affects: [15-test-coverage, 16-final-polish]

# Tech tracking
tech-stack:
  added: []
  patterns: [cumulative-true-cost-formula, dual-line-promo-chart]

key-files:
  created: []
  modified:
    - src/fathom/engine.py
    - src/fathom/charts.py
    - src/fathom/routes.py
    - tests/test_engine.py
    - tests/test_charts.py

key-decisions:
  - "Derive is_not_paid from name suffix inside _build_line_dataset to avoid PLR0913"
  - "Cumulative cost starts at 0 (not down payment) to match results.py formula"
  - "Padded months continue accumulating opportunity cost rather than freezing"

patterns-established:
  - "True cost formula: payment + opportunity_cost - tax_savings + inflation_adjustment (consistent across engine and results)"
  - "NOT_PAID_SUFFIX constant for detecting not-paid-on-time entries by name"

requirements-completed: [ENG-02, TEST-02]

# Metrics
duration: 5min
completed: 2026-03-15
---

# Phase 14 Plan 02: Cumulative True Cost & Dual Promo Lines Summary

**Fixed cumulative_cost to track true cost (payment + opp - tax + inflation) in all engine builders, added dual promo lines to chart with dashed not-paid stroke**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-15T14:42:57Z
- **Completed:** 2026-03-15T14:48:30Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- All three engine builders (cash, loan, promo) now compute cumulative_cost as running sum of true cost factors, matching results.py formula exactly
- Line chart plots cumulative true cost with title "Cumulative True Cost Over Time"
- Promo options produce dual lines: solid for paid-on-time, dashed (6,4 pattern) for not-paid-on-time
- Cross-validation test confirms engine cumulative_cost matches results._monthly_data_to_rows output

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix cumulative_cost (RED)** - `1e650e0` (test)
2. **Task 1: Fix cumulative_cost (GREEN)** - `2c42b7b` (feat)
3. **Task 2: Dual promo lines and chart label** - `31fed7f` (feat)

_Note: Task 1 used TDD with RED/GREEN commits_

## Files Created/Modified
- `src/fathom/engine.py` - Fixed cumulative_cost in _build_cash_result, _build_loan_result, and _build_not_paid_result
- `src/fathom/charts.py` - Added NOT_PAID_SUFFIX/DASH constants, dual-line detection in _collect_option_points, title in prepare_line_chart
- `src/fathom/routes.py` - Include not-paid entries in sorted_options for chart rendering
- `tests/test_engine.py` - 4 new tests for cumulative true cost across all builders
- `tests/test_charts.py` - 5 new tests for dual lines, dash pattern, color, and title

## Decisions Made
- Cumulative cost starts at 0 (not down payment) to match results.py formula -- down payment is included in the payment stream
- Derived is_not_paid from name suffix inside _build_line_dataset rather than passing parameter to avoid PLR0913 (too many args)
- Padded months beyond loan term continue accumulating opportunity cost rather than freezing at final value

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Engine corrections phase complete -- both cumulative cost and promo penalty modeling fixed
- Ready for Phase 15 (test coverage backfill) or Phase 16 (final polish)

## Self-Check: PASSED

All 5 files found. All 3 commits verified.

---
*Phase: 14-engine-corrections*
*Completed: 2026-03-15*
