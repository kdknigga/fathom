# Phase 10: JSON Export/Import - Research

**Researched:** 2026-03-13
**Domain:** Flask file download/upload, JSON serialization, Pydantic validation
**Confidence:** HIGH

## Summary

This phase adds two server-side routes: one to export current form inputs as a downloadable JSON file, and one to import a previously exported JSON file to repopulate the form. The implementation is straightforward because the existing codebase already has all the building blocks: `extract_form_data()` produces a JSON-friendly dict, `FormInput.model_validate()` validates arbitrary dicts through Pydantic, `pydantic_errors_to_dict()` converts errors for template display, and `_build_template_context()` renders form state back into the template.

Flask's built-in `Response` class handles file downloads (setting `Content-Disposition: attachment` and `application/json` content type). Flask's `request.files` handles file uploads via multipart form data. No new dependencies are needed -- everything is achievable with Flask + Pydantic + Python's `json` standard library.

**Primary recommendation:** Add two new routes (`POST /export`, `POST /import`) to `routes.py`, a small `form_data_to_export_dict()` helper in `forms.py` for clean JSON conversion (booleans, version field), and Export/Import buttons in `index.html`. Reuse existing validation pipeline entirely.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Export contains **form inputs only** -- no calculated results
- Export available **anytime** -- does not require successful calculation first
- Two separate buttons: **Export** and **Import**, placed below the form near the Compare button
- Export triggers file download via server-side route (POST form data -> server builds JSON -> returns as file attachment)
- Import **replaces all current form inputs silently** -- no confirmation dialog
- Upload via **standard file picker button only** -- no drag-and-drop
- After successful import, **populate the form only** -- user must click Compare manually
- Validation errors displayed **inline with form fields** -- same error display as regular form validation
- Import submits file to server route, validates via `FormInput` Pydantic model, re-renders form with populated values (or errors)
- Downloaded filename: **`fathom-YYYY-MM-DD.json`**
- JSON includes top-level **`version`** field (e.g., `1`)
- JSON is **compact (minified)**
- Boolean settings export as **native JSON booleans**

### Claude's Discretion
- Exact JSON key naming (match form field names vs. cleaner aliases)
- Whether version migration logic is needed now or just the version field
- Button styling (primary vs. secondary vs. outline)
- Import file size limit (if any)
- Error message wording for invalid JSON structure vs. invalid field values

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DATA-01 | User can click "Export" to download current form inputs as `.json` file | Export route using `extract_form_data()` -> JSON serialization -> Flask Response with Content-Disposition attachment |
| DATA-02 | User can upload a previously exported `.json` file to restore all form inputs | Import route using `request.files` -> JSON parse -> `FormInput.model_validate()` -> `_build_template_context()` to repopulate form |
| DATA-03 | Imported JSON validated through same Pydantic models as form submission -- invalid files show error | Reuse `FormInput.model_validate()` + `pydantic_errors_to_dict()` for field-level errors; catch `json.JSONDecodeError` for malformed files |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Flask | >=3.1.3 | Routes, request handling, Response | Already in project |
| Pydantic | >=2.12.5 | Import validation via `FormInput` model | Already in project |
| json (stdlib) | N/A | JSON serialization/deserialization | No dependency needed |
| datetime (stdlib) | N/A | Date-stamped filename generation | No dependency needed |

### Supporting
No additional libraries needed. Everything required is already available.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Flask Response with headers | `flask.send_file` with BytesIO | send_file is heavier; raw Response is simpler for small JSON payloads |
| Manual JSON parse | `FormInput.model_validate_json()` | Pydantic's `model_validate_json` parses JSON directly but we need to extract version field first; two-step parse is cleaner |

## Architecture Patterns

### Recommended Project Structure
```
src/fathom/
├── forms.py          # Add form_data_to_export_dict() helper
├── routes.py         # Add POST /export and POST /import routes
└── templates/
    └── index.html    # Add Export/Import buttons near Compare button
```

