---
phase: 9
slug: tooltips-and-tax-guidance
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-13
validated: 2026-03-14
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (Flask test client for DOM assertions) |
| **Config file** | `pyproject.toml` (pytest section) |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | TIPS-01 | integration | `uv run pytest tests/test_tooltips.py -x -q` | ✅ | ✅ green |
| 09-01-02 | 01 | 1 | TIPS-02 | integration | `uv run pytest tests/test_tooltips.py -x -q` | ✅ | ✅ green |
| 09-01-03 | 01 | 1 | TIPS-03 | integration | `uv run pytest tests/test_tooltips.py -x -q` | ✅ | ✅ green |
| 09-02-01 | 02 | 1 | TAX-01 | unit + integration | `uv run pytest tests/test_tax_brackets.py -x -q` | ✅ | ✅ green |
| 09-02-02 | 02 | 1 | TAX-02 | unit | `uv run pytest tests/test_tax_brackets.py -x -q` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_tax_brackets.py` — verify bracket data constant has correct 2025 IRS values, all 7 rates, correct income ranges
- [x] `tests/test_tax_brackets.py` — verify `tax_brackets` in template context for index route, comma-formatted rendering
- [x] `tests/test_tooltips.py` — verify .tip buttons on form labels with popovertarget and matching popover divs (TIPS-01)
- [x] `tests/test_tooltips.py` — verify .tip buttons on breakdown rows and recommendation card (TIPS-02)
- [x] `tests/test_tooltips.py` — verify keyboard accessibility: focusable buttons, tabindex on bracket rows, Enter handler, popover Escape (TIPS-03)

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

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
| Gaps found | 5 |
| Resolved | 5 |
| Escalated | 0 |
