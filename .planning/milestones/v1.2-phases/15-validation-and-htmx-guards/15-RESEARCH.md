# Phase 15: Validation and HTMX Guards - Research

**Researched:** 2026-03-15
**Domain:** Server-side form validation (Pydantic) + HTMX endpoint guards
**Confidence:** HIGH

## Summary

Phase 15 adds inflation/tax rate bounds checking and HTMX option count guards. The codebase already has well-established patterns for both concerns: `SettingsInput` has a `validate_return_rate` model validator that demonstrates the exact two-step validation pattern (non-numeric first, then bounds check), and `FormInput.validate_option_count` already enforces 2-4 at submit time. The add/remove routes use `extract_form_data` which conveniently parses option indices from raw form keys via the existing `_OPTION_INDEX_RE` regex.

The work is straightforward pattern replication. The inflation/tax validators follow `validate_return_rate` exactly. The HTMX guards add an early count check in `add_option` and `remove_option` before calling `extract_form_data`. Template changes are minimal: update input types and add error display blocks to `global_settings.html`, plus an optional warning banner slot in `option_list.html`.

**Primary recommendation:** Follow the existing `validate_return_rate` pattern for inflation/tax validation; add pre-extraction count guards to add/remove routes using the same `_OPTION_INDEX_RE` regex.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Inline errors next to inflation/tax fields using the existing `<small class="field-error">` pattern with `aria-invalid="true"` on the input
- Consistent with how APR, term, and other fields already show errors
- Exact bounds in error messages: "Inflation rate must be between 0% and 20%", "Tax rate must be between 0% and 60%"
- Separate message for non-numeric input: "Must be a number" (two-step validation like return rate)
- When toggle is OFF (inflation_enabled/tax_enabled = false), skip validation entirely -- no inline error shown for disabled fields (SC5)
- Server-side guard in `add_option`: count options from raw form keys BEFORE calling `extract_form_data`. If >= 4, return unchanged form with flash-style warning banner above options: "Maximum 4 options allowed"
- Server-side guard in `remove_option`: same approach. If <= 2, return unchanged form with banner: "Minimum 2 options required"
- Warning banner renders at top of `option_list.html` partial, disappears on next HTMX interaction (re-render clears it)
- The `/compare` submit endpoint relies on existing Pydantic `FormInput.validate_option_count` -- no duplication needed
- Change inflation_rate input to `type="number" min="0" max="20" step="0.1"`
- Change tax_rate input to `type="number" min="0" max="60" step="1"`
- Also add `type="number" min="0" max="30" step="0.01"` to the custom return rate field for consistency
- Add HTML `disabled` attribute to inflation/tax inputs when their toggle is OFF -- greys out field, prevents interaction, and excludes from form submission

### Claude's Discretion
- Exact implementation of the raw form key counting (regex pattern for option indices)
- How to wire the disabled attribute to toggle state (JS listener or HTMX swap)
- Test structure and assertion patterns for the new validation
- Warning banner styling (color, icon, animation)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| VAL-01 | Inflation rate validated to 0-20% bounds with clear error message | `SettingsInput.validate_return_rate` pattern; add `validate_inflation_rate` model validator with toggle-off bypass |
| VAL-02 | Tax rate validated to 0-60% bounds with clear error message | Same pattern as VAL-01; add `validate_tax_rate` model validator with toggle-off bypass |
| VAL-03 | HTMX add endpoint rejects adding beyond 4 options | Early count check in `add_option` route using `_OPTION_INDEX_RE` before `extract_form_data` |
| VAL-04 | HTMX remove endpoint rejects removing below 2 options | Early count check in `remove_option` route using `_OPTION_INDEX_RE` before `extract_form_data` |
| TEST-03 | Tests verify HTMX add-at-4 and remove-at-2 are rejected server-side | Flask test client POST to add/remove with boundary counts; assert option count unchanged |
| TEST-04 | Tests verify inflation/tax rate bounds reject impossible values | Pydantic unit tests + route integration tests with out-of-range values |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic | 2.x (installed) | Form validation models | Already used for all form validation in `forms.py` |
| Flask | 3.x (installed) | Route handlers, test client | Already the web framework |
| Jinja2 | 3.x (installed) | Template rendering | Already the template engine |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | (installed) | Test framework | All unit and integration tests |
| werkzeug | (installed) | `ImmutableMultiDict` for test form data | Test helpers |

