---
phase: 3
slug: results-display-and-charts
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-10
validated: 2026-03-13
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
| **Estimated runtime** | ~0.5 seconds |

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
| 03-01-01 | 01 | 1 | RSLT-01 | integration | `uv run pytest tests/test_results_display.py::TestRecommendationCard::test_recommendation_card_shows_winner -x` | ✅ | ✅ green |
| 03-01-02 | 01 | 1 | RSLT-02 | integration | `uv run pytest tests/test_results_display.py::TestRecommendationCard::test_savings_displayed -x` | ✅ | ✅ green |
| 03-01-03 | 01 | 1 | RSLT-03 | integration | `uv run pytest tests/test_results_display.py::TestCaveats::test_caveats_on_hero -x` | ✅ | ✅ green |
| 03-01-04 | 01 | 1 | RSLT-04 | integration | `uv run pytest tests/test_results_display.py::TestBreakdownTable::test_breakdown_table_present -x` | ✅ | ✅ green |
| 03-02-01 | 02 | 1 | RSLT-05 | integration | `uv run pytest tests/test_results_display.py::TestChartSvg::test_bar_chart_svg -x` | ✅ | ✅ green |
| 03-02-02 | 02 | 1 | RSLT-06 | integration | `uv run pytest tests/test_results_display.py::TestChartSvg::test_line_chart_svg -x` | ✅ | ✅ green |
| 03-02-03 | 02 | 1 | A11Y-02 | integration | `uv run pytest tests/test_results_display.py::TestChartSvg::test_chart_accessibility -x` | ✅ | ✅ green |
| 03-02-04 | 02 | 1 | A11Y-03 | integration | `uv run pytest tests/test_results_display.py::TestChartSvg::test_chart_patterns -x` | ✅ | ✅ green |
| 03-03-01 | 03 | 2 | RSLT-07 | integration | `uv run pytest tests/test_results_display.py::TestHtmxPartial::test_htmx_partial -x` | ✅ | ✅ green |
| 03-03-02 | 03 | 2 | RSLT-08 | integration | `uv run pytest tests/test_results_display.py::TestHtmxPartial::test_calculate_button_fallback -x` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Additional Test Coverage

| File | Tests | Coverage |
|------|-------|----------|
| `tests/test_results_helpers.py` | 8 unit tests | Winner detection, savings calculation, breakdown rows, options data, recommendation text |
| `tests/test_charts.py` | 13 unit tests | Bar chart (count, winner, heights, patterns, coordinates, labels), line chart (count, paths, dash patterns, cash flat lines, year boundaries, endpoints) |
| `tests/test_results_display.py` | 14 integration tests | Recommendation card, savings, caveats, breakdown table, HTMX partial/full-page/fallback/error, chart SVG, accessibility |
| `tests/playwright_verify.py` | 21 browser checks | HTMX swap, hero card, charts, accessibility, responsive layout |

**Total: 35 pytest tests + 21 Playwright checks = 56 automated verifications**

---

## Wave 0 Requirements

- [x] `tests/test_results_display.py` — 14 integration tests for RSLT-01 through RSLT-08, A11Y-02, A11Y-03
- [x] `tests/test_charts.py` — 13 unit tests for SVG chart coordinate computation
- [x] `tests/test_results_helpers.py` — 8 unit tests for winner detection, savings calculation, recommendation text

*Existing test infrastructure (conftest.py, pytest config) covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|

*All phase behaviors have automated verification (Playwright MCP handles browser-based checks).*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s (0.45s actual)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** complete

---

## Validation Audit 2026-03-13

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

All 10 requirements (RSLT-01 through RSLT-08, A11Y-02, A11Y-03) have automated test coverage.
35 pytest tests all passing green. No gaps to fill.