No new files needed. All changes fit within existing modules.

### Pattern 1: Export Route (POST /export)
**What:** Receives form data via POST (same as `/compare`), extracts it using `extract_form_data()`, converts to clean JSON with version field and native booleans, returns as file download.
**When to use:** When user clicks Export button.
**Example:**
```python
# Source: Flask documentation + existing codebase patterns
import json
from datetime import date
from flask import Response

@bp.route("/export", methods=["POST"])
def export_data():
    """Export current form inputs as a downloadable JSON file."""
    parsed = extract_form_data(request.form)
    export = form_data_to_export_dict(parsed)
    json_bytes = json.dumps(export, separators=(",", ":")).encode("utf-8")
    filename = f"fathom-{date.today().isoformat()}.json"
    return Response(
        json_bytes,
        mimetype="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
```

### Pattern 2: Import Route (POST /import)
**What:** Receives uploaded file via multipart POST, parses JSON, validates through `FormInput.model_validate()`, re-renders full page with populated form (or errors).
**When to use:** When user selects a file via the Import file picker.
**Example:**
```python
@bp.route("/import", methods=["POST"])
def import_data():
    """Import form inputs from a previously exported JSON file."""
    file = request.files.get("import_file")
    if not file or not file.filename:
        # Re-render with error
        ...
    try:
        data = json.load(file.stream)
    except (json.JSONDecodeError, UnicodeDecodeError):
        # Re-render with structural error message
        ...
    # Strip version field, validate rest through Pydantic
    data.pop("version", None)
    try:
        FormInput.model_validate(data)
    except ValidationError as exc:
        errors = pydantic_errors_to_dict(exc)
        ctx = _build_template_context(data, errors)
        ...
    # Success: render form with imported values
    ctx = _build_template_context(data, errors={})
    ...
```

### Pattern 3: Export Dict Conversion
**What:** Convert `extract_form_data()` output to clean export format with version field and native JSON booleans.
**When to use:** In the export route before JSON serialization.
**Example:**
```python
def form_data_to_export_dict(parsed: dict) -> dict:
    """Convert parsed form data to a clean export dict."""
    export = {
        "version": 1,
        "purchase_price": parsed["purchase_price"],
        "options": parsed["options"],
        "settings": parsed["settings"],
    }
    # Booleans are already native Python bools from extract_form_data()
    # (checkbox handling: `key in form_data` returns bool)
    return export
```

### Pattern 4: Import Button (HTML form with file input)
**What:** A separate `<form>` with `enctype="multipart/form-data"` containing a file input that auto-submits on selection.
**When to use:** The import button cannot be inside the main comparison form since it needs different enctype and action.
**Example:**
```html
<!-- Export: submits main form data to /export -->
<button type="submit" formaction="/export" class="outline">Export</button>

<!-- Import: separate form with file upload -->
<form method="post" action="/import" enctype="multipart/form-data" id="import-form">
  <label for="import-file" role="button" class="outline secondary">Import</label>
  <input type="file" id="import-file" name="import_file" accept=".json"
         style="display:none" onchange="this.form.submit()">
</form>
```

### Anti-Patterns to Avoid
- **Client-side JSON parsing:** CLAUDE.md explicitly forbids duplicating logic in client-side JS. All validation must happen server-side.
- **Using `formaction` for import:** The import needs `enctype="multipart/form-data"` which conflicts with the main form. Use a separate form element.
- **Pretty-printing JSON:** User decision specifies compact/minified output. Use `separators=(",", ":")`.
- **Including calculated results in export:** User decision explicitly limits export to form inputs only.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Form input validation | Custom JSON schema validator | `FormInput.model_validate()` | Already validates all fields with range checks, type constraints, cross-field validation |
| Error display formatting | Custom error message builder | `pydantic_errors_to_dict()` | Already converts Pydantic errors to template-compatible format |
| Form state extraction | Manual JSON field mapping | `extract_form_data()` | Already handles option indexing, checkbox booleans, settings extraction |
| Template repopulation | Custom form rendering | `_build_template_context()` | Already maps parsed data to template context with option templates |

