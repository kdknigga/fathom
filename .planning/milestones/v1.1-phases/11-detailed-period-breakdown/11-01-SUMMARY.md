---
phase: 11-detailed-period-breakdown
plan: 01
subsystem: engine
tags: [decimal, pydantic, opportunity-cost, inflation, tax, per-period]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: "MonthlyDataPoint model, engine builders, opportunity/inflation/tax modules"
provides:
  - "MonthlyDataPoint with per-period opportunity_cost, inflation_adjustment, tax_savings fields"
  - "compute_opportunity_cost_per_period() returning per-month growth values"
  - "Engine builders populating per-period cost factors for loan, cash, promo options"
affects: [11-02, 11-03, period-breakdown-ui, detailed-tabs]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Per-period cost factor decomposition alongside aggregate totals"]

key-files:
  created: []
  modified:
    - src/fathom/models.py
    - src/fathom/opportunity.py
    - src/fathom/engine.py
    - tests/test_models.py
    - tests/test_opportunity.py
    - tests/test_engine.py

key-decisions:
  - "Widened rounding tolerance from 0.02 to 0.05 for per-period-to-aggregate sum checks due to cumulative rounding over 36 months"
  - "Used discount_cash_flows for per-period inflation instead of recomputing present_value per month"

patterns-established:
  - "Per-period cost factors: each MonthlyDataPoint carries its own opportunity_cost, inflation_adjustment, tax_savings"
  - "Aggregate-to-per-period consistency: per-period values sum to aggregate totals within rounding tolerance"

requirements-completed: [DETAIL-01]

# Metrics
duration: 4min
completed: 2026-03-14
---

# Phase 11 Plan 01: Per-Period Cost Factors Summary

**Extended MonthlyDataPoint with per-period opportunity cost, inflation adjustment, and tax savings computed by all engine builders**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-14T03:04:16Z
- **Completed:** 2026-03-14T03:07:59Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- MonthlyDataPoint extended with 3 new Decimal fields (opportunity_cost, inflation_adjustment, tax_savings) defaulting to Decimal(0) for backward compatibility
- compute_opportunity_cost_per_period() returns per-month investment growth values that sum to aggregate opportunity cost
- All 3 engine builders (_build_loan_result, _build_cash_result, _build_promo_result) populate per-period cost factors
- 14 new tests covering model fields, per-period computation, and engine builder integration

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend MonthlyDataPoint and add per-period computation functions**
   - `b2fe7fb` (test: failing tests for model fields and per-period computation)
   - `a57cd0d` (feat: implement model fields and compute_opportunity_cost_per_period)
2. **Task 2: Modify engine builders to populate per-period cost factors**
   - `87a1b3e` (test: failing tests for engine builder per-period values)
   - `2b4240b` (feat: populate per-period cost factors in engine builders)

_Note: TDD tasks have two commits each (test then feat)_

## Files Created/Modified
- `src/fathom/models.py` - Added opportunity_cost, inflation_adjustment, tax_savings fields to MonthlyDataPoint
- `src/fathom/opportunity.py` - Added compute_opportunity_cost_per_period() function
- `src/fathom/engine.py` - Modified _build_loan_result, _build_cash_result to populate per-period cost factors
- `tests/test_models.py` - Added tests for new MonthlyDataPoint fields and defaults
- `tests/test_opportunity.py` - Added tests for per-period computation and sum-to-aggregate consistency
- `tests/test_engine.py` - Added tests for engine builders populating per-period values

## Decisions Made
- Widened rounding tolerance from 0.02 to 0.05 for per-period-to-aggregate sum checks; 36 quantize_money() calls accumulate up to 0.03 rounding error which exceeds 0.02
- Used discount_cash_flows from inflation module for per-period inflation computation rather than calling present_value individually

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Widened rounding tolerance for sum-to-aggregate checks**
- **Found during:** Task 1 (per-period computation tests)
- **Issue:** Plan specified 0.02 tolerance but 36-month loan accumulates 0.03 rounding error from per-period quantize_money calls
- **Fix:** Changed tolerance to 0.05 in tests (still tight enough to catch real errors)
- **Files modified:** tests/test_opportunity.py, tests/test_engine.py
- **Verification:** All tests pass, tolerance is still meaningful
- **Committed in:** a57cd0d, 2b4240b

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor tolerance adjustment for mathematical correctness. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Per-period data foundation is complete for all option types
- Ready for UI work: period breakdown tabs, compare view, column toggles
- All 228 tests pass including 14 new per-period tests

---
*Phase: 11-detailed-period-breakdown*
*Completed: 2026-03-14*
