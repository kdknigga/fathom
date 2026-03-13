---
phase: 01-calculation-engine
verified: 2026-03-10T18:00:00Z
status: passed
score: 17/17 must-haves verified
re_verification: false
---

# Phase 1: Calculation Engine Verification Report

**Phase Goal:** Users' financing options can be computed correctly with full True Total Cost modeling, verified by automated tests against known values
**Verified:** 2026-03-10T18:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

All must-have truths derived from the three PLAN frontmatter `must_haves` sections (plans 01, 02, and 03).

| #  | Truth                                                                                    | Status     | Evidence                                                                        |
|----|------------------------------------------------------------------------------------------|------------|---------------------------------------------------------------------------------|
| 1  | All domain types use Decimal for monetary values, never float                            | VERIFIED   | All monetary fields in models.py typed as `Decimal`; no float anywhere in src/ |
| 2  | Domain models capture all six option types with their distinct fields                    | VERIFIED   | `OptionType` enum: CASH, TRADITIONAL_LOAN, PROMO_ZERO_PERCENT, PROMO_CASH_BACK, PROMO_PRICE_REDUCTION, CUSTOM |
| 3  | Dual-outcome PromoResult exists for 0% promo options                                     | VERIFIED   | `PromoResult` dataclass with `paid_on_time`, `not_paid_on_time`, `required_monthly_payment`, `break_even_month` |
| 4  | Monthly data series structure exists for chart rendering in Phase 3                      | VERIFIED   | `MonthlyDataPoint` dataclass with all 7 fields including `investment_balance` and `cumulative_cost` |
| 5  | Caveat types are enumerated with severity levels                                         | VERIFIED   | `CaveatType` (3 values) and `Severity` (INFO/WARNING/CRITICAL) enums present    |
| 6  | pytest runs and discovers test files                                                     | VERIFIED   | `uv run pytest --collect-only` collects 24 tests across 6 files                 |
| 7  | Test fixtures provide reusable standard options and global settings                      | VERIFIED   | `conftest.py` has 6 fixtures: standard_loan, cash_option, promo_zero_percent, default_settings, settings_with_inflation, settings_with_tax |
| 8  | Standard amortization produces $304.22/month for $10k at 6% over 36 months              | VERIFIED   | `monthly_payment(10000, 0.06, 36) == Decimal("304.22")` confirmed live          |
| 9  | Zero APR handled without division by zero                                                | VERIFIED   | `monthly_payment(10000, 0.00, 36) == Decimal("277.78")` confirmed live; guard at line 44 of amortization.py |
| 10 | Cash buyer opportunity cost models full price as lump-sum investment                    | VERIFIED   | `compute_opportunity_cost` for CASH uses `purchase_price` as `initial_pool`; test passes |
| 11 | Loan buyer investment pool decreases monthly and clamps to zero                          | VERIFIED   | Pool clamped to zero in `_compute_pool_series`; `test_pool_exhaustion` passes   |
| 12 | Freed-up cash after shorter loan payoff is invested for remaining months                 | VERIFIED   | Phase 2 in `compute_opportunity_cost` runs `remaining_months` freed-cash loop; `test_freed_cash_after_payoff` passes |
| 13 | Inflation discounting produces correct present values                                    | VERIFIED   | `present_value(304.22, 0.03, 12) == Decimal("295.24")` confirmed live           |
| 14 | Tax savings equals total deductible interest times marginal rate                         | VERIFIED   | `compute_tax_savings` sums interest * rate; `test_tax_savings_basic` passes     |
| 15 | Engine normalizes all options to the longest term among active options                   | VERIFIED   | `_determine_comparison_period` returns `max(terms)`; `test_normalization_to_longest_term` passes |
| 16 | True Total Cost = total payments + opportunity cost - rebates - tax savings +/- inflation adjustment | VERIFIED | Formula verified in `_build_cash_result` and `_build_loan_result`; `test_true_total_cost` asserts this directly |
| 17 | All code passes ruff check, ruff format, ty check, pyrefly check, prek run with zero errors | VERIFIED | All five quality tools return zero errors (confirmed live)                    |

**Score:** 17/17 truths verified

---

### Required Artifacts