**Key insight:** The existing form processing pipeline (`extract_form_data` -> `FormInput.model_validate` -> `_build_template_context`) is the exact same pipeline needed for both export and import, just with different input sources (form POST vs. JSON file).

## Common Pitfalls

### Pitfall 1: Export Button Inside Main Form Triggers Compare
**What goes wrong:** If Export is a regular button inside the `<form>` that posts to `/compare`, clicking it triggers the compare flow instead of export.
**Why it happens:** Buttons inside a form submit to the form's action by default.
**How to avoid:** Use `formaction="/export"` on the Export button to override the form action. This is valid HTML and keeps the button inside the main form (so all form data is submitted). The Export button should also have `formnovalidate` to skip HTML5 validation and `hx-disable` or no HTMX attributes so it does a regular form POST (file download).
**Warning signs:** Export triggers comparison results instead of file download.

### Pitfall 2: Import Form Needs multipart/form-data Enctype
**What goes wrong:** File upload arrives empty or missing.
**Why it happens:** The main form uses `application/x-www-form-urlencoded` (default). File uploads require `multipart/form-data`.
**How to avoid:** Put the import file input in a separate `<form>` element with `enctype="multipart/form-data"`.
**Warning signs:** `request.files.get("import_file")` returns None.

### Pitfall 3: HTMX Intercepting Export/Import Requests
**What goes wrong:** HTMX intercepts the export POST and tries to swap the response into the DOM instead of triggering a file download.
**Why it happens:** The main form has `hx-post="/compare"` which HTMX uses. Buttons with `formaction` inside an HTMX-enabled form may still be intercepted.
**How to avoid:** Add `hx-disable` attribute on the Export button (or ensure it has no `hx-*` attributes that trigger HTMX). For import, using a separate form without HTMX attributes avoids this entirely. Alternatively, set `hx-boost="false"` on the export button.
**Warning signs:** Export shows JSON text in the page instead of downloading a file.

### Pitfall 4: JSON Key Mismatch Between Export and Import
**What goes wrong:** Exported JSON keys don't match what `FormInput.model_validate()` expects.
**Why it happens:** `extract_form_data()` produces keys like `purchase_price`, `options`, `settings` -- but if export uses different key names, import validation fails.
**How to avoid:** Use the exact same key structure that `FormInput` expects. Since `extract_form_data()` already produces a dict compatible with `FormInput.model_validate()`, use it directly (with version field added).
**Warning signs:** Valid exports fail on re-import with "field required" errors.

### Pitfall 5: Missing purchase_price in OptionInput During Import
**What goes wrong:** Import validation fails because `OptionInput` expects a `purchase_price` field (for cross-field validation like down_payment < purchase_price).
**Why it happens:** `parse_form_data()` injects `purchase_price` into each option dict (`opt["purchase_price"] = purchase_price`), but the exported JSON from `extract_form_data()` does NOT include `purchase_price` in each option.
**How to avoid:** During import, before calling `FormInput.model_validate()`, inject `purchase_price` into each option dict -- same as `parse_form_data()` does.
**Warning signs:** Import fails with Pydantic errors about purchase_price on options.

### Pitfall 6: Checkbox/Boolean Type Mismatch
**What goes wrong:** Exported booleans (`true`/`false`) don't match what Pydantic expects, or form-native strings ("on"/"") cause type confusion.
**Why it happens:** `extract_form_data()` already returns native Python bools for checkbox fields. JSON serializes these as `true`/`false`. Pydantic accepts both, so this should work. But if intermediate processing converts bools to strings, it breaks.
**How to avoid:** Ensure the export-to-import round trip preserves Python bool types. `json.dumps(True)` -> `"true"` -> `json.loads("true")` -> `True`. No conversion needed.
**Warning signs:** "inflation_enabled" appears as string "true" instead of bool.