No new dependencies needed. Everything required is already in the project.

## Architecture Patterns

### Pattern 1: Two-Step Model Validator (existing pattern)
**What:** Pydantic `@model_validator(mode="after")` that first checks non-numeric, then checks bounds, with field-prefixed error messages.
**When to use:** For inflation_rate and tax_rate validation, following `validate_return_rate`.
**Example (from existing code, forms.py:99-116):**
```python
@model_validator(mode="after")
def validate_return_rate(self) -> Self:
    """Validate the return rate setting."""
    custom = self.return_rate_custom
    if custom and custom.strip():
        val = _try_decimal(custom)
        if val is None:
            msg = "return_rate:Custom return rate must be a number."
            raise ValueError(msg)
        if val < 0 or val > 30:
            msg = "return_rate:Return rate must be between 0% and 30%."
            raise ValueError(msg)
    else:
        # preset validation...
    return self
```

**New validators follow this pattern exactly**, with toggle bypass:
```python
@model_validator(mode="after")
def validate_inflation_rate(self) -> Self:
    """Validate inflation rate bounds when inflation is enabled."""
    if not self.inflation_enabled:
        return self
    val = _try_decimal(self.inflation_rate)
    if val is None:
        msg = "inflation_rate:Must be a number."
        raise ValueError(msg)
    if val < 0 or val > 20:
        msg = "inflation_rate:Inflation rate must be between 0% and 20%."
        raise ValueError(msg)
    return self
```

### Pattern 2: Early Count Guard in Route (new pattern)
**What:** Count option indices from raw form keys before calling `extract_form_data`. Return unchanged form if limit hit.
**When to use:** In `add_option` and `remove_option` routes.
**Implementation approach:**
```python
@bp.route("/partials/option/add", methods=["POST"])
def add_option() -> str:
    # Count options from raw form keys BEFORE extract_form_data
    indices: set[int] = set()
    for key in request.form:
        match = _OPTION_INDEX_RE.match(key)
        if match:
            indices.add(int(match.group(1)))
    if len(indices) >= 4:
        # Return unchanged form with warning banner
        parsed = extract_form_data(request.form)
        # ... build options list, render with warning_message
        return render_template(
            "partials/option_list.html",
            options=options,
            option_types=_build_option_types(),
            errors={},
            warning_message="Maximum 4 options allowed",
        )
    # ... normal add logic
```

Note: `_OPTION_INDEX_RE` is already defined in `forms.py` and imported. For DRY, the route can either import it or use a small helper. Since `forms.py` already exports the regex module-level, importing it is cleanest.

### Pattern 3: Inline Error Display (existing template pattern)
**What:** `<small class="field-error">` with `aria-invalid="true"` on the input.
**When to use:** For inflation_rate and tax_rate error display in `global_settings.html`.
**Example (from traditional.html):**
```html
<input
  type="number" min="0" max="20" step="0.1"
  id="inflation-rate"
  name="inflation_rate"
  value="{{ settings.inflation_rate|default('3') }}"
  {% if errors.get('settings.inflation_rate') %}aria-invalid="true"{% endif %}
>
{% if errors.get('settings.inflation_rate') %}
<small class="field-error">{{ errors['settings.inflation_rate'] }}</small>
{% endif %}
```

