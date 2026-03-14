---
phase: 07-dark-mode
plan: 01
subsystem: ui
tags: [css, dark-mode, pico-css, prefers-color-scheme, custom-properties]

# Dependency graph
requires:
  - phase: 06-charts
    provides: "Base CSS styles and Pico CSS framework integration"
provides:
  - "OS-preference dark mode auto-detection via Pico CSS"
  - "CSS custom properties for all custom colors (caveats, winner, highlights)"
  - "Dark mode color overrides in @media prefers-color-scheme block"
affects: [07-02]

# Tech tracking
tech-stack:
  added: []
  patterns: ["CSS custom properties for theme-aware colors", "prefers-color-scheme media query for dark mode"]

key-files:
  created: []
  modified:
    - src/fathom/templates/base.html
    - src/fathom/static/style.css

key-decisions:
  - "Used :root:not([data-theme]) selector in dark media query for Pico CSS compatibility"
  - "Dark mode caveat colors use muted/desaturated backgrounds with lighter text for readability"

patterns-established:
  - "CSS custom property pattern: define light defaults in :root, override in @media (prefers-color-scheme: dark)"
  - "All custom colors must use var() references, never hardcoded hex in rules"

requirements-completed: [DARK-01, DARK-02]

# Metrics
duration: 1min
completed: 2026-03-13
---

# Phase 7 Plan 1: Dark Mode CSS Summary

**OS-preference dark mode via Pico CSS auto-detection with CSS custom properties for all 11 custom colors**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-13T20:30:08Z
- **Completed:** 2026-03-13T20:31:26Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- Enabled Pico CSS built-in dark mode by removing `data-theme="light"` attribute
- Defined 11 CSS custom properties for all custom colors (caveats, winner star, winner column)
- Added `@media (prefers-color-scheme: dark)` block with dark-mode color overrides
- Replaced all hardcoded hex colors in CSS rules with `var()` references

## Task Commits

Each task was committed atomically:

1. **Task 1: Enable Pico dark mode and define CSS custom properties** - `5b348fc` (feat)

## Files Created/Modified
- `src/fathom/templates/base.html` - Removed data-theme="light" to enable Pico auto dark mode
- `src/fathom/static/style.css` - Added :root custom properties, dark mode overrides, replaced hardcoded colors

## Decisions Made
- Used `:root:not([data-theme])` selector in dark media query to match Pico CSS internal convention, ensuring custom properties switch correctly when Pico switches its own variables
- Dark caveat backgrounds use deep muted tones (#422006 warning, #450a0a critical, #1e3a5f info) with light text for readability without strict WCAG AA enforcement per user decision

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Dark mode CSS foundation is complete
- Ready for Plan 02 (browser-based visual verification of dark mode rendering)

---
*Phase: 07-dark-mode*
*Completed: 2026-03-13*
