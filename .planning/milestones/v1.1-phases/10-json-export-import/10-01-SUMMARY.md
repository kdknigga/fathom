---
phase: 10-json-export-import
plan: 01
subsystem: ui
tags: [json, export, import, file-download, file-upload, pydantic]

# Dependency graph
requires:
  - phase: 09-tooltips
    provides: completed form UI with tooltips and tax guidance
provides:
  - POST /export route returning downloadable JSON file
  - POST /import route with Pydantic validation and form repopulation
  - form_data_to_export_dict helper with version field
  - Export and Import buttons in template
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "form_data_to_export_dict wraps extract_form_data output with version"
    - "Import reuses FormInput.model_validate for field-level validation"
    - "Structural errors (bad JSON) vs field errors (invalid values) use separate display paths"

key-files:
  created: []
  modified:
    - src/fathom/forms.py
    - src/fathom/routes.py
    - src/fathom/templates/index.html
    - tests/test_forms.py
    - tests/test_routes.py

key-decisions:
  - "Used formaction attribute on Export button to override HTMX form action"
  - "Used hx-disable on Export button to prevent HTMX interception of file download"
  - "Used tuple variable for except clause to maintain Python 3.12 pre-commit hook compatibility"

patterns-established:
  - "File download via Response with Content-Disposition attachment header"
  - "File upload via separate form with hidden file input and auto-submit on change"

requirements-completed: [DATA-01, DATA-02, DATA-03]

# Metrics
duration: 6min
completed: 2026-03-14
---

# Phase 10 Plan 01: JSON Export/Import Summary

**Export/import routes with versioned JSON, Pydantic validation on import, and round-trip fidelity for all form inputs**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-14T01:53:03Z
- **Completed:** 2026-03-14T01:58:36Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- POST /export returns downloadable fathom-YYYY-MM-DD.json with version:1 field and all form inputs
- POST /import validates JSON via Pydantic, shows structural errors for bad JSON and inline field errors for invalid values
- Export-then-import round-trip produces identical form state
- Export and Import buttons added to template with proper HTMX isolation

## Task Commits

Each task was committed atomically:

1. **Task 1: Export helper, export/import routes, and tests (TDD)**
   - `9f59cf2` (test: RED - failing tests for export/import)
   - `8b5bd1c` (feat: GREEN - implement routes and helpers)
2. **Task 2: Add Export and Import buttons to template** - `92de4e4` (feat)

## Files Created/Modified
- `src/fathom/forms.py` - Added form_data_to_export_dict helper
- `src/fathom/routes.py` - Added POST /export and POST /import routes with _render_import_error helper
- `src/fathom/templates/index.html` - Added Export button (formaction), Import form (file picker), import_error display
- `tests/test_forms.py` - Added TestExportDict class (3 tests)
- `tests/test_routes.py` - Added TestExport, TestImport, TestImportErrors, TestImportRoundTrip classes (11 tests)

## Decisions Made
- Used `formaction="/export"` with `hx-disable` attribute on Export button to bypass HTMX interception for file download
- Used tuple variable `_json_parse_errors = (json.JSONDecodeError, UnicodeDecodeError)` in except clause for Python 3.12 pre-commit hook compatibility (Python 3.14 runtime supports bare comma syntax but hooks run 3.12)
- Import form uses hidden file input with `onchange="this.form.submit()"` for clean UX

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Python 3.12 pre-commit hook incompatibility with except syntax**
- **Found during:** Task 1 (GREEN phase commit)
- **Issue:** Ruff formatter targeting py314 removed parentheses from `except (JSONDecodeError, UnicodeDecodeError):` to bare comma syntax, which Python 3.12 pre-commit hooks reject as SyntaxError
- **Fix:** Used tuple variable `_json_parse_errors = (...)` and `except _json_parse_errors:` to avoid formatter interference
- **Files modified:** src/fathom/routes.py
- **Committed in:** 8b5bd1c

**2. [Rule 3 - Blocking] Template import_error display needed for test verification**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Tests for import error display required template to render import_error, but Task 2 was planned for template changes
- **Fix:** Added minimal import_error display block to template in Task 1 (refined in Task 2)
- **Files modified:** src/fathom/templates/index.html
- **Committed in:** 8b5bd1c

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes necessary for test execution and commit flow. No scope creep.

## Issues Encountered
None beyond the deviations documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Export/import fully functional with all quality gates passing
- Ready for Phase 11 (Period Breakdown)

---
*Phase: 10-json-export-import*
*Completed: 2026-03-14*
