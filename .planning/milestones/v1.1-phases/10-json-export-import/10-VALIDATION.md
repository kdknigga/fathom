---
phase: 10
slug: json-export-import
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-13
validated: 2026-03-14
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/test_routes.py tests/test_forms.py -x -q` |
| **Full suite command** | `uv run pytest -x -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_routes.py tests/test_forms.py -x -q`
- **After every plan wave:** Run `uv run pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | DATA-01 | unit | `uv run pytest tests/test_forms.py::TestExportDict -x` | ✅ | ✅ green |
| 10-01-02 | 01 | 1 | DATA-01 | integration | `uv run pytest tests/test_routes.py::TestExport -x` | ✅ | ✅ green |
| 10-01-03 | 01 | 1 | DATA-02 | integration | `uv run pytest tests/test_routes.py::TestImport -x` | ✅ | ✅ green |
| 10-01-04 | 01 | 1 | DATA-03 | integration | `uv run pytest tests/test_routes.py::TestImportErrors -x` | ✅ | ✅ green |
| 10-01-05 | 01 | 1 | DATA-02 | integration | `uv run pytest tests/test_routes.py::TestImportRoundTrip -x` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_forms.py::TestExportDict` — unit tests for export dict helper (DATA-01) — 3 tests
- [x] `tests/test_routes.py::TestExport` — export route integration tests (DATA-01) — 6 tests
- [x] `tests/test_routes.py::TestImport` — import route integration tests (DATA-02) — 1 test
- [x] `tests/test_routes.py::TestImportErrors` — error handling tests (DATA-03) — 3 tests
- [x] `tests/test_routes.py::TestImportRoundTrip` — round-trip fidelity tests (DATA-02) — 1 test

*All tests created during execution via TDD (plan 01). Playwright browser verification in `tests/playwright_verify.py::verify_export_import` (27 checks).*

---

## Manual-Only Verifications

*All phase behaviors have automated verification (pytest + Playwright).*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** complete

---

## Validation Audit 2026-03-14

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
