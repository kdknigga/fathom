# Phase 10: JSON Export/Import - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can save their current form inputs to a `.json` file and restore them by uploading a previously exported file. Validation on import uses the same Pydantic models as form submission. No persistent storage, no cloud sync, no results in the export — inputs only.

</domain>

<decisions>
## Implementation Decisions

### Export content & trigger
- Export contains **form inputs only** — purchase price, option configurations, and global settings. No calculated results (those are recalculated on demand)
- Export available **anytime** — does not require a successful calculation first. User can save partial work or draft configurations
- Two separate buttons: **Export** and **Import**, placed below the form near the Compare button
- Export button triggers a file download via server-side route (POST form data → server builds JSON → returns as file attachment)

### Import flow & behavior
- Import **replaces all current form inputs silently** — no confirmation dialog. The user chose to import knowing it would replace
- Upload via **standard file picker button only** — no drag-and-drop. Simple, universally understood, works on mobile
- After successful import, **populate the form only** — user must click Compare manually. Lets them review/tweak inputs before calculating
- Validation errors displayed **inline with form fields** — same error display as regular form validation (red messages next to the fields that failed). Consistent experience
- Import submits the file to a server route, which validates via `FormInput` Pydantic model, then re-renders the form with populated values (or errors)

### File format & naming
- Downloaded filename: **`fathom-YYYY-MM-DD.json`** — date-stamped, easy to sort chronologically
- JSON includes a top-level **`version`** field (e.g., `1`) for forward compatibility. Future format changes can check version and migrate
- JSON is **compact (minified)** — no pretty-printing
- Boolean settings (inflation_enabled, tax_enabled) export as **native JSON booleans** (`true`/`false`), not form-native strings. Server converts on import

### Claude's Discretion
- Exact JSON key naming (match form field names vs. cleaner aliases)
- Whether version migration logic is needed now or just the version field
- Button styling (primary vs. secondary vs. outline)
- Import file size limit (if any)
- Error message wording for invalid JSON structure vs. invalid field values

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. The key principle is round-trip fidelity: export then import should produce an identical form state.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`FormInput` Pydantic model** (`forms.py`): Validates all form data — reuse directly for import validation (DATA-03)
- **`extract_form_data()`** (`forms.py`): Already produces a JSON-friendly nested dict from form submission — natural export source
- **`parse_form_data()`** (`forms.py`): Validates dict → `FormInput` — can validate imported JSON the same way
- **`pydantic_errors_to_dict()`** (`forms.py`): Converts Pydantic errors to template-friendly format — reuse for import error display
- **`_build_template_context()`** (`routes.py`): Builds template context from parsed form data — reuse to repopulate form after import

### Established Patterns
- All form processing flows through `parse_form_data()` → `build_domain_objects()` → engine pipeline
- Error display uses field-path dot notation (e.g., `options.0.apr`) mapped to template error containers
- HTMX partial rendering for form updates — import may need full page re-render since all fields change
- Form field naming: `purchase_price`, `options[idx][field]`, `return_preset`, etc.

### Integration Points
- **`routes.py`**: New `POST /export` route (receives form data, returns JSON file) and `POST /import` route (receives file upload, validates, re-renders form)
- **`index.html`**: Export and Import buttons near the Compare button
- **`forms.py`**: May need a `form_input_to_export_dict()` function to produce clean JSON (booleans, version field)
- **Templates**: Import re-renders the full form with all option fields populated — same flow as error re-rendering in `compare_options()`

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 10-json-export-import*
*Context gathered: 2026-03-13*