| Artifact                          | Provides                                            | Status      | Details                                                |
|-----------------------------------|-----------------------------------------------------|-------------|--------------------------------------------------------|
| `src/fathom/models.py`            | All domain models (inputs, outputs, enums)          | VERIFIED    | 177 lines; 3 enums, 6 dataclasses, all Decimal fields  |
| `src/fathom/amortization.py`      | Amortization calc with schedule generation          | VERIFIED    | `monthly_payment` + `amortization_schedule` fully implemented |
| `src/fathom/opportunity.py`       | Opportunity cost with decreasing investment pool    | VERIFIED    | `compute_opportunity_cost` + `compute_opportunity_cost_series` implemented |
| `src/fathom/inflation.py`         | Present value discounting                           | VERIFIED    | `present_value`, `discount_cash_flows`, `discount_payment_series`, `compute_inflation_adjustment` |
| `src/fathom/tax.py`               | Tax savings computation                             | VERIFIED    | `compute_tax_savings` implemented                      |
| `src/fathom/caveats.py`           | Caveat generation logic                             | VERIFIED    | `generate_caveats`, `generate_all_caveats`, sensitivity check implemented |
| `src/fathom/engine.py`            | Top-level `compare()` orchestrating all modules     | VERIFIED    | `compare()` fully implemented, wired to all sub-modules |
| `tests/conftest.py`               | Shared fixtures for all test modules                | VERIFIED    | 6 fixtures; imports from `fathom.models`               |
| `tests/test_amortization.py`      | 5 passing tests for amortization                    | VERIFIED    | All tests PASS, no xfail markers                       |
| `tests/test_opportunity.py`       | 4 passing tests for opportunity cost                | VERIFIED    | All tests PASS, no xfail markers                       |
| `tests/test_inflation.py`         | 3 passing tests for inflation discounting           | VERIFIED    | All tests PASS, no xfail markers                       |
| `tests/test_tax.py`               | 3 passing tests for tax savings                     | VERIFIED    | All tests PASS, no xfail markers                       |
| `tests/test_caveats.py`           | 4 passing tests for caveat generation               | VERIFIED    | All tests PASS, no xfail markers                       |
| `tests/test_engine.py`            | 5 passing integration tests for engine              | VERIFIED    | All tests PASS, no xfail markers                       |

---

### Key Link Verification

| From                            | To                              | Via                                         | Status  | Details                                                    |
|---------------------------------|---------------------------------|---------------------------------------------|---------|------------------------------------------------------------|
| `tests/conftest.py`             | `src/fathom/models.py`          | `from fathom.models import`                 | WIRED   | Line 12: `from fathom.models import FinancingOption, GlobalSettings, OptionType` |
| `tests/test_amortization.py`    | `src/fathom/amortization.py`    | `from fathom.amortization import`           | WIRED   | Lines 15, 30, 42 import and invoke `monthly_payment`; lines 57, 75 import `amortization_schedule` |
| `src/fathom/amortization.py`    | `src/fathom/models.py`          | uses `MonthlyDataPoint` for schedule output | WIRED   | Line 11: `from fathom.models import MonthlyDataPoint`      |
| `src/fathom/opportunity.py`     | `src/fathom/models.py`          | uses Decimal types and `OptionType`         | WIRED   | Lines 13-14: imports `FinancingOption, GlobalSettings, OptionType` |
| `src/fathom/engine.py`          | `src/fathom/amortization.py`    | calls `amortization_schedule`               | WIRED   | Line 11: import; invoked at lines 143, 261, 279, 291      |
| `src/fathom/engine.py`          | `src/fathom/opportunity.py`     | calls `compute_opportunity_cost`            | WIRED   | Line 23: import; invoked at lines 75, 159                 |
| `src/fathom/engine.py`          | `src/fathom/inflation.py`       | calls `compute_inflation_adjustment`        | WIRED   | Line 13: import; invoked at lines 97, 165                 |
| `src/fathom/engine.py`          | `src/fathom/tax.py`             | calls `compute_tax_savings`                 | WIRED   | Line 24: import; invoked at line 173                      |
| `src/fathom/engine.py`          | `src/fathom/caveats.py`         | calls `generate_all_caveats`                | WIRED   | Line 12: import; invoked at line 343                      |
| `src/fathom/engine.py`          | `src/fathom/models.py`          | accepts `FinancingOption`/`GlobalSettings`, returns `ComparisonResult` | WIRED | Lines 14-22: imports all required model types |
| `src/fathom/caveats.py`         | `src/fathom/opportunity.py`     | calls `compute_opportunity_cost` for sensitivity | WIRED | Line 21: import; invoked at lines 109, 118, 127, 174  |

---

### Requirements Coverage

All 17 requirement IDs claimed across plans 01-01, 01-02, and 01-03 verified against REQUIREMENTS.md:

