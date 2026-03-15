---
phase: 14-engine-corrections
plan: 01
subsystem: engine
tags: [promo, deferred-interest, amortization, two-phase-schedule, decimal]

# Dependency graph
requires:
  - phase: 13-centralize-monetary-rounding
    provides: quantize_money canonical function
provides:
  - Two-phase promo schedule (min payments + post-promo amortization)
  - Materially different costs for retroactive vs forward-only vs paid-on-time
  - _PromoContext dataclass for promo calculation state
  - Updated comparison period accounting for 2x promo terms
affects: [15-cumulative-cost-fix, 16-test-backfill]

# Tech tracking
tech-stack:
  added: []
  patterns: [two-phase-schedule, promo-context-dataclass, pool-model-opp-cost]

key-files:
  created: []
  modified:
    - src/fathom/engine.py
    - tests/test_engine.py
    - tests/conftest.py

key-decisions:
  - "Used _PromoContext dataclass to bundle promo params and satisfy ruff PLR0913 complexity limits"
  - "Computed opportunity cost inline using pool model rather than creating synthetic FinancingOption"
  - "Min payment = required_monthly / 2 as promo not-paid-on-time assumption"

patterns-established:
  - "Two-phase schedule: min payments during promo, then amortization post-promo"
  - "_PromoContext dataclass for passing grouped promo state between helpers"

requirements-completed: [ENG-01, TEST-01]

# Metrics
duration: 6min
completed: 2026-03-15
---

# Phase 14 Plan 01: Fix Promo Penalty Modeling Summary

**Two-phase promo schedule with retroactive vs forward-only interest producing materially different costs verified by exact Decimal assertions**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-15T14:33:58Z
- **Completed:** 2026-03-15T14:40:22Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Rewrote _build_promo_result to build custom two-phase MonthlyDataPoint series instead of delegating to _build_loan_result
- Retroactive interest now adds principal * APR * term/12 to post-promo balance, producing materially higher costs
- Forward-only uses remaining principal only, producing intermediate costs
- Tests verify invariant: retroactive > forward-only > paid-on-time with exact Decimal values
- Updated _determine_comparison_period to account for 2x promo term

## Task Commits

Each task was committed atomically:

1. **Task 1: Add test fixtures and write failing promo penalty tests** - `98e51c0` (test)
2. **Task 2: Rewrite _build_promo_result with two-phase schedule** - `40bbd51` (feat)

## Files Created/Modified
- `src/fathom/engine.py` - Rewritten _build_promo_result with two-phase schedule, _PromoContext dataclass, extracted helpers
- `tests/test_engine.py` - 6 new promo penalty tests with exact Decimal assertions
- `tests/conftest.py` - Added promo_forward_only and promo_retroactive fixtures

## Decisions Made
- Used _PromoContext dataclass to bundle 6 promo parameters and satisfy ruff PLR0913 (max 5 args) limits
- Computed opportunity cost inline using the pool model rather than creating a synthetic FinancingOption, since the two-phase payment stream doesn't map to standard option parameters
- Min payment set to required_monthly / 2 as the not-paid-on-time assumption

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Extracted helper functions for ruff complexity limits**
- **Found during:** Task 2 (engine rewrite)
- **Issue:** Initial _build_promo_result had 74 statements (limit 50) and 14 branches (limit 12)
- **Fix:** Extracted _build_promo_phases, _compute_promo_opp_cost, _compute_promo_inflation, _compute_promo_tax, _build_not_paid_result helpers with _PromoContext dataclass
- **Files modified:** src/fathom/engine.py
- **Verification:** uv run ruff check . passes clean
- **Committed in:** 40bbd51 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed ty type error on sum() return type**
- **Found during:** Task 2 (engine rewrite)
- **Issue:** sum(generator) without start value returns Decimal | Literal[0], failing ty check
- **Fix:** Added Decimal(0) as start value to sum() call
- **Files modified:** src/fathom/engine.py
- **Verification:** uv run ty check passes clean
- **Committed in:** 40bbd51 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both auto-fixes necessary for quality gate compliance. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Engine correctly models three promo scenarios with materially different costs
- Ready for Phase 15 (cumulative cost fix) and Phase 16 (test backfill)
- Comparison period now accounts for 2x promo terms, which may affect chart rendering

---
*Phase: 14-engine-corrections*
*Completed: 2026-03-15*
