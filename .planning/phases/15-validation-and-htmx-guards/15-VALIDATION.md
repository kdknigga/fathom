---
phase: 15
slug: validation-and-htmx-guards
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-15
---

# Phase 15 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (installed) |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/test_forms.py tests/test_routes.py -x -q` |
| **Full suite command** | `uv run pytest -x -q` |
| **Estimated runtime** | ~1 second |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_forms.py tests/test_routes.py -x -q`
- **After every plan wave:** Run `uv run pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 15-01-01 | 01 | 1 | VAL-01 | unit | `uv run pytest tests/test_forms.py -x -k "inflation"` | ✅ | ✅ green |
| 15-01-02 | 01 | 1 | VAL-02 | unit | `uv run pytest tests/test_forms.py -x -k "tax_rate"` | ✅ | ✅ green |
| 15-01-03 | 01 | 1 | VAL-03, TEST-03 | integration | `uv run pytest tests/test_routes.py -x -k "add"` | ✅ | ✅ green |
| 15-01-04 | 01 | 1 | VAL-04, TEST-03 | integration | `uv run pytest tests/test_routes.py -x -k "remove"` | ✅ | ✅ green |
| 15-01-05 | 01 | 1 | TEST-04 | unit | `uv run pytest tests/test_forms.py -x -k "bounds"` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_forms.py::TestInflationRateValidation` — 6 tests for VAL-01 (bounds, non-numeric, toggle bypass)
- [x] `tests/test_forms.py::TestTaxRateValidation` — 7 tests for VAL-02 (bounds, non-numeric, toggle bypass)
- [x] `tests/test_routes.py::TestAddOptionGuard` — 2 tests for VAL-03, TEST-03 (add at 4 returns unchanged)
- [x] `tests/test_routes.py::TestRemoveOptionGuard` — 2 tests for VAL-04, TEST-03 (remove at 2 returns unchanged)

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** complete

---

## Validation Audit 2026-03-15

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
