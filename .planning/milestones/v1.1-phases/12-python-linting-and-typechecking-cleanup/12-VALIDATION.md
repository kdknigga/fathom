---
phase: 12
slug: python-linting-and-typechecking-cleanup
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-14
validated: 2026-03-14
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=9.0.2 |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run ruff check . && uv run pytest -x` |
| **Full suite command** | `uv run ruff check . && uv run ruff format --check . && uv run ty check && uv run pyrefly check && uv run pytest` |
| **Estimated runtime** | ~3 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run ruff check . && uv run pytest -x`
- **After every plan wave:** Run `uv run ruff check . && uv run ruff format --check . && uv run ty check && uv run pyrefly check && uv run pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 3 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 12-01-01 | 01 | 1 | LINT-01 | lint | `uv run ruff check .` | N/A (tool) | ✅ green |
| 12-01-02 | 01 | 1 | LINT-02 | regression | `uv run pytest -x` | ✅ (283 tests) | ✅ green |
| 12-01-03 | 01 | 1 | LINT-02 | typecheck | `uv run ty check` | N/A (tool) | ✅ green |
| 12-01-04 | 01 | 1 | LINT-02 | typecheck | `uv run pyrefly check` | N/A (tool) | ✅ green |
| 12-01-05 | 01 | 1 | LINT-03 | policy | `grep -r "# noqa\|# type: ignore" src/ tests/` | N/A (grep) | ✅ green |
| 12-02-01 | 02 | 2 | LINT-04 | lint | `uv run ruff check .` | N/A (tool) | ✅ green |
| 12-02-02 | 02 | 2 | LINT-04 | format | `uv run ruff format --check .` | N/A (tool) | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No new test files needed; this phase modifies configuration and refactors existing code.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved

---

## Validation Audit 2026-03-14

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

All 7 verification checks pass green. Phase requirements LINT-01 through LINT-04 fully covered by tool-based automated verification (ruff, pytest, ty, pyrefly, grep).
