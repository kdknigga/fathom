---
phase: 16
slug: custom-option-cleanup
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-15
---

# Phase 16 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing) |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/test_forms.py tests/test_routes.py -x -q` |
| **Full suite command** | `uv run pytest -x -q` |
| **Estimated runtime** | ~5 seconds |

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
| 16-01-01 | 01 | 1 | CUST-01 | unit | `uv run pytest tests/test_forms.py -x -k "custom_label"` | ❌ W0 | ⬜ pending |
| 16-01-02 | 01 | 1 | CUST-01 | unit | `uv run pytest tests/test_forms.py -x -k "disambigu"` | ❌ W0 | ⬜ pending |
| 16-01-03 | 01 | 1 | CUST-01 | unit | `uv run pytest tests/test_forms.py -x -k "fallback"` | ❌ W0 | ⬜ pending |
| 16-01-04 | 01 | 1 | CUST-02 | integration | `uv run pytest tests/test_routes.py -x -k "down_payment_optional"` | ❌ W0 | ⬜ pending |
| 16-01-05 | 01 | 1 | TEST-05 | integration | `uv run pytest tests/test_routes.py -x -k "custom_label_in_results"` | ❌ W0 | ⬜ pending |
| 16-01-06 | 01 | 1 | CUST-01 | integration | `uv run pytest tests/test_routes.py -x -k "custom_label"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_forms.py` — new tests for custom_label -> label flow, disambiguation, fallback
- [ ] `tests/test_routes.py` — new tests for custom label in rendered HTML, down payment optional indicator

*Existing infrastructure covers framework needs — pytest already configured.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