## Code Examples

### Complete Export Helper
```python
# forms.py addition
def form_data_to_export_dict(parsed: dict) -> dict:
    """
    Convert parsed form data to a versioned export dict.

    Ensures booleans are native Python bools (not strings) and adds
    a version field for forward compatibility.

    Args:
        parsed: Output from extract_form_data().

    Returns:
        Dict ready for JSON serialization.
    """
    return {
        "version": 1,
        "purchase_price": parsed["purchase_price"],
        "options": parsed["options"],
        "settings": parsed["settings"],
    }
```

### Complete Import Validation Flow
```python
# routes.py addition
def _validate_import_data(data: dict) -> tuple[dict | None, dict[str, str]]:
    """
    Validate imported JSON data through FormInput model.

    Returns (parsed_data, errors) tuple. On success, errors is empty.
    On failure, parsed_data contains the raw data for form repopulation.
    """
    # Strip metadata fields
    data.pop("version", None)

    # Inject purchase_price into each option (required by OptionInput)
    purchase_price = data.get("purchase_price", "")
    for opt in data.get("options", []):
        opt["purchase_price"] = purchase_price

    try:
        FormInput.model_validate(data)
    except ValidationError as exc:
        return data, pydantic_errors_to_dict(exc)

    return data, {}
```

### Export Button (No HTMX Interference)
```html
<!-- Inside the main form, next to Compare button -->
<button type="submit" formaction="/export" formnovalidate
        class="outline" hx-disable>
  Export
</button>
```

The `formaction` overrides the form's action. `formnovalidate` skips HTML5 validation. `hx-disable` prevents HTMX from intercepting (HTMX attribute that disables HTMX processing for this element). Note: the exact HTMX attribute may be `data-hx-disable` -- verify during implementation.

### Hidden File Input for Import
```html
<!-- Separate form outside the main comparison form -->
<form method="post" action="/import" enctype="multipart/form-data">
  <label for="import-file" role="button" class="outline secondary"
         tabindex="0">Import</label>
  <input type="file" id="import-file" name="import_file"
         accept=".json,application/json" hidden
         onchange="this.form.submit()">
</form>
```

## Discretion Recommendations

### JSON Key Naming
**Recommendation:** Match form field names exactly. `extract_form_data()` already produces keys that `FormInput.model_validate()` accepts. Using the same keys guarantees round-trip fidelity without any mapping layer.

### Version Migration Logic
**Recommendation:** Just include the `version: 1` field for now. No migration code needed until a version 2 format actually exists. The import route should log/ignore the version field.

### Button Styling
**Recommendation:** Export as `outline` (secondary action, same row as Compare). Import as `outline secondary` (separate form, visually distinct from Export). Both should be smaller/less prominent than the primary Compare button.

### Import File Size Limit
**Recommendation:** Set a 64KB limit via `request.content_length` check or Flask's `MAX_CONTENT_LENGTH`. Fathom forms have at most 4 options with ~15 fields each -- the JSON will be well under 1KB. A 64KB limit prevents abuse while being generous.

