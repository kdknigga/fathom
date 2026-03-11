---
phase: 05-refactor-form-validation-to-use-pydantic
plan: 02
subsystem: forms
tags: [pydantic, validation, basemodel, model-validator, form-parsing]

# Dependency graph
requires:
  - phase: 05-refactor-form-validation-to-use-pydantic
    provides: "Pydantic BaseModel domain models (Plan 01)"
provides:
  - "Pydantic-powered form validation with FormInput, OptionInput, SettingsInput models"
  - "pydantic_errors_to_dict helper for template-compatible error display"
  - "extract_form_data function for non-validating routes"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: [model-validator-with-field-prefixed-errors, try-except-ValidationError-in-routes]

key-files:
  created: []
  modified: [src/fathom/forms.py, src/fathom/routes.py, tests/test_forms.py, tests/test_edge_cases.py]

key-decisions:
  - "Combined tasks 1 and 2 into single commit due to pre-commit hooks checking full project (forms.py and routes.py are interdependent)"
  - "Model validator errors use field:message prefix format, remapped in pydantic_errors_to_dict to preserve dot-notation error keys"
  - "Collected all option validation errors in a list and raised as newline-separated string to support multiple errors per option"
  - "extract_form_data returns raw dict (no validation) for add_option/remove_option routes"

patterns-established:
  - "Form validation via Pydantic model validators with field-prefixed error messages"
  - "pydantic_errors_to_dict bridges Pydantic ValidationError to template error display"
  - "try/except ValidationError pattern in routes for form submission handling"
  - "extract_form_data for non-validating form restructuring"

requirements-completed: [REFACTOR-02, REFACTOR-03, REFACTOR-04, REFACTOR-06]

# Metrics
duration: 8min
completed: 2026-03-11
---

# Phase 5 Plan 2: Pydantic Form Validation Summary

**Replaced ~200 lines of hand-written validation with Pydantic models (FormInput, OptionInput, SettingsInput), preserving identical error keys and messages**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-11T01:49:13Z
- **Completed:** 2026-03-11T01:57:32Z
- **Tasks:** 2 (combined into 1 commit due to interdependency)
- **Files modified:** 4

## Accomplishments
- Replaced validate_form_data, _validate_option, _validate_return_rate with Pydantic model validators
- parse_form_data now returns FormInput (Pydantic model) or raises ValidationError
- Error keys preserved in exact dot-notation format (options.0.apr, settings.return_rate)
- All 161 tests pass, all quality gates clean (ruff, ty, pyrefly)
- Zero template modifications

## Task Commits

Tasks were combined into a single commit due to pre-commit hook interdependency:

1. **Tasks 1+2: Rewrite forms.py + update routes.py + rewrite tests** - `ee75f11` (feat)

## Files Created/Modified
- `src/fathom/forms.py` - Added FormInput, OptionInput, SettingsInput Pydantic models; pydantic_errors_to_dict helper; extract_form_data function; deleted validate_form_data pipeline
- `src/fathom/routes.py` - Updated compare_options with try/except ValidationError; add_option/remove_option use extract_form_data
- `tests/test_forms.py` - Rewritten for new API: parse_form_data returns FormInput, validation tested via pydantic_errors_to_dict
- `tests/test_edge_cases.py` - Updated to use _get_errors helper pattern with ValidationError catch

## Decisions Made
- Combined tasks into single commit: pre-commit hooks (ty, pyrefly) check the entire project, so forms.py changes alone fail because routes.py still imports deleted validate_form_data
- Used field-prefixed error messages in model_validator ("apr:APR is required.") remapped by pydantic_errors_to_dict to correct dot-notation keys
- Collected all validation errors per option in a list, raised as newline-separated string to allow multiple field errors per option
- Edge case tests updated to always include 2 options (minimum required by form structure)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Combined tasks 1 and 2 into single commit**
- **Found during:** Task 1 commit attempt
- **Issue:** Pre-commit hooks (ty, pyrefly) check the full project; forms.py alone fails because routes.py still imports validate_form_data
- **Fix:** Combined forms.py, routes.py, and test changes into a single atomic commit
- **Files modified:** src/fathom/forms.py, src/fathom/routes.py, tests/test_forms.py, tests/test_edge_cases.py
- **Verification:** Pre-commit hooks pass, all 161 tests pass
- **Committed in:** ee75f11

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary due to project pre-commit hook configuration. No scope change -- all planned work was completed.

## Issues Encountered
- Pydantic model_validator errors get model-level loc (e.g., `options.0`) instead of field-level loc (e.g., `options.0.apr`). Solved by prefixing error messages with field names and remapping in pydantic_errors_to_dict.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 5 is complete: domain models (Plan 01) and form validation (Plan 02) both use Pydantic
- All 161 tests pass with zero quality gate issues
- The codebase is fully Pydantic-native for models and form validation

## Self-Check: PASSED

- All 4 modified files exist on disk
- Commit ee75f11 verified in git log
- All 161 tests pass
- All quality gates clean (ruff, ty, pyrefly)
- validate_form_data not found in src/ (confirmed deleted)
- Zero template files modified

---
*Phase: 05-refactor-form-validation-to-use-pydantic*
*Completed: 2026-03-11*
