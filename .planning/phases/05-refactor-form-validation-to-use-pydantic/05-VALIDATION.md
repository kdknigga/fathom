---
phase: 5
slug: refactor-form-validation-to-use-pydantic
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-10
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2+ |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/test_forms.py tests/test_edge_cases.py -x` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest -x && uv run ruff check . && uv run ty check && uv run pyrefly check`
- **After every plan wave:** Run `uv run pytest && uv run prek run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | REFACTOR-01 | unit | `uv run pytest tests/test_engine.py tests/test_amortization.py -x` | Yes | ⬜ pending |
| 05-01-02 | 01 | 1 | REFACTOR-05 | unit | `uv run pytest tests/test_engine.py -x` | Yes | ⬜ pending |
| 05-02-01 | 02 | 1 | REFACTOR-02 | unit | `uv run pytest tests/test_forms.py -x` | Yes (rewrite) | ⬜ pending |
| 05-02-02 | 02 | 1 | REFACTOR-03 | unit | `uv run pytest tests/test_forms.py tests/test_edge_cases.py -x` | Yes (rewrite) | ⬜ pending |
| 05-03-01 | 03 | 2 | REFACTOR-04 | integration | `uv run pytest tests/test_routes.py -x` | Yes | ⬜ pending |
| 05-03-02 | 03 | 2 | REFACTOR-06 | lint | `uv run ty check && uv run pyrefly check` | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. Test files for forms and edge cases exist and will be rewritten to match the new API.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