### Error Messages
**Recommendation:** Two categories:
1. **Structural errors** (not valid JSON, no file selected, file too large): "The selected file is not a valid Fathom export. Please select a .json file previously exported from Fathom."
2. **Field validation errors** (valid JSON but field values fail Pydantic): Display inline with form fields using existing error rendering, same as form submission errors. The form should be populated with the imported values so user can see and fix them.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `send_file()` for downloads | `Response()` with headers | Always available | Simpler for small payloads, no temp file needed |
| Custom validation | Pydantic `model_validate()` | Pydantic v2 | Already in use; accepts plain dicts directly |
| `formaction` HTML attribute | Same | HTML5 | Widely supported, lets Export button stay inside main form |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/test_routes.py -x -q` |
| Full suite command | `uv run pytest -x -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01 | POST /export returns JSON file with Content-Disposition attachment | integration | `uv run pytest tests/test_routes.py::TestExport -x` | No -- Wave 0 |
| DATA-01 | Export JSON contains version field and correct structure | unit | `uv run pytest tests/test_forms.py::TestExportDict -x` | No -- Wave 0 |
| DATA-01 | Export filename follows fathom-YYYY-MM-DD.json pattern | integration | `uv run pytest tests/test_routes.py::TestExport -x` | No -- Wave 0 |
| DATA-02 | POST /import with valid JSON repopulates all form fields | integration | `uv run pytest tests/test_routes.py::TestImport -x` | No -- Wave 0 |
| DATA-02 | Round-trip: export then import produces identical form state | integration | `uv run pytest tests/test_routes.py::TestImportRoundTrip -x` | No -- Wave 0 |
| DATA-03 | Import of malformed JSON shows structural error message | integration | `uv run pytest tests/test_routes.py::TestImportErrors -x` | No -- Wave 0 |
| DATA-03 | Import of invalid field values shows inline errors | integration | `uv run pytest tests/test_routes.py::TestImportErrors -x` | No -- Wave 0 |
| DATA-03 | Import with no file selected shows error | integration | `uv run pytest tests/test_routes.py::TestImportErrors -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_routes.py tests/test_forms.py -x -q`
- **Per wave merge:** `uv run pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_routes.py::TestExport` -- covers DATA-01 (export route tests)
- [ ] `tests/test_routes.py::TestImport` -- covers DATA-02 (import route tests)
- [ ] `tests/test_routes.py::TestImportErrors` -- covers DATA-03 (error handling tests)
- [ ] `tests/test_routes.py::TestImportRoundTrip` -- covers DATA-02 round-trip fidelity
- [ ] `tests/test_forms.py::TestExportDict` -- covers DATA-01 (export dict helper unit tests)

### Playwright Verification
Per CLAUDE.md, all browser-based verification must use Playwright MCP:
- Verify Export button triggers file download (not DOM swap)
- Verify Import file picker opens and form submits on file selection
- Verify imported values appear in form fields
- Verify invalid import shows inline error messages

## Open Questions

1. **HTMX `hx-disable` attribute name**
   - What we know: HTMX has a way to prevent processing on specific elements
   - What's unclear: The exact attribute name -- could be `hx-disable`, `data-hx-disable`, or may need `hx-boost="false"`
   - Recommendation: Test during implementation; if `hx-disable` doesn't work, wrap the export button to avoid HTMX inheritance

2. **Import full-page re-render vs. HTMX partial**
   - What we know: Import changes ALL form fields, so a full page re-render is cleaner than partial swap
   - What's unclear: Whether to return full HTML page or use HTMX swap of the entire form
   - Recommendation: Full page render (non-HTMX POST) is simpler and avoids partial-state issues. The import form has no `hx-*` attributes, so it will do a regular form POST naturally.

## Sources

### Primary (HIGH confidence)
- Existing codebase: `forms.py`, `routes.py`, `index.html` -- direct code inspection
- Flask documentation (from training data) -- Response, request.files, Content-Disposition patterns

### Secondary (MEDIUM confidence)
- HTMX `hx-disable` behavior -- needs implementation-time verification
- `formaction` + `formnovalidate` HTML5 attributes -- well-established standard

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies needed, all patterns verified in existing codebase
- Architecture: HIGH -- directly extends existing form processing pipeline with minimal new code
- Pitfalls: HIGH -- identified from code inspection (especially the purchase_price injection issue in Pitfall 5)

**Research date:** 2026-03-13
**Valid until:** 2026-04-13 (stable domain, no fast-moving dependencies)
