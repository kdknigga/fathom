---
phase: 13-centralize-monetary-rounding
plan: 01
subsystem: engine
tags: [decimal, rounding, refactoring, dry]

requires: []
provides:
  - "Canonical money.py module with quantize_money() and CENTS"
  - "Single import path for all monetary rounding: fathom.money"
affects: [14-fix-promo-penalty, 15-engine-edge-cases, 16-test-backfill]

tech-stack:
  added: []
  patterns:
    - "All monetary rounding imports from fathom.money"

key-files:
  created:
    - src/fathom/money.py
  modified:
    - src/fathom/amortization.py
    - src/fathom/opportunity.py
    - src/fathom/inflation.py
    - src/fathom/caveats.py
    - src/fathom/tax.py
    - src/fathom/engine.py

key-decisions:
  - "Kept quantize_money signature identical to existing copies -- no new parameters"

patterns-established:
  - "Import monetary rounding from fathom.money, never define locally"

requirements-completed: [ENG-03]

duration: 2min
completed: 2026-03-15
---

# Phase 13 Plan 01: Centralize Monetary Rounding Summary

**Single canonical money.py module replacing 5 duplicate quantize_money()/CENTS definitions across calculation modules**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-15T13:45:50Z
- **Completed:** 2026-03-15T13:47:40Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Created src/fathom/money.py as the single source of truth for monetary rounding
- Removed 5 duplicate CENTS constant and quantize_money() definitions
- Updated 6 consumer files to import from the canonical module
- All 283 tests pass with zero behavior change

## Task Commits

Each task was committed atomically:

1. **Task 1: Create money.py canonical module** - `303867f` (feat)
2. **Task 2: Replace duplicate definitions with imports from money.py** - `003e065` (refactor)

## Files Created/Modified
- `src/fathom/money.py` - Canonical monetary rounding utilities (CENTS constant, quantize_money function)
- `src/fathom/amortization.py` - Removed local CENTS/quantize_money, imports from money.py
- `src/fathom/opportunity.py` - Removed local CENTS/quantize_money, imports from money.py
- `src/fathom/inflation.py` - Removed local CENTS/quantize_money, imports from money.py
- `src/fathom/caveats.py` - Removed local CENTS/quantize_money, imports from money.py
- `src/fathom/tax.py` - Removed local CENTS/quantize_money, imports from money.py
- `src/fathom/engine.py` - Changed quantize_money import source from amortization to money

## Decisions Made
- Kept quantize_money function signature identical to existing copies (no rounding mode parameter, no new functionality) to ensure zero behavior change

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Monetary rounding centralized, eliminating drift risk for future calculation changes
- Ready for Phase 14 (promo penalty fix) which may need rounding adjustments

## Self-Check: PASSED

- FOUND: src/fathom/money.py
- FOUND: commit 303867f
- FOUND: commit 003e065

---
*Phase: 13-centralize-monetary-rounding*
*Completed: 2026-03-15*
