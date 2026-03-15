---
phase: 14
slug: engine-corrections
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-15
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (configured in pyproject.toml) |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/test_engine.py tests/test_charts.py -x` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_engine.py tests/test_charts.py -x`
- **After every plan wave:** Run `uv run pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 14-01-01 | 01 | 0 | ENG-01, TEST-01 | unit | `uv run pytest tests/test_engine.py::test_deferred_interest_higher_than_forward_only -x` | ❌ W0 | ⬜ pending |
| 14-01-02 | 01 | 0 | ENG-01 | unit | `uv run pytest tests/test_engine.py::test_forward_only_higher_than_paid_on_time -x` | ❌ W0 | ⬜ pending |
| 14-01-03 | 01 | 0 | ENG-01 | unit | `uv run pytest tests/test_engine.py::test_promo_worked_example_exact_values -x` | ❌ W0 | ⬜ pending |
| 14-01-04 | 01 | 0 | ENG-02 | unit | `uv run pytest tests/test_engine.py::test_cumulative_cost_is_true_cost -x` | ❌ W0 | ⬜ pending |
| 14-01-05 | 01 | 0 | TEST-02 | unit | `uv run pytest tests/test_charts.py::test_line_chart_uses_true_cost -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_engine.py` — new test functions for promo penalty invariants and worked example (ENG-01, TEST-01)
- [ ] `tests/test_charts.py` — new test functions for cumulative true cost in chart data (ENG-02, TEST-02)
- [ ] `tests/conftest.py` — fixture for forward-only promo option (deferred_interest=False)

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
