---
phase: 6
slug: bug-fixes-and-tech-debt-cleanup
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-13
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (latest via uv) |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/test_forms.py tests/test_routes.py -x` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_forms.py tests/test_routes.py -x`
- **After every plan wave:** Run `uv run pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | FORM-05 | unit | `uv run pytest tests/test_forms.py -x -k "option"` | ✅ | ✅ green |
| 06-01-02 | 01 | 1 | (gap) retroactive_interest | unit | `uv run pytest tests/test_forms.py -x -k "retroactive"` | ✅ | ✅ green |
| 06-01-03 | 01 | 1 | (gap) return_preset | unit | `uv run pytest tests/test_routes.py -x -k "return_preset"` | ✅ | ✅ green |
| 06-02-01 | 02 | 2 | (gap) data_table_values | browser | `uv run python tests/playwright_verify.py` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_forms.py` — tests for option count validation (2-4 enforcement) — `TestOptionCountValidation` (4 tests)
- [x] `tests/test_forms.py` — tests for retroactive_interest field parsing and cross-field validation — `TestRetroactiveInterestValidation` (3 tests) + `TestBuildDomainObjects` (2 tests)
- [x] `tests/test_routes.py` — test for return_preset format with 0.10 rate — `TestReturnPresetFormat` (1 test)
- [x] `tests/playwright_verify.py` — cell value assertion checks for data table accuracy — Checks 5 & 6 (30+ assertions)

*All Wave 0 tests implemented during phase execution.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s (pytest: 1.26s, Playwright: ~15s)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** complete

## Validation Audit 2026-03-13

| Metric | Count |
|--------|-------|
| Gaps found | 4 |
| Resolved | 4 |
| Escalated | 0 |
