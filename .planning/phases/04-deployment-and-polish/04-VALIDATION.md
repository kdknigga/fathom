---
phase: 4
slug: deployment-and-polish
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-10
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | pyproject.toml [tool.pytest.ini_options] |
| **Quick run command** | `uv run pytest -x -q` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest -x -q`
- **After every plan wave:** Run `uv run pytest && uv run ruff check . && uv run ruff format --check .`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | TECH-06 | unit | `uv run pytest tests/test_config.py -x` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | TECH-06 | unit | `uv run pytest tests/test_config.py -x` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 1 | TECH-05 | integration | `docker build -t fathom . && docker run --rm -p 5000:5000 -d fathom` + curl | ❌ W0 | ⬜ pending |
| 04-02-02 | 02 | 1 | PERF-01 | integration | `uv run pytest tests/test_performance.py -x` | ❌ W0 | ⬜ pending |
| 04-03-01 | 03 | 2 | TECH-07 | smoke | `test -s README.md` | ❌ | ⬜ pending |
| 04-03-02 | 03 | 2 | TECH-08 | smoke | `test -s LICENSE` | ❌ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_config.py` — stubs for TECH-06 (Settings validation, defaults, env prefix, invalid values)
- [ ] `tests/test_performance.py` — stubs for PERF-01 (response time assertion under 300ms via test client)

*Existing pytest infrastructure covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Docker build & run | TECH-05 | Docker daemon required; Playwright cannot test container builds | `docker build -t fathom . && docker run --rm -p 5000:5000 -d fathom && curl -s http://localhost:5000/ | head -20` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
