---
phase: 15-validation-and-htmx-guards
plan: 02
subsystem: routes
tags: [htmx, flask, guards, validation, accessibility]

# Dependency graph
requires:
  - phase: 15-validation-and-htmx-guards
    provides: Phase context and research for option count guards
provides:
  - Server-side guards on add/remove option HTMX endpoints enforcing 2-4 option contract
  - Warning banner template slot with role="alert" for accessibility
  - count_form_options() helper in forms.py
  - _build_options_list() helper in routes.py reducing code duplication
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Early guard pattern: count before extract, return unchanged form with warning on violation"
    - "Jinja2 is-defined guard for optional template variables"

key-files:
  created: []
  modified:
    - src/fathom/routes.py
    - src/fathom/forms.py
    - src/fathom/templates/partials/option_list.html
    - tests/test_routes.py

key-decisions:
  - "Created count_form_options() public helper rather than exposing _OPTION_INDEX_RE regex"
  - "Extracted _build_options_list() helper to reduce duplicated option-building loops in routes"

patterns-established:
  - "Guard pattern: count options from raw form keys before calling extract_form_data"
  - "Warning banner: use Jinja2 'is defined and' guard for optional warning_message variable"

requirements-completed: [VAL-03, VAL-04, TEST-03]

# Metrics
duration: 4min
completed: 2026-03-15
---

# Phase 15 Plan 02: HTMX Option Count Guards Summary

**Server-side guards on add/remove HTMX endpoints enforcing 2-4 option contract with accessible warning banners**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-15T15:17:43Z
- **Completed:** 2026-03-15T15:21:37Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 4

## Accomplishments
- Add option at 4 returns HTTP 200 with unchanged form and "Maximum 4 options allowed" warning
- Remove option at 2 returns HTTP 200 with unchanged form and "Minimum 2 options required" warning
- Warning banner uses role="alert" for screen reader accessibility
- Normal add/remove operations continue working correctly
- All 314 tests pass including 4 new guard tests

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Add failing guard tests** - `95f2bd3` (test)
2. **Task 1 (GREEN): Implement guards and warning banner** - `a3d780d` (feat)

## Files Created/Modified
- `src/fathom/forms.py` - Added count_form_options() public helper for counting option indices from raw form keys
- `src/fathom/routes.py` - Added early count guards in add_option/remove_option, extracted _build_options_list() helper
- `src/fathom/templates/partials/option_list.html` - Added warning banner slot with role="alert" at top of option list
- `tests/test_routes.py` - Added TestAddOptionGuard and TestRemoveOptionGuard test classes (4 tests)

## Decisions Made
- Created `count_form_options()` as a public function in forms.py rather than exposing the private `_OPTION_INDEX_RE` regex, providing a clean API boundary
- Extracted `_build_options_list()` helper to eliminate duplicated option-building loops across add_option, remove_option, and guard paths

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-commit hook stash/restore cycle reverted unstaged working tree changes after the RED commit, requiring re-application of routes.py edits for the GREEN phase

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Option count guards complete, enforcing the 2-4 option contract server-side
- Warning banners auto-clear on next HTMX interaction (no persistent state needed)
- Ready for remaining Phase 15 plans or Phase 16

---
*Phase: 15-validation-and-htmx-guards*
*Completed: 2026-03-15*
