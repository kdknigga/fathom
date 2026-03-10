---
phase: 02-web-layer-and-input-forms
plan: 01
subsystem: ui
tags: [flask, jinja2, pico-css, htmx, ssr, forms]

requires:
  - phase: 01-calculation-engine
    provides: OptionType enum, FinancingOption/GlobalSettings dataclasses
provides:
  - Flask app factory with create_app()
  - Routes blueprint with GET / serving full form page
  - Base template with Pico CSS and HTMX CDN
  - All 6 option type field templates
  - Global settings collapsible section
  - Two-column responsive grid layout
  - Flask test client fixtures in conftest.py
affects: [02-02, 02-03, 03-results-display]

tech-stack:
  added: [flask, jinja2, pico-css, htmx]
  patterns: [app-factory, blueprint-routes, jinja2-includes, pico-grid-layout]

key-files:
  created:
    - src/fathom/app.py
    - src/fathom/routes.py
    - src/fathom/templates/base.html
    - src/fathom/templates/index.html
    - src/fathom/templates/partials/option_card.html
    - src/fathom/templates/partials/option_list.html
    - src/fathom/templates/partials/option_fields/cash.html
    - src/fathom/templates/partials/option_fields/traditional.html
    - src/fathom/templates/partials/option_fields/promo_zero.html
    - src/fathom/templates/partials/option_fields/promo_cashback.html
    - src/fathom/templates/partials/option_fields/promo_price.html
    - src/fathom/templates/partials/option_fields/custom.html
    - src/fathom/templates/partials/global_settings.html
    - src/fathom/static/style.css
  modified:
    - pyproject.toml
    - uv.lock
    - src/fathom/__init__.py
    - tests/conftest.py

key-decisions:
  - "Used os.environ.get for SECRET_KEY to avoid hardcoded password lint warning (S105)"
  - "Visually-hidden labels on option card header inputs for accessibility without visual clutter"
  - "Option template path passed as opt.template string for dynamic Jinja2 include"

patterns-established:
  - "App factory pattern: create_app() in app.py returns configured Flask instance"
  - "Blueprint routes: bp in routes.py registered via register_blueprint"
  - "Indexed form fields: options[idx][fieldname] pattern for multi-option forms"
  - "Dynamic template includes: opt.template path string for type-specific field rendering"

requirements-completed: [FORM-01, FORM-05, FORM-06, FORM-07, OPTY-01, OPTY-02, OPTY-03, OPTY-04, OPTY-05, OPTY-06, A11Y-01, LYOT-01, LYOT-02, LYOT-03]

duration: 4min
completed: 2026-03-10
---

# Phase 2 Plan 1: Flask App and Form Templates Summary

**Flask app factory with Pico CSS/HTMX base, 6 option type field templates, two-column responsive layout, and consumer-friendly labeled form inputs**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-10T20:17:52Z
- **Completed:** 2026-03-10T20:22:00Z
- **Tasks:** 2
- **Files modified:** 18

## Accomplishments
- Flask app factory serving GET / with complete form UI including purchase price, 2 default option cards, and global settings
- All 6 option type field templates with correct fields per type, visible labels, error display, and consumer-friendly language
- Two-column responsive Pico grid layout with mobile sticky "View Results" anchor
- Flask test client fixtures added to conftest.py; all 24 existing tests still pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Flask app factory, routes blueprint, base template, and dependency setup** - `dff778b` (feat)
2. **Task 2: Index page, all option field templates, global settings, and responsive layout** - `33eb6de` (feat)

## Files Created/Modified
- `src/fathom/app.py` - Flask app factory with create_app()
- `src/fathom/routes.py` - Blueprint with GET / route, option type labels and template mappings
- `src/fathom/templates/base.html` - Base template with Pico CSS and HTMX CDN links
- `src/fathom/templates/index.html` - Main form page with two-column grid layout
- `src/fathom/templates/partials/option_card.html` - Option card with editable name, type dropdown, remove button
- `src/fathom/templates/partials/option_list.html` - Option loop with add button (max 4)
- `src/fathom/templates/partials/option_fields/cash.html` - Cash (no fields needed)
- `src/fathom/templates/partials/option_fields/traditional.html` - APR, term, down payment
- `src/fathom/templates/partials/option_fields/promo_zero.html` - Term, down payment, deferred interest, post-promo APR
- `src/fathom/templates/partials/option_fields/promo_cashback.html` - APR, term, cash-back amount, down payment
- `src/fathom/templates/partials/option_fields/promo_price.html` - Discounted price, APR, term, down payment
- `src/fathom/templates/partials/option_fields/custom.html` - Effective APR, term, upfront cash, description
- `src/fathom/templates/partials/global_settings.html` - Return rate presets, inflation toggle, tax toggle
- `src/fathom/static/style.css` - Error styling, sticky anchor, accessibility helpers
- `pyproject.toml` - Added flask dependency
- `uv.lock` - Updated with flask and transitive deps
- `src/fathom/__init__.py` - Updated main() to create and run Flask app
- `tests/conftest.py` - Added app and client fixtures

## Decisions Made
- Used os.environ.get for SECRET_KEY to avoid S105 hardcoded password lint warning while keeping dev default
- Applied visually-hidden class on option card header labels for accessibility without visual clutter in the grid header
- Passed template path as opt.template string in context for dynamic Jinja2 includes (simplest approach from plan options)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Ruff D213/D413 docstring style rules required multi-line docstrings to start on second line with trailing blank line after last section; fixed by reformatting all docstrings

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Complete template layer ready for Plan 02 to wire HTMX interactivity (add/remove options, type switching)
- Complete template layer ready for Plan 03 to add form processing and validation on POST /compare
- Routes module has OPTION_TYPE_LABELS and OPTION_FIELD_TEMPLATES dicts ready for reuse

---
*Phase: 02-web-layer-and-input-forms*
*Completed: 2026-03-10*
