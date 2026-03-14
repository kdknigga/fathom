---
phase: quick
plan: 2
subsystem: ui/detail-table
tags: [ux, conditional-rendering, jinja2]
dependency_graph:
  requires: []
  provides: [conditional-inflation-tax-columns]
  affects: [detailed_table.html, routes.py]
tech_stack:
  added: []
  patterns: [jinja2-conditional-columns]
key_files:
  created: []
  modified:
    - src/fathom/routes.py
    - src/fathom/templates/partials/results/detailed_table.html
decisions:
  - Used same conditional pattern as detailed_breakdown.html for consistency
metrics:
  duration: 5min
  completed: "2026-03-14T12:14:00Z"
---

# Quick Task 2: Hide Inflation/Tax Columns When Disabled — Summary

Conditional rendering of inflation and tax columns in the detailed period breakdown table, eliminating confusing $0.00 columns when features are disabled.

## What Changed

### routes.py
- Added `global_settings=settings` kwarg to the `detail_tab` endpoint's `render_template` call, enabling the detail table template to check feature flags.

### detailed_table.html
- Wrapped all `col-inflation` elements (th/td in thead, tbody, tfoot for both promo and non-promo branches) in `{% if global_settings and global_settings.inflation_enabled %}` conditionals.
- Wrapped all `col-tax` elements similarly with `{% if global_settings and global_settings.tax_enabled %}`.
- Toggle checkboxes in `detailed_breakdown.html` were already conditionally rendered (no change needed).

## Verification Results

Playwright browser automation confirmed all 12 checks passing:

| Test | Checks | Result |
|------|--------|--------|
| Default (both disabled) | No col-inflation, no col-tax, no toggles | PASS (5/5) |
| Inflation enabled | col-inflation present, toggle visible, no col-tax | PASS (3/3) |
| Tax enabled | col-tax present, toggle visible | PASS (2/2) |
| HTMX tab switch | Both columns persist after tab switch | PASS (2/2) |

## Deviations from Plan

None -- plan executed exactly as written.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | cf662ff | Hide inflation/tax columns when features disabled |
| 2 | (verification only) | Playwright browser verification |

## Self-Check: PASSED
