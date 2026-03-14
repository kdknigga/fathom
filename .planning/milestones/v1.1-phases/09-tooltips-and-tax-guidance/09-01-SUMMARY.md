---
phase: 09-tooltips-and-tax-guidance
plan: 01
subsystem: ui
tags: [tooltips, tax-brackets, popover, css-anchor-positioning, accessibility]

requires:
  - phase: 08-comma-inputs
    provides: "Event delegation pattern on #comparison-form, formatting.js IIFE pattern"
provides:
  - "TAX_BRACKETS_2025 constant with 7 verified 2025 IRS brackets"
  - "tax_brackets passed to all template contexts via routes"
  - "_TOOLTIP_TEXT dict and tooltip field on breakdown rows"
  - "CSS for .tip, .tooltip-content, .label-with-tip, .bracket-table, .bracket-row"
  - "tooltips.js with bracket row click-to-fill and keyboard activation"
affects: [09-02-templates]

tech-stack:
  added: []
  patterns:
    - "HTML Popover API with CSS Anchor Positioning (@supports fallback)"
    - "Tooltip text as data field in breakdown row dicts"
    - "Delegated bracket row click handler in tooltips.js IIFE"

key-files:
  created:
    - src/fathom/tax_brackets.py
    - src/fathom/static/tooltips.js
  modified:
    - src/fathom/routes.py
    - src/fathom/results.py
    - src/fathom/static/style.css

key-decisions:
  - "Tooltip text stored in _TOOLTIP_TEXT dict in results.py, added as tooltip field to breakdown rows"
  - "CSS Anchor Positioning uses implicit invoker-anchor relationship with @supports fallback to fixed viewport centering"

patterns-established:
  - ".tip button + .tooltip-content popover pattern for all tooltips"
  - ".label-with-tip flex container to separate button from label"
  - "Bracket row aria-selected state management in JS"

requirements-completed: [TAX-01, TAX-02, TIPS-02, TIPS-03]

duration: 2min
completed: 2026-03-13
---

# Phase 9 Plan 1: Tooltip/Bracket Foundation Summary

**2025 IRS tax bracket data module, tooltip text for all breakdown metrics, CSS for tips/popovers/bracket-table with dark mode, and tooltips.js click-to-fill handler**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-13T23:37:42Z
- **Completed:** 2026-03-13T23:40:11Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Tax bracket data module with 7 verified 2025 IRS brackets (Rev. Proc. 2024-40)
- Tooltip explanations for all 7 breakdown metrics (definition, why it matters, example)
- Complete CSS infrastructure for tips, popovers, bracket table with dark mode and anchor positioning
- Bracket row click-to-fill handler with keyboard activation and aria-selected state

## Task Commits

Each task was committed atomically:

1. **Task 1: Tax bracket data module and route wiring** - `ed4ef26` (feat)
2. **Task 2: CSS styles and tooltips.js** - `86673f3` (feat)

## Files Created/Modified
- `src/fathom/tax_brackets.py` - 2025 IRS tax bracket data constant (7 brackets, Single + MFJ)
- `src/fathom/routes.py` - Import and pass tax_brackets to all template render calls
- `src/fathom/results.py` - _TOOLTIP_TEXT dict and tooltip field on breakdown rows
- `src/fathom/static/style.css` - Tip button, tooltip popover, bracket table CSS with dark mode
- `src/fathom/static/tooltips.js` - Bracket row click-to-fill and keyboard activation handler

## Decisions Made
- Tooltip text stored as Python dict in results.py alongside breakdown components, keeping content with data
- CSS Anchor Positioning uses implicit invoker-anchor relationship rather than explicit anchor names
- Bracket row click handler manages aria-selected state across sibling rows for visual feedback

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All foundation artifacts ready for 09-02 template integration
- Templates can consume tax_brackets from context and tooltip from breakdown rows
- CSS classes ready for use in template markup
- tooltips.js loaded and functional for bracket widget interaction

---
*Phase: 09-tooltips-and-tax-guidance*
*Completed: 2026-03-13*
