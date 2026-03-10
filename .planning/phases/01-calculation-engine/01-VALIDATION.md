---
phase: 1
slug: calculation-engine
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-10
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=8.0 |
| **Config file** | none — Wave 0 adds `[tool.pytest.ini_options]` to pyproject.toml |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

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
| 01-01-01 | 01 | 0 | CALC-01, CALC-08 | unit | `uv run pytest tests/test_amortization.py -x` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 0 | CALC-02, CALC-04 | unit | `uv run pytest tests/test_opportunity.py -x` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 0 | CALC-06 | unit | `uv run pytest tests/test_inflation.py -x` | ❌ W0 | ⬜ pending |
| 01-01-04 | 01 | 0 | CALC-07 | unit | `uv run pytest tests/test_tax.py -x` | ❌ W0 | ⬜ pending |
| 01-01-05 | 01 | 0 | CALC-03, CALC-05 | integration | `uv run pytest tests/test_engine.py -x` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | CALC-01 | unit | `uv run pytest tests/test_amortization.py -x` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | CALC-02 | unit | `uv run pytest tests/test_opportunity.py -x` | ❌ W0 | ⬜ pending |
| 01-02-03 | 02 | 1 | CALC-05 | integration | `uv run pytest tests/test_engine.py -x` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 2 | QUAL-01 | lint | `uv run ruff check .` | ✅ | ⬜ pending |
| 01-03-02 | 03 | 2 | QUAL-02 | format | `uv run ruff format --check .` | ✅ | ⬜ pending |
| 01-03-03 | 03 | 2 | QUAL-03 | type | `uv run ty check` | ✅ | ⬜ pending |
| 01-03-04 | 03 | 2 | QUAL-04 | type | `uv run pyrefly check` | ✅ | ⬜ pending |
| 01-03-05 | 03 | 2 | QUAL-06 | hooks | `uv run prek run` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `uv add --dev pytest` — add pytest as dev dependency
- [ ] `pyproject.toml` — add `[tool.pytest.ini_options]` section with `testpaths = ["tests"]`
- [ ] `tests/__init__.py` — package init
- [ ] `tests/conftest.py` — shared fixtures (standard test options, global settings)
- [ ] `tests/test_amortization.py` — stubs for CALC-01, CALC-08
- [ ] `tests/test_opportunity.py` — stubs for CALC-02, CALC-04
- [ ] `tests/test_inflation.py` — stubs for CALC-06
- [ ] `tests/test_tax.py` — stubs for CALC-07
- [ ] `tests/test_caveats.py` — stubs for caveat generation
- [ ] `tests/test_engine.py` — stubs for CALC-03, CALC-05 (integration)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| No client-side JS calculations | TECH-01 | Architectural — no JS exists in this phase | Verify no .js files in src/ |
| No persistent storage | TECH-02 | Architectural — no database code exists | Verify no file/DB I/O in src/ |
| Single process, no external DB | TECH-04 | Architectural — no dependencies require DB | Verify `dependencies = []` or no DB packages |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
