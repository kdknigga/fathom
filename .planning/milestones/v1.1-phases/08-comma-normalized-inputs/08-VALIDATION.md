---
phase: 08
slug: comma-normalized-inputs
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-13
audited: 2026-03-14
---

# Phase 08 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + Playwright (custom runner) |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] |
| **Quick run command** | `uv run pytest tests/test_forms.py -x` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~2 seconds (unit), ~10 seconds (e2e) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_forms.py -x`
- **After every plan wave:** Run `uv run pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | INPUT-01, INPUT-03 | unit | `uv run pytest tests/test_forms.py -x -k "comma or dollar or try_decimal"` | ✅ | ✅ green |
| 08-01-02 | 01 | 1 | INPUT-02 | unit | `uv run pytest tests/test_routes.py -x -k "comma"` | ✅ | ✅ green |
| 08-02-01 | 02 | 2 | INPUT-02 | e2e | `uv run python tests/playwright_verify.py` | ✅ | ✅ green |
| 08-02-02 | 02 | 2 | INPUT-01 | e2e | `uv run python tests/playwright_verify.py` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_forms.py` — 16 test cases for comma/dollar stripping in `_try_decimal`, `_to_money`, `comma_format`, and `purchase_price` validator
- [x] `tests/test_routes.py` — 3 test cases for comma-formatted values in rendered HTML
- [x] `tests/playwright_verify.py` — 7 Playwright checks for blur/focus/paste/server-render/HTMX-swap/full-calc behavior

*All Wave 0 tests implemented and passing.*

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

## Validation Audit 2026-03-14

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

All 4 tasks have automated verification covering all 3 requirements (INPUT-01, INPUT-02, INPUT-03).
Unit tests: 16 comma + 3 route tests passing. E2e: 7 Playwright checks passing. Full suite: 241 tests green.
