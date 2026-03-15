---
phase: 13
slug: centralize-monetary-rounding
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-15
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest tests/` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 13-01-01 | 01 | 1 | ENG-03 | existing regression | `uv run pytest tests/ -x -q` | ✅ | ✅ green |
| 13-01-02 | 01 | 1 | ENG-03 | grep verification | `grep -rn "def quantize_money" src/fathom/` | ✅ | ✅ green |
| 13-01-03 | 01 | 1 | ENG-03 | quality gates | `uv run ruff check . && uv run ruff format --check . && uv run ty check && uv run pyrefly check` | ✅ | ✅ green |
| 13-01-04 | 01 | 1 | ENG-03 | unit: quantize_money edge cases + CENTS | `uv run pytest tests/test_money.py -v` | ✅ | ✅ green |
| 13-01-05 | 01 | 1 | ENG-03 | unit: import centralization assertion | `uv run pytest tests/test_money.py -v` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

New dedicated test file added: `tests/test_money.py` (11 tests).
- 8 unit tests for `quantize_money()` edge cases and `CENTS` constant
- 3 structural integrity tests verifying no consumer module defines its own copy

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** 2026-03-15 — gaps filled by gsd-nyquist-auditor (335 tests passing, all quality gates clean)

---

## Validation Audit 2026-03-15

| Metric | Count |
|--------|-------|
| Gaps found | 2 |
| Resolved | 2 |
| Escalated | 0 |
