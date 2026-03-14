---
phase: 12-python-linting-and-typechecking-cleanup
plan: 01
subsystem: tooling
tags: [ruff, linting, pylint, pytest-style, datetime-timezone, trailing-commas]

# Dependency graph
requires: []
provides:
  - Expanded ruff lint config with PL, PT, DTZ, T20 rules
  - Zero lint violations (except complexity rules deferred to Plan 02)
  - Per-file-ignores for test code and Flask app factory lazy imports
affects: [12-02]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Per-file-ignores for complexity rules pending refactor"
    - "datetime.now(tz=UTC).date() instead of date.today()"
    - "pytest.fail() instead of assert False in tests"

key-files:
  created: []
  modified:
    - pyproject.toml
    - src/fathom/routes.py
    - src/fathom/forms.py
    - tests/test_forms.py
    - tests/playwright_verify.py

key-decisions:
  - "Kept COM812 in ignore list because ruff formatter handles trailing commas natively and warns about conflict"
  - "Added per-file-ignores for PLR0911/PLR0912/PLR0915 in charts.py, forms.py, formatting.py (Plan 02 refactors)"
  - "Used datetime.UTC alias instead of timezone.utc per UP017 rule"

patterns-established:
  - "Per-file-ignores for complexity: temporary until Plan 02 refactors"

requirements-completed: [LINT-01, LINT-02, LINT-03]

# Metrics
duration: 3min
completed: 2026-03-14
---

# Phase 12 Plan 01: Ruff Lint Expansion Summary

**Expanded ruff with PL/PT/DTZ/T20 rules, applied 77 auto-fixes, resolved all trivial manual violations across 14 files**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-14T13:08:58Z
- **Completed:** 2026-03-14T13:12:07Z
- **Tasks:** 2
- **Files modified:** 14

## Accomplishments
- Added PL (Pylint), PT (pytest-style), DTZ (datetime timezone), T20 (print) rule sets to ruff config
- Applied 77 safe auto-fixes including trailing commas, if-stmt-min-max, and import sorting
- Fixed all trivial manual violations: DTZ011, PLW2901, PT015, PLR1714
- Removed all inline noqa/type-ignore comments -- zero inline suppressions remain
- All 241 tests pass, ruff/ty/pyrefly all clean

## Task Commits

Tasks 1 and 2 were combined into a single commit due to pre-commit hook requiring all violations resolved before committing:

1. **Task 1+2: Expand ruff config, apply auto-fixes, fix manual violations** - `d3017cf` (feat)

**Plan metadata:** pending (docs: complete plan)

## Files Created/Modified
- `pyproject.toml` - Expanded ruff lint select, ignore, and per-file-ignores
- `src/fathom/routes.py` - DTZ011 fix: date.today() to datetime.now(tz=UTC).date()
- `src/fathom/forms.py` - PLW2901 fix: renamed loop variable to avoid shadowing
- `tests/test_forms.py` - PT015 fix: assert False to pytest.fail(), added pytest import
- `tests/playwright_verify.py` - PLR1714 fix: merged comparisons into set membership
- `src/fathom/caveats.py` - Auto-fix: trailing commas
- `src/fathom/charts.py` - Auto-fix: trailing commas, formatting
- `src/fathom/engine.py` - Auto-fix: trailing commas
- `src/fathom/opportunity.py` - Auto-fix: trailing commas
- `src/fathom/results.py` - Auto-fix: trailing commas
- `tests/test_charts.py` - Auto-fix: trailing commas
- `tests/test_edge_cases.py` - Auto-fix: trailing commas
- `tests/test_results_helpers.py` - Auto-fix: trailing commas
- `tests/test_routes.py` - Auto-fix: trailing commas

## Decisions Made
- Kept COM812 in ruff ignore list: ruff's own formatter warns about conflict with COM812 rule. The formatter handles trailing commas natively via skip-magic-trailing-comma setting, making the rule redundant.
- Added per-file-ignores for PLR0911/PLR0912/PLR0915 in charts.py, forms.py, formatting.py as temporary measures until Plan 02 refactors those complex functions.
- Used `datetime.UTC` alias instead of `timezone.utc` per ruff UP017 rule preference.
- Combined Tasks 1 and 2 into single commit because pre-commit hooks require zero violations before any commit can be made.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] COM812 kept in ignore due to formatter conflict**
- **Found during:** Task 1
- **Issue:** Ruff warns that COM812 rule conflicts with the ruff formatter
- **Fix:** Kept COM812 in ignore list; formatter handles trailing commas natively
- **Files modified:** pyproject.toml
- **Verification:** `uv run ruff check .` passes clean, no formatter warnings

**2. [Rule 3 - Blocking] UP017 required datetime.UTC alias**
- **Found during:** Task 2
- **Issue:** Using timezone.utc triggered UP017 (use datetime.UTC alias)
- **Fix:** Changed import and usage to `from datetime import UTC, datetime`
- **Files modified:** src/fathom/routes.py
- **Verification:** `uv run ruff check .` passes clean

**3. [Rule 3 - Blocking] Tasks combined into single commit**
- **Found during:** Task 1 commit attempt
- **Issue:** Pre-commit hook runs ruff check on all staged files; Task 1 config changes expose violations that Task 2 was meant to fix
- **Fix:** Applied all fixes (config + auto-fix + manual) before committing
- **Impact:** Two logical tasks became one commit, but all work completed

---

**Total deviations:** 3 auto-fixed (3 blocking)
**Impact on plan:** All fixes necessary for pre-commit compliance. No scope creep.

## Issues Encountered
- Pre-commit hook prevented splitting config expansion and manual fixes into separate commits. Resolved by combining into single commit.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Ruff config fully expanded with PL/PT/DTZ/T20 rules
- Only complexity violations (PLR0911, PLR0912, PLR0915) remain in production code -- per-file-ignores added as temporary measures
- Plan 02 can now refactor complex functions and remove per-file-ignores

---
*Phase: 12-python-linting-and-typechecking-cleanup*
*Completed: 2026-03-14*