### Pattern 4: Warning Banner (new pattern)
**What:** A dismissable/auto-clearing banner at top of `option_list.html` for option limit warnings.
**When to use:** When add/remove guard fires.
**Implementation:**
```html
{% if warning_message %}
<div role="alert" class="option-warning">
  {{ warning_message }}
</div>
{% endif %}
```
PicoCSS has built-in styling for `role="alert"` which will suffice. The banner auto-clears on the next HTMX interaction because re-renders won't pass `warning_message`.

### Pattern 5: Toggle-Disabled Fields (client-side JS)
**What:** When inflation/tax checkbox is unchecked, add `disabled` attribute to the corresponding input.
**When to use:** For inflation_rate and tax_rate inputs.
**Implementation:** Small inline JS listener on the checkbox:
```html
<input
  type="checkbox"
  name="inflation_enabled"
  value="1"
  {% if settings.inflation_enabled %}checked{% endif %}
  onchange="document.getElementById('inflation-rate').disabled = !this.checked"
>
```
Plus set initial state on page load:
```html
<input
  type="number" min="0" max="20" step="0.1"
  id="inflation-rate"
  name="inflation_rate"
  value="{{ settings.inflation_rate|default('3') }}"
  {% if not settings.inflation_enabled %}disabled{% endif %}
>
```
This is the simplest approach: `onchange` on the checkbox, initial `disabled` via Jinja conditional. No HTMX swap needed -- pure HTML + minimal JS.

### Anti-Patterns to Avoid
- **Duplicating count logic in routes:** The `_OPTION_INDEX_RE` regex is already in `forms.py`. Import it rather than redefining.
- **Validating disabled fields:** When toggle is OFF, the server must skip validation. The `disabled` attribute on the input means the browser won't send the value, but the Pydantic model has defaults (`inflation_rate: str = "3"`), so the default value would pass validation anyway. The validator must explicitly check the enabled flag first.
- **Client-only validation:** HTML5 `min`/`max` attributes are hints only. Server-side Pydantic validation is the enforcement layer. Never rely on `type="number"` alone.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Form key counting | Custom regex or string parsing | `_OPTION_INDEX_RE` from forms.py | Already exists, tested, handles edge cases |
| Error message formatting | Custom error dict builder | `pydantic_errors_to_dict` | Already handles field-prefixed messages from model validators |
| Decimal parsing | Manual string-to-number | `_try_decimal` from forms.py | Already handles $, commas, spaces, invalid input |

## Common Pitfalls

### Pitfall 1: Disabled Fields Still Have Default Values
**What goes wrong:** When inflation is disabled and the input has `disabled` attribute, the browser does not send `inflation_rate` in the form. Pydantic model defaults it to `"3"`, which would pass bounds validation.
**Why it happens:** Pydantic default values are valid, so validation passes even when the field wasn't submitted.
**How to avoid:** The validator checks `self.inflation_enabled` first and returns early if False. This is the correct approach regardless of whether the browser sends the value.
**Warning signs:** Tests passing without the toggle-bypass check.

### Pitfall 2: Error Key Mismatch Between Validator and Template
**What goes wrong:** The `pydantic_errors_to_dict` function uses field-prefixed messages (e.g., `"inflation_rate:Must be a number."`). The template must look up `errors.get('settings.inflation_rate')`.
**Why it happens:** The error key path is `settings` (from `FormInput.settings`) + field name from the prefixed message.
**How to avoid:** Use exact same prefix pattern as `validate_return_rate`. The message format `"inflation_rate:..."` gets mapped to key `settings.inflation_rate` by `pydantic_errors_to_dict`.
**Warning signs:** Error messages appear in server logs but not in the rendered HTML.

### Pitfall 3: Warning Banner Variable Not Passed
**What goes wrong:** `option_list.html` checks `{% if warning_message %}` but routes that don't need the warning forget to pass it, causing Jinja `UndefinedError`.
**Why it happens:** New template variable not passed from all calling routes.
**How to avoid:** Use `{% if warning_message is defined and warning_message %}` or set a default in the template with `{{ warning_message|default('') }}`. Alternatively, always pass `warning_message=""` from every route that renders `option_list.html`.
**Warning signs:** Normal add/remove operations (not at limits) raise template errors.

