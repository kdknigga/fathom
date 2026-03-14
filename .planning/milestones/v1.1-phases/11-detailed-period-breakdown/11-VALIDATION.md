---
phase: 11
slug: detailed-period-breakdown
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-14
validated: 2026-03-14
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2+ |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green + Playwright browser verification
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | DETAIL-01 | unit | `uv run pytest tests/test_models.py tests/test_engine.py -x` | ✅ | ✅ green |
| 11-01-02 | 01 | 1 | DETAIL-01 | unit | `uv run pytest tests/test_engine.py -x -k "per_period"` | ✅ | ✅ green |
| 11-02-01 | 02 | 1 | DETAIL-02 | integration | `uv run pytest tests/test_routes.py::TestDetailTab -x` | ✅ | ✅ green |
| 11-02-02 | 02 | 1 | DETAIL-03 | unit | `uv run pytest tests/test_results_helpers.py::TestBuildCompareData -x` | ✅ | ✅ green |
| 11-02-03 | 02 | 1 | DETAIL-04 | unit + integration | `uv run pytest tests/test_results_helpers.py::TestBuildDetailedBreakdown tests/test_results_helpers.py::TestAggregateAnnual -x` | ✅ | ✅ green |
| 11-02-04 | 02 | 1 | DETAIL-05 | e2e | Playwright: `tests/playwright_verify.py::verify_detailed_breakdown` (35 checks) | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_models.py` — MonthlyDataPoint extended fields (opportunity_cost, inflation_adjustment, tax_savings)
- [x] `tests/test_engine.py` — 8 tests for per-period cost factor computation and sum-to-aggregate consistency
- [x] `tests/test_results_helpers.py` — 7 tests for build_detailed_breakdown, aggregate_annual, build_compare_data
- [x] `tests/test_routes.py::TestDetailTab` — 4 integration tests for detail tab HTMX endpoints
- [x] `tests/playwright_verify.py::verify_detailed_breakdown` — 35 browser checks for tabs, column toggles, keyboard nav, ARIA

*All tests created during execution via TDD (plans 01-02) and Playwright verification (plan 03).*

---

## Manual-Only Verifications

*All phase behaviors have automated verification — Playwright handles browser-based checks.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** complete

---

## Validation Audit 2026-03-14

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
