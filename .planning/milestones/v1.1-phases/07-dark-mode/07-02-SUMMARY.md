---
phase: 07-dark-mode
plan: 02
subsystem: ui
tags: [css-variables, dark-mode, svg-charts, playwright]

requires:
  - phase: 07-01
    provides: CSS custom properties and dark mode media query block
provides:
  - SVG chart colors using CSS variables with dark mode overrides
  - Brighter series color variants for dark mode readability
  - Playwright dark/light mode verification tests
affects: []

tech-stack:
  added: []
  patterns:
    - CSS variables for SVG inline attribute colors via var() in fill/stroke
    - Playwright color_scheme context for theme testing

key-files:
  created: []
  modified:
    - src/fathom/static/style.css
    - src/fathom/templates/partials/results/bar_chart.html
    - src/fathom/templates/partials/results/line_chart.html
    - tests/playwright_verify.py

key-decisions:
  - "Used CSS variables in SVG fill/stroke attributes (var(--chart-series-N)) instead of Python-side color switching"
  - "Brighter dark mode series colors: #60a5fa, #f87171, #34d399, #fbbf24"

patterns-established:
  - "SVG chart theming: use var(--chart-*) CSS variables in inline SVG attributes"

requirements-completed: [DARK-03]

duration: 7min
completed: 2026-03-13
---

# Phase 07 Plan 02: SVG Chart Dark Mode Summary

**SVG chart colors replaced with CSS variables providing automatic dark/light mode switching with brighter series colors and Playwright verification**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-13T20:33:49Z
- **Completed:** 2026-03-13T20:40:55Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- All hardcoded hex colors in bar_chart.html and line_chart.html replaced with CSS variables
- Chart series colors switch to brighter variants in dark mode for readability
- Pattern fill backgrounds use var(--chart-bg) instead of hardcoded white
- Playwright tests verify both dark and light mode rendering (60 total checks)

## Task Commits

Each task was committed atomically:

1. **Task 1: Replace hardcoded SVG colors with CSS variables** - `cc1cb2b` (feat)
2. **Task 2: Add Playwright dark mode verification tests** - `5e35d45` (feat)

## Files Created/Modified
- `src/fathom/static/style.css` - Added chart CSS variables (grid, label, bg, series-0..3) with dark overrides
- `src/fathom/templates/partials/results/bar_chart.html` - Replaced all hardcoded colors with var() references
- `src/fathom/templates/partials/results/line_chart.html` - Replaced all hardcoded colors with var() references
- `tests/playwright_verify.py` - Added verify_dark_mode() and verify_light_mode() with color luminance checks

## Decisions Made
- Used CSS variables in SVG fill/stroke attributes directly (var(--chart-series-N) indexed by loop.index0) rather than Python-side color switching, keeping the Python COLORS array as a fallback reference
- Selected brighter dark mode series colors: blue #60a5fa, red #f87171, green #34d399, orange #fbbf24

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed background color check targeting wrong element**
- **Found during:** Task 2 (Playwright dark mode tests)
- **Issue:** Test checked document.body backgroundColor which returns rgba(0,0,0,0) because Pico CSS sets background on document.documentElement
- **Fix:** Changed to check document.documentElement.backgroundColor
- **Files modified:** tests/playwright_verify.py
- **Verification:** Both dark and light mode background checks now pass
- **Committed in:** 5e35d45 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed pattern background check including solid pattern**
- **Found during:** Task 2 (Playwright dark mode tests)
- **Issue:** Solid pattern uses fill="currentColor" (inherits series color), not var(--chart-bg). Test incorrectly expected all pattern rects to be light/dark background.
- **Fix:** Excluded #bar-pattern-solid from pattern background checks
- **Files modified:** tests/playwright_verify.py
- **Verification:** Pattern background checks pass in both modes
- **Committed in:** 5e35d45 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 bugs in test assertions)
**Impact on plan:** Both fixes necessary for correct test assertions. No scope creep.

## Issues Encountered
- Stale server process from a previous run had data-theme="light" hardcoded, causing initial dark mode test failures. Resolved by restarting the server with the current codebase.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Dark mode is fully functional for all custom CSS, SVG charts, and Pico CSS
- Phase 07 (Dark Mode) is complete
- Ready for Phase 08 (Comma Inputs)

---
*Phase: 07-dark-mode*
*Completed: 2026-03-13*