| Requirement | Source Plan | Description                                                                  | Status    | Evidence                                                     |
|-------------|-------------|------------------------------------------------------------------------------|-----------|--------------------------------------------------------------|
| CALC-01     | 01-02       | Total payments via standard amortization                                     | SATISFIED | `amortization_schedule` computes full payment breakdown; `test_amortization_schedule` passes |
| CALC-02     | 01-02       | Opportunity cost of upfront cash at user return rate                         | SATISFIED | `compute_opportunity_cost` with pool model; `test_cash_buyer_opportunity_cost` passes |
| CALC-03     | 01-03       | Normalize all options to same comparison period (longest term)               | SATISFIED | `_determine_comparison_period` returns max term; `test_normalization_to_longest_term` passes |
| CALC-04     | 01-02       | Freed-up cash after shorter loan invested for remainder                       | SATISFIED | Phase 2 loop in `compute_opportunity_cost`; `test_freed_cash_after_payoff` passes |
| CALC-05     | 01-03       | True Total Cost formula                                                      | SATISFIED | Formula verified in engine and asserted by `test_true_total_cost` |
| CALC-06     | 01-02       | Inflation adjustment on future cash flows                                    | SATISFIED | `compute_inflation_adjustment` via `discount_cash_flows`; `test_full_term_discounting` passes |
| CALC-07     | 01-02       | Tax savings = deductible interest × marginal rate                            | SATISFIED | `compute_tax_savings`; `test_tax_savings_basic` and `test_tax_over_full_term` pass |
| CALC-08     | 01-01, 01-02| Decimal arithmetic for all monetary calculations                             | SATISFIED | All monetary fields typed as `Decimal`; no float found in src/; `test_decimal_types` passes |
| TECH-01     | 01-01       | All financial calculations server-side Python                                | SATISFIED | All calculation modules are pure Python; no JS calculation logic exists yet |
| TECH-02     | 01-01       | No user data persisted beyond request/response                               | SATISFIED | Stateless pure functions with no persistent state or I/O     |
| TECH-04     | 01-01       | Single deployable Python process, no external database                       | SATISFIED | No database dependencies; runs as single process             |
| QUAL-01     | 01-03       | `ruff check` passes with zero errors, no `# noqa`                           | SATISFIED | `uv run ruff check .` → "All checks passed!"; grep for `# noqa` returns empty |
| QUAL-02     | 01-03       | `ruff format` passes (Black-compatible)                                      | SATISFIED | `uv run ruff format --check .` → "16 files already formatted" |
| QUAL-03     | 01-03       | `ty check` passes with zero errors, no `# type: ignore`                     | SATISFIED | `uv run ty check` → "All checks passed!"; grep for `# type: ignore` returns empty |
| QUAL-04     | 01-03       | `pyrefly check` passes with zero errors                                      | SATISFIED | `uv run pyrefly check` → "0 errors"                         |
| QUAL-05     | 01-01       | All public modules, classes, and functions have docstrings                   | SATISFIED | All 7 source modules have module docstrings; all public classes and functions have docstrings; ruff D rules enforced |
| QUAL-06     | 01-03       | `prek` pre-commit hooks pass on all commits                                  | SATISFIED | `uv run prek run` → all hooks pass (ty and pyrefly confirmed clean) |

**Note on TECH-01 and TECH-02:** These are architectural properties that are fully in force for Phase 1 (pure calculation engine with no web layer yet). Phase 2 will add the web layer; these requirements remain satisfied as long as no JS calculation logic or server-side persistence is added there.

**Note on type checker scope:** Both `ty` and `pyrefly` are configured to exclude `tests/` from checking (`[tool.ty.src] exclude = ["tests/"]` and `[tool.pyrefly] project_excludes = ["tests/"]`). This is an intentional documented decision from Plan 01 — the test files use function-level imports as a guard pattern for the TDD stubs. The per-file ruff ignore for tests (`S101`, `ANN`, `TCH`) is appropriate and not suppression of real errors.

---

### Anti-Patterns Found

No blockers or warnings found.

| File | Pattern | Severity | Verdict |
|------|---------|----------|---------|
| All src/ files | Suppression comments (`# noqa`, `# type: ignore`) | — | None found |
| All src/ files | Placeholder/stub implementations | — | None found; all functions have real implementations |
| All src/ files | Empty returns (`return null`, `return {}`) | — | None found |
| `engine.py` L266-289 | Duplicate `if/else` branches for `not_paid_option` in `_build_promo_result` | Info | Both branches produce identical code — minor refactor opportunity but not a correctness issue |

---

### Human Verification Required

None. All phase 1 goals are computation/correctness assertions that are fully verifiable programmatically. The phase does not yet involve any UI, visual output, or external service integration.

---

### Test Run Summary

```
24 passed in 0.02s
```

All 24 tests passed with zero failures, zero xfail markers remaining, and zero skips. Tests cover:

- 5 amortization tests (including $304.22 check value and last-payment balance clearing)
- 4 opportunity cost tests (including pool exhaustion and freed-cash investing)
- 3 inflation tests (including $295.24 PV check value)
- 3 tax tests (basic savings, disabled, full term)
- 4 caveat tests (all three caveat types + all-options coverage)
- 5 engine integration tests (normalization, TTC formula, cash vs loan, all-cash, dual-outcome promo)

---

### Quality Gate Summary

| Tool         | Result        |
|--------------|---------------|
| ruff check   | 0 errors      |
| ruff format  | 0 changes     |
| ty check     | 0 errors      |
| pyrefly      | 0 errors      |
| prek hooks   | All passed    |

---

_Verified: 2026-03-10T18:00:00Z_
_Verifier: Claude (gsd-verifier)_
