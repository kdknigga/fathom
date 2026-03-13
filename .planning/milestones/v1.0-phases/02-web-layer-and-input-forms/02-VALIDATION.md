---
phase: 2
slug: web-layer-and-input-forms
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-10
validated: 2026-03-13
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x (already installed as dev dependency) |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

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
| 02-01-01 | 01 | 0 | FORM-01 | integration | `uv run pytest tests/test_routes.py::TestGetIndex::test_contains_purchase_price_input -x` | ✅ | ✅ green |
| 02-01-02 | 01 | 0 | FORM-05 | integration | `uv run pytest tests/test_routes.py::TestAddOption -x && uv run pytest tests/test_routes.py::TestRemoveOption -x` | ✅ | ✅ green |
| 02-01-03 | 01 | 0 | FORM-06 | integration | `uv run pytest tests/test_routes.py::TestTypeSwitch -x` | ✅ | ✅ green |
| 02-01-04 | 01 | 0 | OPTY-01–06 | unit | `uv run pytest tests/test_forms.py::TestValidateFormData -x` | ✅ | ✅ green |
| 02-01-05 | 01 | 0 | FORM-02 | integration | `uv run pytest tests/test_routes.py::TestFormSubmission::test_return_rate_presets -x` | ✅ | ✅ green |
| 02-01-06 | 01 | 0 | FORM-03 | integration | `uv run pytest tests/test_routes.py::TestFormSubmission::test_inflation_toggle -x` | ✅ | ✅ green |
| 02-01-07 | 01 | 0 | FORM-04 | integration | `uv run pytest tests/test_routes.py::TestFormSubmission::test_tax_toggle -x` | ✅ | ✅ green |
| 02-01-08 | 01 | 0 | FORM-07 | integration | `uv run pytest tests/test_routes.py::TestGetIndex::test_reset_form -x` | ✅ | ✅ green |
| 02-01-09 | 01 | 0 | A11Y-01 | integration | `uv run pytest tests/test_routes.py::TestGetIndex::test_labels_have_for_attribute -x` | ✅ | ✅ green |
| 02-01-10 | 01 | 0 | LYOT-01 | integration | `uv run pytest tests/test_routes.py::TestGetIndex::test_grid_layout -x` | ✅ | ✅ green |
| 02-01-11 | 01 | 0 | TECH-03 | integration | `uv run pytest tests/test_routes.py::TestFormSubmission::test_submit_repopulates_values -x` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_routes.py` — Flask test client integration tests for all form routes (21 tests)
- [x] `tests/test_forms.py` — Unit tests for form parsing and validation logic (37 tests)
- [x] `tests/conftest.py` — Flask app and client fixtures

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Consumer-friendly language in labels | LYOT-03 | Content/UX review — cannot be automated | Review all visible labels and text for plain language, no jargon |
| Mobile stacked layout | LYOT-02 | Requires visual inspection at mobile viewport | Resize browser to <768px, verify single-column stack |
| Sticky "View Results" anchor | LYOT-02 | CSS position:sticky behavior needs visual check | Scroll form on mobile, verify anchor stays visible |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** complete

---

## Validation Audit 2026-03-13

| Metric | Count |
|--------|-------|
| Gaps found | 3 |
| Resolved | 3 |
| Escalated | 0 |

Tests added: `test_tax_toggle`, `test_reset_form`, `test_grid_layout` in `tests/test_routes.py`.
All 11 requirements now have automated verification. Full suite: 58 tests passing (21 route + 37 form).
