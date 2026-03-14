---
phase: 12-python-linting-and-typechecking-cleanup
plan: 02
subsystem: code-quality
tags: [ruff, refactoring, complexity, pylint]

# Dependency graph
requires:
  - phase: 12-python-linting-and-typechecking-cleanup
    provides: "Expanded ruff rule set with per-file-ignores for complexity violations"
provides:
  - "All production functions compliant with ruff default complexity thresholds"
  - "Zero ruff violations across entire codebase with no per-file-ignores for production code"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Extract helper functions to reduce cyclomatic complexity"
    - "Type alias _ScaleFn for callback function signatures"

key-files:
  created: []
  modified:
    - src/fathom/charts.py
    - src/fathom/forms.py
    - src/fathom/formatting.py
    - pyproject.toml

key-decisions:
  - "Extracted chart helpers (_collect_option_points, _build_line_dataset, _build_axis_labels) as module-level functions with _ScaleFn type alias for scale callbacks"
  - "Extracted per-field validators as module-level functions before OptionInput class using forward reference annotations"
  - "Extracted _comma_format_str to isolate string-path complexity from comma_format"

patterns-established:
  - "Helper extraction pattern: break complex validators into per-concern functions that mutate an errors list"

requirements-completed: [LINT-04]

# Metrics
duration: 4min
completed: 2026-03-14
---

# Phase 12 Plan 02: Complexity Refactoring Summary

**Refactored 3 complex functions (prepare_line_chart, validate_by_type, comma_format) below ruff default thresholds by extracting 10 helper functions, eliminating all PLR0911/PLR0912/PLR0915 per-file-ignores**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-14T13:15:08Z
- **Completed:** 2026-03-14T13:19:08Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- prepare_line_chart reduced from 64 statements/14 branches to within limits via 3 extracted helpers
- validate_by_type reduced from 62 statements/24 branches to 16/3 via 7 extracted per-field validators
- comma_format reduced from 8 returns to 3 by extracting _comma_format_str helper
- Removed all production-code per-file-ignores from pyproject.toml (charts.py, forms.py, formatting.py)
- All 241 tests pass, zero ruff violations, ty and pyrefly clean, no inline suppressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Refactor charts.py prepare_line_chart** - `67132cc` (refactor)
2. **Task 2: Refactor forms.py validate_by_type and formatting.py comma_format** - `5d093fc` (refactor)

## Files Created/Modified
- `src/fathom/charts.py` - Extracted _collect_option_points, _build_line_dataset, _build_axis_labels; added _ScaleFn type alias
- `src/fathom/forms.py` - Extracted _validate_apr, _validate_term_months, _validate_down_payment, _validate_promo_fields, _validate_post_promo_apr, _validate_cash_back, _validate_discounted_price
- `src/fathom/formatting.py` - Extracted _comma_format_str for string-path formatting
- `pyproject.toml` - Removed per-file-ignores for charts.py, forms.py, formatting.py

## Decisions Made
- Used module-level helper functions (not methods) for extracted validators in forms.py, leveraging `from __future__ import annotations` for forward references to OptionInput
- Used `_ScaleFn = Callable[[int | float], float]` type alias for scale function callbacks in charts.py
- Kept scale_x/scale_y as closures in prepare_line_chart since they capture max_months/max_cost/width/height

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 12 fully complete: all ruff rules expanded, all complexity violations resolved
- Codebase at zero lint violations with comprehensive rule set
- Ready for any future development with clean baseline

---
*Phase: 12-python-linting-and-typechecking-cleanup*
*Completed: 2026-03-14*

## Self-Check: PASSED
