---
phase: 2
slug: web-layer-and-input-forms
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-10
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
| 02-01-01 | 01 | 0 | FORM-01 | integration | `uv run pytest tests/test_routes.py::test_purchase_price_field -x` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 0 | FORM-05 | integration | `uv run pytest tests/test_routes.py::test_add_remove_options -x` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 0 | FORM-06 | integration | `uv run pytest tests/test_routes.py::test_type_switch_fields -x` | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 0 | OPTY-01–06 | unit | `uv run pytest tests/test_forms.py::test_option_type_fields -x` | ❌ W0 | ⬜ pending |
| 02-01-05 | 01 | 0 | FORM-02 | integration | `uv run pytest tests/test_routes.py::test_return_rate_presets -x` | ❌ W0 | ⬜ pending |
| 02-01-06 | 01 | 0 | FORM-03 | integration | `uv run pytest tests/test_routes.py::test_inflation_toggle -x` | ❌ W0 | ⬜ pending |
| 02-01-07 | 01 | 0 | FORM-04 | integration | `uv run pytest tests/test_routes.py::test_tax_toggle -x` | ❌ W0 | ⬜ pending |
| 02-01-08 | 01 | 0 | FORM-07 | integration | `uv run pytest tests/test_routes.py::test_reset_form -x` | ❌ W0 | ⬜ pending |
| 02-01-09 | 01 | 0 | A11Y-01 | integration | `uv run pytest tests/test_routes.py::test_labels_present -x` | ❌ W0 | ⬜ pending |
| 02-01-10 | 01 | 0 | LYOT-01 | integration | `uv run pytest tests/test_routes.py::test_grid_layout -x` | ❌ W0 | ⬜ pending |
| 02-01-11 | 01 | 0 | TECH-03 | integration | `uv run pytest tests/test_routes.py::test_form_repopulation -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_routes.py` — Flask test client integration tests for all form routes
- [ ] `tests/test_forms.py` — Unit tests for form parsing and validation logic
- [ ] `tests/conftest.py` — Add Flask app fixture (`create_app` + `client` fixture)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Consumer-friendly language in labels | LYOT-03 | Content/UX review — cannot be automated | Review all visible labels and text for plain language, no jargon |
| Mobile stacked layout | LYOT-02 | Requires visual inspection at mobile viewport | Resize browser to <768px, verify single-column stack |
| Sticky "View Results" anchor | LYOT-02 | CSS position:sticky behavior needs visual check | Scroll form on mobile, verify anchor stays visible |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
