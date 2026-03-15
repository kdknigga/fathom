---
phase: 14-engine-corrections
verified: 2026-03-15T15:00:00Z
status: passed
score: 7/7 must-haves verified
re_verification: false
---

# Phase 14: Engine Corrections Verification Report

**Phase Goal:** Users comparing promo financing options see materially different costs for deferred-interest vs forward-only scenarios, and the line chart accurately plots cumulative true cost
**Verified:** 2026-03-15
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Deferred-interest (retroactive) promo not-paid cost exceeds forward-only not-paid cost | VERIFIED | `test_deferred_interest_higher_than_forward_only` passes; `_build_promo_result` adds `principal * post_apr * term/12` to post_promo_balance only when `deferred_interest and retroactive_interest` |
| 2 | Forward-only not-paid cost exceeds paid-on-time cost | VERIFIED | `test_forward_only_higher_than_paid_on_time` passes; post_promo_balance includes remaining principal amortized at 24.99% APR, while paid-on-time uses 0% |
| 3 | Worked numeric example ($10K, 24.99% APR, 12-month promo) produces specific expected invariants | VERIFIED | `test_promo_worked_example_exact_values` passes; asserts required_monthly, retroactive_interest == $2499.00, and full retroactive > forward > paid_on_time ordering |
| 4 | Not-paid-on-time monthly_data covers months 1 through 2*promo_term (24 months) | VERIFIED | `test_promo_not_paid_monthly_data_covers_full_timeline` passes; engine builds Phase 1 (months 1-12) + Phase 2 post-promo schedule (months 13-24) |
| 5 | MonthlyDataPoint.cumulative_cost tracks cumulative true cost (payment + opportunity_cost - tax_savings + inflation_adjustment) | VERIFIED | `test_cumulative_cost_is_true_cost`, `test_cash_cumulative_cost_is_true_cost`, `test_promo_cumulative_cost_is_true_cost` all pass; formula applied in `_build_cash_result`, `_build_loan_result`, and `_build_not_paid_result` |
| 6 | Line chart plots cumulative true cost with title "Cumulative True Cost Over Time" | VERIFIED | `test_line_chart_title` passes; `prepare_line_chart` returns `{"title": "Cumulative True Cost Over Time", ...}`; `_collect_option_points` uses `dp.cumulative_cost` directly |
| 7 | Promo options show both paid-on-time (solid) and not-paid-on-time (dashed) lines | VERIFIED | `test_line_chart_promo_dual_lines`, `test_line_chart_not_paid_is_dashed`, `test_line_chart_not_paid_same_color_as_paid` all pass; routes.py inserts not-paid entries into chart_sorted; charts.py uses NOT_PAID_SUFFIX detection and NOT_PAID_DASH = "6,4" |

