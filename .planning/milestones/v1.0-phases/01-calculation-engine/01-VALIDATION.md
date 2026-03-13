---
phase: 1
slug: calculation-engine
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-10
audited: 2026-03-13
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=8.0 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest tests/ -v` |
| **Actual runtime** | 0.03s (24 tests) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q && uv run ruff check . && uv run ruff format --check . && uv run ty check && uv run pyrefly check`
- **After every plan wave:** Run `uv run pytest tests/ -v && uv run prek run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 0 | CALC-01, CALC-08 | unit | `uv run pytest tests/test_amortization.py -x` | ✅ | ✅ green |
| 01-01-02 | 01 | 0 | CALC-02, CALC-04 | unit | `uv run pytest tests/test_opportunity.py -x` | ✅ | ✅ green |
| 01-01-03 | 01 | 0 | CALC-06 | unit | `uv run pytest tests/test_inflation.py -x` | ✅ | ✅ green |
| 01-01-04 | 01 | 0 | CALC-07 | unit | `uv run pytest tests/test_tax.py -x` | ✅ | ✅ green |
| 01-01-05 | 01 | 0 | CALC-03, CALC-05 | integration | `uv run pytest tests/test_engine.py -x` | ✅ | ✅ green |
| 01-02-01 | 02 | 1 | CALC-01 | unit | `uv run pytest tests/test_amortization.py -x` | ✅ | ✅ green |
| 01-02-02 | 02 | 1 | CALC-02 | unit | `uv run pytest tests/test_opportunity.py -x` | ✅ | ✅ green |
| 01-02-03 | 02 | 1 | CALC-05 | integration | `uv run pytest tests/test_engine.py -x` | ✅ | ✅ green |
| 01-03-01 | 03 | 2 | QUAL-01 | lint | `uv run ruff check .` | ✅ | ✅ green |
| 01-03-02 | 03 | 2 | QUAL-02 | format | `uv run ruff format --check .` | ✅ | ✅ green |
| 01-03-03 | 03 | 2 | QUAL-03 | type | `uv run ty check` | ✅ | ✅ green |
| 01-03-04 | 03 | 2 | QUAL-04 | type | `uv run pyrefly check` | ✅ | ✅ green |
| 01-03-05 | 03 | 2 | QUAL-06 | hooks | `uv run prek run` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `uv add --dev pytest` — add pytest as dev dependency
- [x] `pyproject.toml` — add `[tool.pytest.ini_options]` section with `testpaths = ["tests"]`
- [x] `tests/__init__.py` — package init
- [x] `tests/conftest.py` — shared fixtures (standard test options, global settings)
- [x] `tests/test_amortization.py` — 5 tests for CALC-01, CALC-08
- [x] `tests/test_opportunity.py` — 4 tests for CALC-02, CALC-04
- [x] `tests/test_inflation.py` — 3 tests for CALC-06
- [x] `tests/test_tax.py` — 3 tests for CALC-07
- [x] `tests/test_caveats.py` — 4 tests for caveat generation
- [x] `tests/test_engine.py` — 5 integration tests for CALC-03, CALC-05

---

## Requirement → Test Coverage

| Requirement | Description | Test File | Tests | Status |
|-------------|-------------|-----------|-------|--------|
| CALC-01 | Standard amortization | test_amortization.py | `test_standard_amortization`, `test_amortization_schedule`, `test_last_payment_adjustment` | COVERED |
| CALC-02 | Opportunity cost of upfront cash | test_opportunity.py | `test_cash_buyer_opportunity_cost`, `test_loan_buyer_decreasing_pool` | COVERED |
| CALC-03 | Normalize to longest term | test_engine.py | `test_normalization_to_longest_term` | COVERED |
| CALC-04 | Freed-up cash invested | test_opportunity.py | `test_freed_cash_after_payoff` | COVERED |
| CALC-05 | True Total Cost formula | test_engine.py | `test_true_total_cost` | COVERED |
| CALC-06 | Inflation adjustment | test_inflation.py | `test_present_value_discounting`, `test_zero_inflation`, `test_full_term_discounting` | COVERED |
| CALC-07 | Tax savings | test_tax.py | `test_tax_savings_basic`, `test_tax_disabled`, `test_tax_over_full_term` | COVERED |
| CALC-08 | Decimal arithmetic | test_amortization.py | `test_decimal_types` | COVERED |
| QUAL-01 | ruff check clean | toolchain | `uv run ruff check .` | COVERED |
| QUAL-02 | ruff format clean | toolchain | `uv run ruff format --check .` | COVERED |
| QUAL-03 | ty check clean | toolchain | `uv run ty check` | COVERED |
| QUAL-04 | pyrefly check clean | toolchain | `uv run pyrefly check` | COVERED |
| QUAL-05 | Docstrings on all public APIs | toolchain | Enforced by ruff D rules | COVERED |
| QUAL-06 | prek hooks pass | toolchain | `uv run prek run` | COVERED |

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| No client-side JS calculations | TECH-01 | Architectural — no JS exists in this phase | Verify no .js files in src/ |
| No persistent storage | TECH-02 | Architectural — no database code exists | Verify no file/DB I/O in src/ |
| Single process, no external DB | TECH-04 | Architectural — no dependencies require DB | Verify `dependencies = []` or no DB packages |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved

---

## Validation Audit 2026-03-13

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

All 14 automatable requirements have passing tests or toolchain checks. 3 architectural requirements appropriately classified as manual-only. 24 pytest tests pass in 0.03s. All 5 quality gates green.

---

_Audited: 2026-03-13_
_Auditor: Claude (gsd-validate-phase)_
