---
phase: 01-calculation-engine
plan: 03
subsystem: calculation
tags: [engine, caveats, orchestrator, comparison, true-total-cost, promo, decimal]

# Dependency graph
requires:
  - phase: 01-calculation-engine/plan-01
    provides: "Domain models (FinancingOption, GlobalSettings, MonthlyDataPoint, ComparisonResult), pytest fixtures"
  - phase: 01-calculation-engine/plan-02
    provides: "Amortization, opportunity cost, inflation, and tax calculation modules"
provides:
  - "Engine compare() orchestrator composing all calculation modules into ComparisonResult"
  - "Caveat generation: deferred interest risk, high interest total, opportunity cost dominance"
  - "Dual-outcome PromoResult for 0% promo options"
  - "Comparison period normalization to longest loan term"
affects: [02-web-layer, 03-results-display]

# Tech tracking
tech-stack:
  added: []
  patterns: [orchestrator-pattern, dual-outcome-modeling, sensitivity-analysis, list-extend-comprehension]

key-files:
  created: []
  modified:
    - src/fathom/engine.py
    - src/fathom/caveats.py
    - tests/test_engine.py
    - tests/test_caveats.py

key-decisions:
  - "generate_caveats takes (option, result) without settings param; generate_all_caveats orchestrates cross-option checks with settings"
  - "Opportunity cost sensitivity uses 10% threshold for significance detection"
  - "Promo not-paid-on-time scenario models full principal at post-promo APR with retroactive interest"

patterns-established:
  - "list.extend with generator expression instead of append-in-loop (ruff PERF401)"
  - "Unused pytest import removed when xfail markers are stripped"

requirements-completed: [CALC-03, CALC-05, QUAL-01, QUAL-02, QUAL-03, QUAL-04, QUAL-06]

# Metrics
duration: 4min
completed: 2026-03-10
---

# Phase 1 Plan 03: Engine Orchestrator and Caveats Summary

**Engine compare() API composing amortization, opportunity cost, inflation, and tax into True Total Cost with three caveat types and dual-outcome promo modeling**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-10T17:17:27Z
- **Completed:** 2026-03-10T17:21:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Engine compare() function orchestrates all calculation modules into a single ComparisonResult with per-option OptionResult or PromoResult
- Three caveat types: deferred interest risk (with break-even month and required payment), high interest total (>30% of price), opportunity cost dominance (winner changes at +/-2% return rate)
- Dual-outcome PromoResult for 0% promo options: paid_on_time vs not_paid_on_time scenarios
- Comparison period normalization to longest loan term; all-cash comparisons return period=0
- True Total Cost formula: total_payments + opportunity_cost - rebates - tax_savings + inflation_adjustment
- Full quality gate passed: 24 tests, ruff lint, ruff format, ty check, pyrefly check, prek hooks -- zero errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement caveats module and engine orchestrator** - `b28d10d` (feat)
2. **Task 2: Full code quality gate** - no changes needed (all gates already passing)

## Files Created/Modified
- `src/fathom/engine.py` - Top-level compare() orchestrating all modules, builds OptionResult/PromoResult per option type
- `src/fathom/caveats.py` - generate_caveats (per-option), generate_all_caveats (cross-option), check_opportunity_cost_sensitivity
- `tests/test_engine.py` - Removed xfail markers; tests for normalization, TTC formula, cash vs loan, all-cash, dual-outcome promo
- `tests/test_caveats.py` - Removed xfail markers; tests for deferred interest, opportunity cost dominance, high interest, all-options coverage

## Decisions Made
- Separated generate_caveats (per-option, no settings needed) from generate_all_caveats (cross-option with settings) to avoid unused-argument lint errors while maintaining clean API
- Opportunity cost sensitivity threshold set at 10% change to detect meaningful ranking shifts at +/-2% return rate
- Promo not-paid-on-time scenario uses full principal at post-promo APR for retroactive interest (worst case modeling)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed ruff ARG001 unused settings parameter**
- **Found during:** Task 1 (caveats implementation)
- **Issue:** generate_caveats had `settings` parameter that wasn't used in per-option checks (only needed for cross-option sensitivity)
- **Fix:** Removed `settings` from generate_caveats signature; only generate_all_caveats takes settings for cross-option checks
- **Files modified:** src/fathom/caveats.py, tests/test_caveats.py
- **Verification:** ruff check passes, all tests pass
- **Committed in:** b28d10d (Task 1 commit)

**2. [Rule 3 - Blocking] Fixed ruff PERF401 append-in-loop pattern**
- **Found during:** Task 1 (engine implementation)
- **Issue:** Engine used for-loop with append instead of list.extend with generator
- **Fix:** Converted two append-in-loop patterns to list.extend with generator expressions
- **Files modified:** src/fathom/engine.py
- **Verification:** ruff check passes, all tests pass
- **Committed in:** b28d10d (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both were lint rule compliance fixes. No scope creep.

## Issues Encountered
None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Engine compare() is the public API for Phase 2 web layer
- All 24 tests provide regression safety for web layer integration
- Clean quality gates ensure maintainable codebase for future phases
- Phase 1 calculation engine is complete

---
*Phase: 01-calculation-engine*
*Completed: 2026-03-10*

## Self-Check: PASSED

- All 4 files verified present on disk
- Commit b28d10d (Task 1) verified in git log
- 24/24 tests passing
- All quality gates clean (ruff, ty, pyrefly, prek)
