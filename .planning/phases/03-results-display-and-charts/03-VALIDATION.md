---
phase: 3
slug: results-display-and-charts
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-10
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (already configured) |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | RSLT-01 | integration | `uv run pytest tests/test_results_display.py::test_recommendation_card_shows_winner -x` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | RSLT-02 | integration | `uv run pytest tests/test_results_display.py::test_savings_displayed -x` | ❌ W0 | ⬜ pending |
| 03-01-03 | 01 | 1 | RSLT-03 | integration | `uv run pytest tests/test_results_display.py::test_caveats_on_hero -x` | ❌ W0 | ⬜ pending |
| 03-01-04 | 01 | 1 | RSLT-04 | integration | `uv run pytest tests/test_results_display.py::test_breakdown_table -x` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 1 | RSLT-05 | integration | `uv run pytest tests/test_results_display.py::test_bar_chart_svg -x` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 1 | RSLT-06 | integration | `uv run pytest tests/test_results_display.py::test_line_chart_svg -x` | ❌ W0 | ⬜ pending |
| 03-02-03 | 02 | 1 | A11Y-02 | integration | `uv run pytest tests/test_results_display.py::test_chart_accessibility -x` | ❌ W0 | ⬜ pending |
| 03-02-04 | 02 | 1 | A11Y-03 | integration | `uv run pytest tests/test_results_display.py::test_chart_patterns -x` | ❌ W0 | ⬜ pending |
| 03-03-01 | 03 | 2 | RSLT-07 | integration | `uv run pytest tests/test_results_display.py::test_htmx_partial -x` | ❌ W0 | ⬜ pending |
| 03-03-02 | 03 | 2 | RSLT-08 | integration | `uv run pytest tests/test_results_display.py::test_calculate_button_fallback -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_results_display.py` — integration test stubs for RSLT-01 through RSLT-08, A11Y-02, A11Y-03
- [ ] `tests/test_charts.py` — unit tests for SVG chart coordinate computation
- [ ] `tests/test_results_helpers.py` — unit tests for winner detection, savings calculation, recommendation text

*Existing test infrastructure (conftest.py, pytest config) covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|

*All phase behaviors have automated verification (Playwright MCP handles browser-based checks).*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
