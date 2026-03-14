---
phase: 7
slug: dark-mode
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-13
validated: 2026-03-14
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
| **Full suite command** | `uv run pytest tests/ && FATHOM_PORT=5001 uv run fathom & sleep 2 && uv run python tests/playwright_verify.py` |
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
| 07-01-01 | 01 | 1 | DARK-01 | Playwright | `verify_dark_mode()`: page bg is dark on load, no flash | ✅ | ✅ green |
| 07-01-02 | 01 | 1 | DARK-02 | Playwright | `verify_dark_mode()`: caveat card dark bg, winner col visible | ✅ | ✅ green |
| 07-01-03 | 01 | 1 | DARK-03 | Playwright | `verify_dark_mode()`: bar/line text legible, patterns not white | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/playwright_verify.py` — dark mode verification sections using `color_scheme="dark"` context
- [x] Dark mode checks: page background color verification, caveat card visibility, SVG chart text legibility, winner column highlight visibility, pattern background color check

*All Wave 0 requirements implemented in `tests/playwright_verify.py` functions `verify_dark_mode()` (lines 69-175) and `verify_light_mode()` (lines 317+).*

---

## Manual-Only Verifications

*All phase behaviors have automated verification via Playwright.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** complete

---

## Validation Audit 2026-03-14

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

All 3 requirements (DARK-01, DARK-02, DARK-03) verified via `tests/playwright_verify.py` — 129 Playwright checks pass, 241 pytest tests pass.
