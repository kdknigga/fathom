---
phase: 06-bug-fixes-and-tech-debt-cleanup
plan: 01
subsystem: forms, ui
tags: [pydantic, validation, jinja2, htmx]

requires:
  - phase: 05-refactor-form-validation-to-use-pydantic
    provides: Pydantic-based form validation with OptionInput/FormInput models
provides:
  - retroactive_interest field on OptionInput with cross-field validation
  - Server-side 2-4 option count enforcement via FormInput field_validator
  - Fixed return_preset format producing "0.10" instead of "0.1"
  - Retroactive interest checkbox in promo_zero template
  - Option count error display in index.html
affects: []

tech-stack:
  added: []
  patterns:
    - "Cross-field silent reset pattern for UI-hidden fields"
    - "Defense-in-depth boolean AND in build_domain_objects"

key-files:
  created: []
  modified:
    - src/fathom/forms.py
    - src/fathom/routes.py
    - src/fathom/templates/partials/option_fields/promo_zero.html
    - src/fathom/templates/index.html
    - tests/test_forms.py
    - tests/test_routes.py

key-decisions:
  - "Retroactive interest silently resets (not error) when deferred_interest=False or type!=promo_zero"
  - "Retroactive interest checkbox defaults to checked (most real-world 0% promos are retroactive)"
  - "Defense-in-depth: build_domain_objects ANDs retroactive_interest with deferred_interest"

patterns-established:
  - "Silent reset pattern: cross-field model_validator resets invalid checkbox combos without raising errors"

requirements-completed: [FORM-05]

duration: 4min
completed: 2026-03-13
---

# Phase 06 Plan 01: Bug Fixes and Form Validation Gaps Summary

**Retroactive interest checkbox with cross-field validation, 2-4 option count enforcement, and return_preset format fix**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-13T16:06:32Z
- **Completed:** 2026-03-13T16:10:56Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Added retroactive_interest field to OptionInput with cross-field validation that silently resets when inapplicable
- Added server-side option count validator enforcing 2-4 financing options (FORM-05)
- Fixed return_preset format bug: f"{rate:.2f}" produces "0.10" instead of str(0.10) -> "0.1"
- Added retroactive_interest checkbox to promo_zero template (visible only when deferred_interest checked, default checked)
- Added option count validation error display at top of form with role="alert" for accessibility

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Add failing tests** - `f0d64ba` (test)
2. **Task 1 GREEN: Implement retroactive_interest, option count, return_preset fix** - `e241b4d` (feat)
3. **Task 2: Template changes for retroactive_interest checkbox and option count error** - `a930534` (feat)

## Files Created/Modified
- `src/fathom/forms.py` - Added retroactive_interest field, cross-field validation, option count validator, build_domain_objects pass-through
- `src/fathom/routes.py` - Fixed return_preset format from str() to f-string with :.2f
- `src/fathom/templates/partials/option_fields/promo_zero.html` - Added retroactive_interest checkbox with conditional visibility
- `src/fathom/templates/index.html` - Added option count error display with role="alert"
- `tests/test_forms.py` - Added 10 new tests for retroactive_interest, option count, and build_domain_objects
- `tests/test_routes.py` - Added return_preset format test

## Decisions Made
- Retroactive interest uses silent reset (not validation error) because the UI hides the checkbox when inapplicable; only crafted POSTs can trigger the mismatch
- Default retroactive_interest to checked when deferred_interest is enabled (matches real-world 0% promo behavior)
- Defense-in-depth: build_domain_objects ANDs retroactive_interest with deferred_interest as extra safety layer

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All v1.0 audit form validation gaps closed
- 179 tests passing, all lint and type checks clean

---
*Phase: 06-bug-fixes-and-tech-debt-cleanup*
*Completed: 2026-03-13*
