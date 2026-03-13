---
phase: 7
slug: dark-mode
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x + Playwright 1.58+ |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest tests/ && uv run python tests/playwright_verify.py` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run ruff check . && uv run ruff format --check .`
- **After every plan wave:** Run `uv run pytest tests/ && uv run python tests/playwright_verify.py`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | DARK-01 | Playwright | `uv run python tests/playwright_verify.py` (dark mode section) | ❌ W0 | ⬜ pending |
| 07-01-02 | 01 | 1 | DARK-02 | Playwright | Screenshot comparison light/dark; verify no hardcoded hex in computed styles | ❌ W0 | ⬜ pending |
| 07-01-03 | 01 | 1 | DARK-03 | Playwright | Verify SVG text elements visible, chart elements have appropriate contrast | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/playwright_verify.py` — needs new dark mode verification sections using `color_scheme="dark"` context
- [ ] Dark mode checks to add: page background color verification, caveat card visibility, SVG chart text legibility, winner column highlight visibility, pattern background color check

*Existing infrastructure covers unit test and lint requirements. Only Playwright dark mode sections are new.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification via Playwright.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
