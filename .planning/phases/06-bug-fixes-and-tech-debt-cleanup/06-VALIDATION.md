---
phase: 6
slug: bug-fixes-and-tech-debt-cleanup
status: draft
nyquist_compliant: false
wave_0_complete: false
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
| 06-01-01 | 01 | 1 | FORM-05 | unit | `uv run pytest tests/test_forms.py -x -k "option_count"` | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 1 | (gap) retroactive_interest | unit | `uv run pytest tests/test_forms.py -x -k "retroactive"` | ❌ W0 | ⬜ pending |
| 06-01-03 | 01 | 1 | (gap) return_preset | unit | `uv run pytest tests/test_routes.py -x -k "return_preset"` | ❌ W0 | ⬜ pending |
| 06-02-01 | 02 | 2 | (gap) data_table_values | browser | `uv run python tests/playwright_verify.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_forms.py` — add tests for option count validation (2-4 enforcement)
- [ ] `tests/test_forms.py` — add tests for retroactive_interest field parsing and cross-field validation
- [ ] `tests/test_routes.py` — add test for return_preset format with 0.10 rate
- [ ] `tests/playwright_verify.py` — add cell value assertion checks for data table accuracy

*Existing infrastructure covers test framework and fixtures.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
