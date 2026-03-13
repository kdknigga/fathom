---
phase: 02-web-layer-and-input-forms
plan: 02
subsystem: ui
tags: [flask, htmx, forms, validation, server-side-rendering]

requires:
  - phase: 02-web-layer-and-input-forms
    plan: 01
    provides: Flask app factory, routes blueprint, all 6 option type field templates, Pico CSS layout
  - phase: 01-calculation-engine
    provides: FinancingOption/GlobalSettings dataclasses, compare() engine function
provides:
  - Form parsing (POST data to structured dicts) via parse_form_data
  - Server-side validation with type-specific range checks via validate_form_data
  - Domain model construction from form data via build_domain_objects
  - HTMX type switching endpoint (GET /partials/option-fields/<idx>)
  - HTMX add/remove option endpoints preserving form state
  - POST /compare form submission calling engine.compare()
  - Value repopulation after submission (valid or invalid)
  - Inline error display under offending fields
affects: [02-03, 03-results-display]

tech-stack:
  added: []
  patterns: [form-parsing-validation-pipeline, htmx-partial-endpoints, template-context-builder]

key-files:
  created:
    - src/fathom/forms.py
    - tests/test_forms.py
    - tests/test_routes.py
  modified:
    - src/fathom/routes.py
    - src/fathom/templates/index.html

key-decisions:
  - "Three-function pipeline: parse_form_data -> validate_form_data -> build_domain_objects for clean separation"
  - "Percentage-to-decimal conversion in build_domain_objects (APR 5.99 -> Decimal('0.0599')) to match engine expectations"
  - "Type switching clears all field values (clean slate) per locked project decision"

patterns-established:
  - "Form pipeline: parse -> validate -> build_domain_objects for any form submission"
  - "_build_template_context helper constructs full context from parsed data for template rendering"
  - "Error keys use dot notation (options.0.apr) matching template error display pattern"

requirements-completed: [FORM-02, FORM-03, FORM-04, FORM-05, FORM-06, TECH-03]

duration: 5min
completed: 2026-03-10
---

# Phase 2 Plan 2: Form Processing, HTMX Interactivity, and Validation Summary

**Server-side form parsing/validation pipeline with HTMX type switching, add/remove options preserving state, and engine integration on valid submission**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-10T20:24:59Z
- **Completed:** 2026-03-10T20:30:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Form parsing module extracting indexed options from ImmutableMultiDict with gap handling and checkbox detection
- Type-specific validation (cash skips APR, promo types require their specific fields) with dot-notation error keys
- HTMX endpoints for type switching (clean slate), adding options (up to 4), and removing options (down to 2)
- POST /compare validates, repopulates all values on error, calls engine.compare() on success
- 48 tests total (30 unit + 18 integration) all passing with zero lint/format issues

## Task Commits

Each task was committed atomically:

1. **Task 1: Form parsing and validation module with tests (TDD)** - `e2a54a3` (feat)
2. **Task 2: HTMX endpoints, form submission handler, and integration tests** - `95ad8a2` (feat)

## Files Created/Modified
- `src/fathom/forms.py` - Form parsing, validation, and domain model construction (3 public functions)
- `src/fathom/routes.py` - Added 4 new routes: option-fields, add, remove, compare
- `src/fathom/templates/index.html` - Added scroll-to-error script block
- `tests/test_forms.py` - 30 unit tests for parse/validate/build pipeline
- `tests/test_routes.py` - 18 integration tests for all routes and HTMX behavior

## Decisions Made
- Three-function pipeline (parse -> validate -> build) keeps each step testable independently
- Percentage-to-decimal conversion happens in build_domain_objects to match engine's expectation of rates as decimals
- _build_template_context helper centralizes option list construction with template paths and field data

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Ruff FURB157 flagged Decimal("100") as verbose, auto-fixed to Decimal(100)
- Ruff TC002 required moving werkzeug import into TYPE_CHECKING block

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All form interactivity complete; ready for Plan 03 to add results display and styling
- engine.compare() is wired in and returns ComparisonResult to template context
- Template context includes `results` key when submission succeeds

---
*Phase: 02-web-layer-and-input-forms*
*Completed: 2026-03-10*
