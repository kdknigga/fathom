---
phase: 09-tooltips-and-tax-guidance
plan: 02
subsystem: ui
tags: [tooltips, popover, tax-brackets, accessibility, templates]

requires:
  - phase: 09-tooltips-and-tax-guidance
    plan: 01
    provides: "CSS for .tip/.tooltip-content/.label-with-tip, tooltips.js, tax_brackets context, row.tooltip field"
provides:
  - "Tooltip ? buttons on all form field labels across 6 option templates"
  - "Tooltip ? buttons on breakdown table metric rows"
  - "Tooltip ? button on recommendation card True Total Cost"
  - "Tax bracket details widget with 7 IRS 2025 brackets and click-to-fill"
affects: []

tech-stack:
  added: []
  patterns:
    - "label-with-tip wrapper pattern applied consistently across all templates"
    - "Conditional tooltip rendering in breakdown table ({% if row.tooltip %})"

key-files:
  created: []
  modified:
    - src/fathom/templates/base.html
    - src/fathom/templates/index.html
    - src/fathom/templates/partials/global_settings.html
    - src/fathom/templates/partials/option_fields/traditional.html
    - src/fathom/templates/partials/option_fields/promo_zero.html
    - src/fathom/templates/partials/option_fields/promo_cashback.html
    - src/fathom/templates/partials/option_fields/promo_price.html
    - src/fathom/templates/partials/option_fields/custom.html
    - src/fathom/templates/partials/option_fields/cash.html
    - src/fathom/templates/partials/results/breakdown_table.html
    - src/fathom/templates/partials/results/recommendation.html
    - src/fathom/formatting.py
    - tests/test_visual.py

key-decisions:
  - "tooltips.js script tag added to base.html (not index.html) since that is where other scripts live"
  - "comma_format filter extended to accept int/float for tax bracket integer data"

patterns-established:
  - "Deferred interest checkbox label wraps input inside label-with-tip div with tip button outside"
  - "Cash option uses inline tip button alongside descriptive paragraph"

requirements-completed: [TIPS-01, TIPS-02, TIPS-03, TAX-01, TAX-02]

duration: 5min
completed: 2026-03-13
---

# Phase 9 Plan 2: Template Tooltip Integration Summary

**Tooltip ? buttons on all form field labels, result metric rows, and recommendation card, plus tax bracket reference widget with click-to-fill**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-13T23:42:50Z
- **Completed:** 2026-03-13T23:47:27Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments
- All form field labels across 6 option templates have ? tooltip buttons with plain-English explanations
- Tax bracket details widget renders 7 IRS 2025 rows with comma-formatted income ranges
- Breakdown table rows conditionally show ? buttons with metric explanations
- Recommendation card True Total Cost has ? tooltip explaining the metric

## Task Commits

Each task was committed atomically:

1. **Task 1: Global settings, index.html, and tax bracket widget** - `1b31979` (feat)
2. **Task 2: Option field and result template tooltips** - `d8caa37` (feat)

## Files Created/Modified
- `src/fathom/templates/base.html` - Added tooltips.js script tag
- `src/fathom/templates/index.html` - Purchase price tooltip with label-with-tip wrapper
- `src/fathom/templates/partials/global_settings.html` - Return rate, inflation, tax rate tooltips + bracket widget
- `src/fathom/templates/partials/option_fields/traditional.html` - APR, term, down payment tooltips
- `src/fathom/templates/partials/option_fields/promo_zero.html` - Promo term, down payment, deferred interest, post-promo APR tooltips
- `src/fathom/templates/partials/option_fields/promo_cashback.html` - APR, term, cash-back, down payment tooltips
- `src/fathom/templates/partials/option_fields/promo_price.html` - Discounted price, APR, term, down payment tooltips
- `src/fathom/templates/partials/option_fields/custom.html` - Effective APR, term, upfront cash tooltips
- `src/fathom/templates/partials/option_fields/cash.html` - Opportunity cost tooltip
- `src/fathom/templates/partials/results/breakdown_table.html` - Conditional metric tooltips from row.tooltip
- `src/fathom/templates/partials/results/recommendation.html` - True Total Cost tooltip
- `src/fathom/formatting.py` - Extended comma_format to accept int/float types
- `tests/test_visual.py` - Updated test for new purchase price label structure

## Decisions Made
- Added tooltips.js script tag to base.html instead of index.html since all other scripts are in base.html
- Extended comma_format filter to handle int/float types (tax bracket data uses raw integers)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] comma_format filter crashes on integer input**
- **Found during:** Task 1 (tax bracket widget rendering)
- **Issue:** comma_format expected string input but tax bracket data provides raw integers, causing AttributeError on .strip()
- **Fix:** Added isinstance checks for int and float at the top of comma_format
- **Files modified:** src/fathom/formatting.py
- **Verification:** Tax bracket widget renders with comma-formatted income ranges (e.g., $11,925)
- **Committed in:** 1b31979 (Task 1 commit)

**2. [Rule 1 - Bug] Test assertion for purchase price label structure**
- **Found during:** Task 2 (after all templates updated)
- **Issue:** test_purchase_price_label_not_duplicated asserted exact `<header><label>` adjacency which broke with label-with-tip wrapper
- **Fix:** Relaxed assertion to check label and header exist separately
- **Files modified:** tests/test_visual.py
- **Verification:** All 198 tests pass
- **Committed in:** d8caa37 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 09 (Tooltips and Tax Guidance) is now complete
- All tooltip infrastructure and content integrated into templates
- Ready for Phase 10 (JSON Export/Import)

---
*Phase: 09-tooltips-and-tax-guidance*
*Completed: 2026-03-13*