### Pitfall 4: Multiple Model Validators Execution Order
**What goes wrong:** Pydantic model validators on the same model run in declaration order but if one raises, subsequent ones don't run. The inflation and tax validators are independent, so both should report errors.
**Why it happens:** `@model_validator` raising ValueError stops the chain.
**How to avoid:** Collect errors in a list and raise once at the end, similar to `OptionInput.validate_by_type`. Or accept that they fire one-at-a-time (simpler, but user fixes one error to see the next).
**Warning signs:** Only one error shown when both inflation and tax are invalid. Since these are rarely both invalid simultaneously, one-at-a-time is acceptable for simplicity.

### Pitfall 5: Count Guard Uses Wrong Comparison
**What goes wrong:** Using `len(indices) > 4` instead of `>= 4` in add_option, allowing a 5th option briefly.
**Why it happens:** Off-by-one: there are 4 indices, we want to prevent adding a 5th.
**How to avoid:** `if len(indices) >= 4: return unchanged`. For remove: `if len(indices) <= 2: return unchanged`.

## Code Examples

### Inflation Rate Validator (to add to SettingsInput)
```python
@model_validator(mode="after")
def validate_inflation_rate(self) -> Self:
    """Validate inflation rate bounds when inflation is enabled."""
    if not self.inflation_enabled:
        return self
    val = _try_decimal(self.inflation_rate)
    if val is None:
        msg = "inflation_rate:Must be a number."
        raise ValueError(msg)
    if val < 0 or val > 20:
        msg = "inflation_rate:Inflation rate must be between 0% and 20%."
        raise ValueError(msg)
    return self
```

### Tax Rate Validator (to add to SettingsInput)
```python
@model_validator(mode="after")
def validate_tax_rate(self) -> Self:
    """Validate tax rate bounds when tax is enabled."""
    if not self.tax_enabled:
        return self
    val = _try_decimal(self.tax_rate)
    if val is None:
        msg = "tax_rate:Must be a number."
        raise ValueError(msg)
    if val < 0 or val > 60:
        msg = "tax_rate:Tax rate must be between 0% and 60%."
        raise ValueError(msg)
    return self
```

### Add Option Guard (to add at top of add_option route)
```python
from fathom.forms import _OPTION_INDEX_RE

# Count options from raw form keys
indices: set[int] = set()
for key in request.form:
    match = _OPTION_INDEX_RE.match(key)
    if match:
        indices.add(int(match.group(1)))

if len(indices) >= 4:
    parsed = extract_form_data(request.form)
    options = _build_options_list(parsed)  # helper to build template options
    return render_template(
        "partials/option_list.html",
        options=options,
        option_types=_build_option_types(),
        errors={},
        warning_message="Maximum 4 options allowed",
    )
```

### Template Error Display (global_settings.html inflation section)
```html
<fieldset role="group">
  <input
    type="number"
    min="0" max="20" step="0.1"
    id="inflation-rate"
    name="inflation_rate"
    value="{{ settings.inflation_rate|default('3') }}"
    placeholder="3"
    {% if not settings.inflation_enabled %}disabled{% endif %}
    {% if errors.get('settings.inflation_rate') %}aria-invalid="true"{% endif %}
  >
  <span class="suffix">%</span>
</fieldset>
{% if errors.get('settings.inflation_rate') %}
<small class="field-error">{{ errors['settings.inflation_rate'] }}</small>
{% endif %}
```

