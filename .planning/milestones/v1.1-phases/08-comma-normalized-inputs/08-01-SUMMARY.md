---
phase: 08-comma-normalized-inputs
plan: 01
subsystem: ui
tags: [jinja, decimal, form-parsing, formatting, htmx]

# Dependency graph
requires:
  - phase: 04-form-validation
    provides: Pydantic form validation with _try_decimal and _to_money
provides:
  - Server-side comma/dollar stripping in all Decimal parsing functions
  - comma_format Jinja filter for rendering comma-separated monetary values
  - data-monetary attribute on all 8 monetary input fields
  - Cleaned purchase_price validator return for safe downstream Decimal()
affects: [08-comma-normalized-inputs]

# Tech tracking
tech-stack:
  added: []
  patterns: [_clean_monetary helper for consistent formatting strip, Jinja filter registration in create_app]

key-files:
  created: [src/fathom/formatting.py]
  modified: [src/fathom/forms.py, src/fathom/app.py, src/fathom/templates/index.html, src/fathom/templates/partials/option_fields/traditional.html, src/fathom/templates/partials/option_fields/promo_zero.html, src/fathom/templates/partials/option_fields/promo_cashback.html, src/fathom/templates/partials/option_fields/promo_price.html, src/fathom/templates/partials/option_fields/custom.html, tests/test_forms.py, tests/test_routes.py]

key-decisions:
  - "Used _clean_monetary helper to DRY the strip pattern across _try_decimal, _to_money, _to_rate, and validate_purchase_price"
  - "comma_format strips then re-formats for idempotency (already-formatted input passes through correctly)"

patterns-established:
  - "_clean_monetary(value) for stripping $, commas, spaces from monetary strings"
  - "data-monetary attribute marks monetary inputs for JS enhancement in Plan 02"

requirements-completed: [INPUT-01, INPUT-02, INPUT-03]

# Metrics
duration: 4min
completed: 2026-03-13
---

# Phase 08 Plan 01: Server-Side Comma Handling Summary

**Server-side comma/dollar stripping in Decimal parsing with comma_format Jinja filter on all 8 monetary input fields**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-13T21:08:41Z
- **Completed:** 2026-03-13T21:13:00Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- _try_decimal, _to_money, and _to_rate strip $, commas, and spaces before Decimal conversion
- FormInput.validate_purchase_price returns cleaned string so downstream Decimal() never sees commas
- New formatting.py with comma_format that preserves trailing decimal zeros and is idempotent
- All 8 monetary input fields across 6 templates have data-monetary attribute and |comma filter
- 198 tests pass (16 new comma tests + 3 new route tests)

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests for comma handling** - `362c533` (test)
2. **Task 1 GREEN: Implement comma stripping and comma_format** - `5be3e33` (feat)
3. **Task 2: Template updates with |comma and data-monetary** - `529923d` (feat)

_Note: TDD task had RED and GREEN commits_

## Files Created/Modified
- `src/fathom/formatting.py` - New comma_format Jinja filter function
- `src/fathom/forms.py` - _try_decimal, _to_money, _to_rate strip formatting chars; _clean_monetary helper; purchase_price validator returns cleaned string
- `src/fathom/app.py` - Jinja "comma" filter registration
- `src/fathom/templates/index.html` - purchase_price input with |comma and data-monetary
- `src/fathom/templates/partials/option_fields/traditional.html` - down_payment with |comma and data-monetary
- `src/fathom/templates/partials/option_fields/promo_zero.html` - down_payment with |comma and data-monetary
- `src/fathom/templates/partials/option_fields/promo_cashback.html` - cash_back_amount and down_payment with |comma and data-monetary
- `src/fathom/templates/partials/option_fields/promo_price.html` - discounted_price and down_payment with |comma and data-monetary
- `src/fathom/templates/partials/option_fields/custom.html` - down_payment with |comma and data-monetary
- `tests/test_forms.py` - 16 new tests for comma handling
- `tests/test_routes.py` - 3 new tests for comma-formatted rendering

## Decisions Made
- Used _clean_monetary helper to DRY the strip pattern across all parsing functions
- comma_format strips then re-formats for idempotency (already-formatted input passes through correctly)
- Preserved trailing decimal zeros by splitting on "." and formatting integer part only

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Server-side comma handling complete, ready for Plan 02 (client-side JS formatting)
- data-monetary attributes in place for JS to target monetary input fields

---
*Phase: 08-comma-normalized-inputs*
*Completed: 2026-03-13*
