---
phase: 01-calculation-engine
plan: 02
subsystem: calculation
tags: [decimal, amortization, opportunity-cost, inflation, tax, tdd, pure-functions]

# Dependency graph
requires:
  - phase: 01-calculation-engine/plan-01
    provides: "Domain models (FinancingOption, GlobalSettings, MonthlyDataPoint), pytest fixtures, xfail test stubs"
provides:
  - "Amortization calculation with schedule generation (monthly_payment, amortization_schedule)"
  - "Opportunity cost with decreasing investment pool and freed-cash investing"
  - "Present value inflation discounting (present_value, discount_cash_flows, discount_payment_series)"
  - "Tax savings computation from deductible interest payments"
affects: [01-calculation-engine]

# Tech tracking
tech-stack:
  added: []
  patterns: [pure-function-modules, decimal-arithmetic, zero-clamping-pool, tdd-green-phase]

key-files:
  created: []
  modified:
    - src/fathom/amortization.py
    - src/fathom/opportunity.py
    - src/fathom/inflation.py
    - src/fathom/tax.py
    - tests/test_amortization.py
    - tests/test_opportunity.py
    - tests/test_inflation.py
    - tests/test_tax.py

key-decisions:
  - "Opportunity cost computed as total investment returns (sum of monthly growth), not pool difference"
  - "Pool exhaustion test adjusted to use parameters where pool actually drains to zero within term"
  - "quantize_money helper duplicated per module to keep modules independent (no shared utils yet)"

patterns-established:
  - "sum(decimals, Decimal(0)) pattern required by ty type checker to avoid Decimal | Literal[0] union"
  - "ruff auto-fix for D213 docstring style and D413 blank-line-after-last-section on every commit"

requirements-completed: [CALC-01, CALC-02, CALC-04, CALC-06, CALC-07, CALC-08]

# Metrics
duration: 6min
completed: 2026-03-10
---

# Phase 1 Plan 02: Core Calculation Modules Summary

**Four pure-function Decimal calculation modules: amortization with schedule, decreasing-pool opportunity cost, PV inflation discounting, and interest tax savings**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-10T17:09:00Z
- **Completed:** 2026-03-10T17:15:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Amortization module: standard formula with zero-APR guard, full schedule generation with last-payment adjustment clearing exact balance
- Opportunity cost module: decreasing investment pool model where cash grows then payments deducted, pool clamps to zero, freed-cash investing after shorter loans end
- Inflation module: present value discounting per month, cash flow series discounting, inflation adjustment calculation
- Tax module: tax savings from sum of deductible interest times marginal rate
- All 15 tests passing (9 amortization+opportunity, 6 inflation+tax), all xfail markers removed

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement amortization and opportunity cost modules** - `6a1a474` (feat)
2. **Task 2: Implement inflation and tax modules** - `5c2cd9e` (feat)

## Files Created/Modified
- `src/fathom/amortization.py` - monthly_payment and amortization_schedule with Decimal arithmetic
- `src/fathom/opportunity.py` - compute_opportunity_cost and compute_opportunity_cost_series with pool model
- `src/fathom/inflation.py` - present_value, discount_cash_flows, discount_payment_series, compute_inflation_adjustment
- `src/fathom/tax.py` - compute_tax_savings from interest payments and marginal rate
- `tests/test_amortization.py` - Removed xfail markers, unused pytest import
- `tests/test_opportunity.py` - Removed xfail markers, fixed pool exhaustion test parameters
- `tests/test_inflation.py` - Removed xfail markers, unused pytest import
- `tests/test_tax.py` - Removed xfail markers, unused pytest import

## Decisions Made
- Opportunity cost is calculated as total investment returns (sum of monthly pool growth), not as final-pool-minus-initial-pool, which correctly handles pool exhaustion and freed-cash phases
- Pool exhaustion test modified to use $5k loan at 2% return (instead of $10k at 7%) so the pool actually drains to zero within the loan term -- original parameters had too much return growth to exhaust
- Used `sum(values, Decimal(0))` pattern throughout to satisfy ty type checker (plain `sum()` returns `Decimal | Literal[0]` union)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed pool exhaustion test parameters**
- **Found during:** Task 1 (opportunity cost implementation)
- **Issue:** Original test used standard_loan ($10k, 6%, 36mo) with 7% return -- pool never actually reaches zero within 36 months due to high return rate
- **Fix:** Changed test to use $5k loan at 2% return with 36-month term and comparison, where pool drains to zero at month 34
- **Files modified:** tests/test_opportunity.py
- **Verification:** Test passes, pool hits zero and stays zero
- **Committed in:** 6a1a474 (Task 1 commit)

**2. [Rule 1 - Bug] Fixed opportunity cost calculation to use total returns**
- **Found during:** Task 1 (opportunity cost implementation)
- **Issue:** Initial implementation computed opportunity cost as final_pool - initial_pool, yielding negative values for loan buyers (pool drains below initial investment)
- **Fix:** Changed to sum of monthly investment growth across entire comparison period
- **Files modified:** src/fathom/opportunity.py
- **Verification:** All opportunity cost tests pass including freed-cash-after-payoff
- **Committed in:** 6a1a474 (Task 1 commit)

**3. [Rule 3 - Blocking] Fixed ty type checker error on sum() return type**
- **Found during:** Task 2 (inflation module)
- **Issue:** `sum(list[Decimal])` returns `Decimal | Literal[0]` per ty, incompatible with `quantize_money(Decimal)` parameter
- **Fix:** Used `sum(values, Decimal(0))` to force Decimal return type
- **Files modified:** src/fathom/inflation.py, src/fathom/tax.py
- **Verification:** ty check passes clean
- **Committed in:** 5c2cd9e (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 blocking)
**Impact on plan:** All auto-fixes necessary for correctness and type safety. No scope creep.

## Issues Encountered
- ruff D213 and D413 rules auto-fixed docstring formatting on every pre-commit hook run (expected, documented in Plan 01 patterns)

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All four calculation modules ready for composition by the engine orchestrator in Plan 03
- Functions export clean APIs: amortization_schedule returns MonthlyDataPoint list, opportunity cost takes FinancingOption+GlobalSettings
- 15 unit tests provide regression safety for engine integration work

---
*Phase: 01-calculation-engine*
*Completed: 2026-03-10*

## Self-Check: PASSED

- All 8 files verified present on disk
- Commit 6a1a474 (Task 1) verified in git log
- Commit 5c2cd9e (Task 2) verified in git log
- 15/15 tests passing
- All quality gates clean (ruff, ty, pyrefly)