### Warning Banner (top of option_list.html)
```html
{% if warning_message is defined and warning_message %}
<div role="alert" class="option-warning">
  {{ warning_message }}
</div>
{% endif %}
{% for opt in options %}
{% include "partials/option_card.html" %}
{% endfor %}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No inflation/tax bounds | Add bounds validators | This phase | Prevents impossible values reaching engine |
| Client-only button hiding | Server-side guards + client hints | This phase | Crafted requests can't bypass limits |

## Open Questions

1. **Should both inflation and tax validators raise independently?**
   - What we know: Current `validate_return_rate` raises immediately. `OptionInput.validate_by_type` collects errors.
   - What's unclear: Whether to show one error at a time or all simultaneously.
   - Recommendation: Use one-at-a-time (simpler). Inflation and tax are rarely both invalid simultaneously. Keeps code consistent with `validate_return_rate`.

2. **Should `_OPTION_INDEX_RE` be exported from forms.py?**
   - What we know: It's a module-level constant, currently prefixed with `_` (private).
   - What's unclear: Whether to make it public or duplicate the counting logic.
   - Recommendation: Either make it public (`OPTION_INDEX_RE`) or create a small `count_form_options(form_data)` helper in `forms.py` that routes can call. The helper approach is cleaner.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (installed) |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/test_forms.py tests/test_routes.py -x -q` |
| Full suite command | `uv run pytest -x -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| VAL-01 | Inflation 0-20% bounds, non-numeric, toggle-off bypass | unit | `uv run pytest tests/test_forms.py -x -k "inflation"` | Partially (no inflation-specific tests yet) |
| VAL-02 | Tax 0-60% bounds, non-numeric, toggle-off bypass | unit | `uv run pytest tests/test_forms.py -x -k "tax_rate"` | Partially (no tax bounds tests yet) |
| VAL-03 | Add at 4 returns unchanged form | integration | `uv run pytest tests/test_routes.py -x -k "add"` | Partially (tests add at 3->4 but not at 4->4 rejection) |
| VAL-04 | Remove at 2 returns unchanged form | integration | `uv run pytest tests/test_routes.py -x -k "remove"` | Partially (tests remove at 3->2 but not at 2->2 rejection) |
| TEST-03 | HTMX add-at-4 and remove-at-2 rejection tests | integration | `uv run pytest tests/test_routes.py -x -k "guard"` | No |
| TEST-04 | Inflation/tax bounds rejection tests | unit | `uv run pytest tests/test_forms.py -x -k "bounds"` | No |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_forms.py tests/test_routes.py -x -q`
- **Per wave merge:** `uv run pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_forms.py::TestInflationRateValidation` -- covers VAL-01 (bounds, non-numeric, toggle bypass)
- [ ] `tests/test_forms.py::TestTaxRateValidation` -- covers VAL-02 (bounds, non-numeric, toggle bypass)
- [ ] `tests/test_routes.py::TestAddOptionGuard` -- covers VAL-03, TEST-03 (add at 4 returns unchanged)
- [ ] `tests/test_routes.py::TestRemoveOptionGuard` -- covers VAL-04, TEST-03 (remove at 2 returns unchanged)

## Sources

### Primary (HIGH confidence)
- Codebase: `src/fathom/forms.py` -- existing validators, `_try_decimal`, `_OPTION_INDEX_RE`, `SettingsInput`, `pydantic_errors_to_dict`
- Codebase: `src/fathom/routes.py` -- existing `add_option`, `remove_option` routes
- Codebase: `src/fathom/templates/partials/global_settings.html` -- current inflation/tax field markup
- Codebase: `src/fathom/templates/partials/option_list.html` -- current add button conditional
- Codebase: `src/fathom/templates/partials/option_card.html` -- current remove button conditional
- Codebase: `src/fathom/templates/partials/option_fields/traditional.html` -- inline error display pattern
- Codebase: `tests/test_forms.py`, `tests/test_routes.py` -- existing test patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in use, no new dependencies
- Architecture: HIGH -- all patterns are direct extensions of existing code
- Pitfalls: HIGH -- identified from reading actual codebase patterns and error handling chain

**Research date:** 2026-03-15
**Valid until:** 2026-04-15 (stable -- internal codebase patterns)