**Score:** 7/7 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/fathom/engine.py` | Rewritten `_build_promo_result` with two-phase schedule | VERIFIED | Contains `_build_promo_result`, `_build_promo_phases`, `_build_not_paid_result`, `_PromoContext` dataclass; worked numeric example comment at lines 578-599 |
| `tests/test_engine.py` | Promo penalty tests with exact dollar amounts | VERIFIED | Contains `test_deferred_interest_higher_than_forward_only`, `test_forward_only_higher_than_paid_on_time`, `test_promo_worked_example_exact_values`, `test_promo_not_paid_monthly_data_covers_full_timeline`, `test_promo_minimum_payments_during_promo`, `test_promo_retroactive_interest_lump_at_boundary`, `test_cumulative_cost_is_true_cost`, `test_cash_cumulative_cost_is_true_cost`, `test_promo_cumulative_cost_is_true_cost`, `test_cumulative_cost_matches_results_module` |
| `tests/conftest.py` | Forward-only and retroactive promo fixtures | VERIFIED | Contains `promo_forward_only` (deferred_interest=False, retroactive_interest=False) and `promo_retroactive` (deferred_interest=True, retroactive_interest=True) |
| `src/fathom/charts.py` | Dual line rendering for promo options | VERIFIED | Contains `NOT_PAID_SUFFIX = " (not paid on time)"`, `NOT_PAID_DASH = "6,4"`, not-paid detection in `_collect_option_points` and `_build_line_dataset`, title in `prepare_line_chart` |
| `tests/test_charts.py` | Chart data point validation | VERIFIED | Contains `test_line_chart_uses_true_cost`, `test_line_chart_promo_dual_lines`, `test_line_chart_not_paid_is_dashed`, `test_line_chart_not_paid_same_color_as_paid`, `test_line_chart_title` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/fathom/engine.py` | `fathom.amortization.amortization_schedule` | Post-promo amortization reuse | WIRED | `amortization_schedule(ctx.post_promo_balance, ctx.post_apr, ctx.term)` called at line 352 inside `_build_promo_phases` |
| `src/fathom/engine.py` | `fathom.money.quantize_money` | All monetary rounding | WIRED | `from fathom.money import quantize_money` at line 24; called throughout `_build_promo_result`, `_build_promo_phases`, `_build_not_paid_result`, `_build_cash_result`, `_build_loan_result` |
| `tests/test_engine.py` | `src/fathom/engine.py` | `compare()` invocation with promo options | WIRED | Multiple tests call `compare([promo_retroactive], settings)` and `compare([promo_forward_only], settings)` |
| `src/fathom/engine.py` | `src/fathom/results.py` | Same true cost formula | WIRED | `net = dp.payment + opp - tax_per_period[i] + infl_per_period[i]` in `_build_not_paid_result`; `test_cumulative_cost_matches_results_module` cross-validates against `_monthly_data_to_rows` |
| `src/fathom/charts.py` | `src/fathom/models.py` | PromoResult detection for dual lines | WIRED | `isinstance(result, PromoResult)` at lines 147 and 185 |
| `src/fathom/routes.py` | `src/fathom/charts.py` | sorted_options includes not-paid entries | WIRED | Routes builds `chart_sorted` with `f"{opt['name']} (not paid on time)"` entries for promo options; passed to `prepare_charts()` |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| ENG-01 | 14-01-PLAN.md | Promo penalty modeling produces distinct costs for deferred-interest (retroactive) vs forward-only interest scenarios | SATISFIED | `_build_promo_result` branches on `option.deferred_interest and option.retroactive_interest`; retroactive adds $2,499 to post-promo balance; all three tests confirming the ordering pass |
| ENG-02 | 14-02-PLAN.md | Line chart plots cumulative true cost (payments + opp cost - tax + inflation) per period, not cumulative payments | SATISFIED | `_collect_option_points` reads `dp.cumulative_cost`; all three engine builders compute cumulative_cost as running true cost sum; cross-validation test passes |
| TEST-01 | 14-01-PLAN.md | Tests prove deferred-interest flags materially change `not_paid_on_time` results | SATISFIED | 6 new tests in test_engine.py; all pass with exact Decimal assertions |
| TEST-02 | 14-02-PLAN.md | Tests assert line chart data points match cumulative true cost metric | SATISFIED | 5 new tests in test_charts.py; `test_line_chart_uses_true_cost` verifies chart points match `cumulative_cost`; all pass |

No orphaned requirements: REQUIREMENTS.md traceability table maps ENG-01, ENG-02, TEST-01, TEST-02 exclusively to Phase 14. No other Phase 14 requirements exist.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | — | — | — | — |

No TODO/FIXME/placeholder comments found. No stub implementations. No return null/empty patterns. No console.log-only handlers.

### Human Verification Required

None. All behavioral assertions are covered by automated tests.

The CLAUDE.md requires Playwright for browser-based visual verification, but there are no new UI components introduced in this phase — only engine calculation logic and chart data preparation. The chart data shape is verified by test_charts.py tests that assert path format, titles, dual lines, dash patterns, and color sharing. No new HTML templates or CSS were added.

### Gaps Summary

No gaps. All seven observable truths verified, all five artifacts substantive and wired, all six key links confirmed, all four requirements satisfied with direct implementation evidence. Full test suite (298 tests) passes. All quality gates pass clean: ruff lint, ruff format, ty, pyrefly.

---

_Verified: 2026-03-15T15:00:00Z_
_Verifier: Claude (gsd-verifier)_
