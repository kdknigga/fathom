---
phase: 06-bug-fixes-and-tech-debt-cleanup
plan: 02
subsystem: testing, docs
tags: [playwright, accessibility, a11y, data-tables, readme]

requires:
  - phase: 03-results-display-and-charts
    provides: SVG charts with accessible data tables
provides:
  - Cell-by-cell Playwright assertions for bar and line chart data tables
  - README architecture tree with config.py entry
affects: []

tech-stack:
  added: []
  patterns:
    - "Playwright CSS :has() selector for targeting tables by caption text"
    - "Cell-by-cell data table verification with exact Decimal-deterministic values"

key-files:
  created: []
  modified:
    - README.md
    - tests/playwright_verify.py

key-decisions:
  - "Used CSS :has(caption:text()) selector to locate specific data tables by caption"
  - "Asserted exact dollar values without tolerance since Decimal arithmetic is deterministic"

patterns-established:
  - "Data table test pattern: locate by caption, verify visually-hidden class, check headers, assert cell values"

requirements-completed: [FORM-05]

duration: 2min
completed: 2026-03-13
---

# Phase 6 Plan 2: README and Data Table Test Hardening Summary

**Added config.py to README architecture tree and 30+ cell-by-cell Playwright assertions for bar/line chart accessible data tables**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-13T16:06:28Z
- **Completed:** 2026-03-13T16:08:55Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- README architecture tree now includes config.py with pydantic-settings description
- Bar chart data table: verified visually-hidden class, caption, headers, 2 rows with exact costs ($29,171 and $30,823)
- Line chart data table: verified visually-hidden class, caption, 3 headers, 4 rows with exact month/cost values
- A11Y-02 regression coverage for both chart data tables
- All 52 Playwright checks pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Add config.py to README architecture tree** - `10a5bcf` (docs)
2. **Task 2: Harden Playwright data table tests with cell value assertions** - `085d9a0` (test)

## Files Created/Modified
- `README.md` - Added config.py entry to architecture tree after app.py
- `tests/playwright_verify.py` - Added Check 5 (bar chart data table) and Check 6 (line chart data table) with full cell-by-cell assertions

## Decisions Made
- Used CSS `:has(caption:text())` selector to locate specific data tables by their caption text
- Asserted exact formatted dollar amounts without tolerance since Decimal arithmetic produces deterministic output
- Renumbered existing Check 5 (responsive) to Check 7 to maintain sequential numbering

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed ruff FBT003 lint error for boolean positional value**
- **Found during:** Task 2
- **Issue:** `check(name, False, detail)` flagged as boolean positional value in function call
- **Fix:** Assigned `len(cells) >= 3` to variable before passing to check function
- **Files modified:** tests/playwright_verify.py
- **Committed in:** 085d9a0 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor lint compliance fix. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Documentation gap (config.py in README) closed
- A11Y-02 data table test gap closed with full cell-by-cell verification
- All quality gates pass

---
*Phase: 06-bug-fixes-and-tech-debt-cleanup*
*Completed: 2026-03-13*
