# Phase 6: Bug Fixes and Tech Debt Cleanup - Research

**Researched:** 2026-03-13
**Domain:** Flask/Pydantic form validation, HTMX UI, Playwright testing, code quality
**Confidence:** HIGH

## Summary

Phase 6 is a gap closure phase addressing 6 specific items from the v1.0 milestone audit. All items are well-scoped with known file locations and established patterns to follow. The codebase already has the patterns needed -- retroactive_interest checkbox mirrors existing deferred_interest checkbox, server-side validation uses existing `@field_validator` patterns, and Playwright tests extend an existing test file.

One item -- `type: ignore` removal -- has already been completed (no `# type: ignore` or `# noqa` comments exist in `src/fathom/`). The remaining 5 items are straightforward implementations following established project conventions.

**Primary recommendation:** Group changes into 2 plans: (1) Model/validation/route fixes (retroactive_interest model+form+template, FORM-05 server validation, return_preset format fix), (2) Documentation and test hardening (README update, Playwright cell value assertions).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Retroactive interest: separate checkbox below deferred_interest, visible only when deferred_interest is checked, default checked, label "Interest calculated from original purchase date" with `<small>` help text, HTMX live recalculation trigger
- Add `retroactive_interest: bool` to `OptionInput` Pydantic model with cross-field validation (only valid when `deferred_interest` is True and `option_type` is `PROMO_ZERO_PERCENT`)
- Template changes in `promo_zero.html`; form parsing in `forms.py`; `build_domain_objects` passes value to `FinancingOption`
- Server-side option count: `@field_validator` on `FormInput.options` enforcing 2-4 count, reject with validation error, message "Please compare between 2 and 4 financing options.", error displays at top of form
- return_preset: change `routes.py:156` from `str(...)` to `f"{...:.2f}"`
- type:ignore removal: remove from `forms.py` lines 410-411 area (ALREADY DONE -- no such comments exist)
- README: add `config.py` to architecture tree
- Playwright: full cell-by-cell verification for bar AND line chart data tables, same $10k scenario, exact formatted dollar amounts, visually-hidden class + aria attributes, dedicated A11Y-02 regression test

### Claude's Discretion
- Exact help text wording for retroactive interest checkbox
- HTMX trigger attributes for the new checkbox
- Specific cell assertions and test structure in playwright_verify.py
- Order of fixes within plans

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FORM-05 | User can define 2-4 financing options to compare (defense-in-depth) | Add `@field_validator` on `FormInput.options` enforcing `len(v)` between 2 and 4. Existing `@field_validator` pattern on `purchase_price` in same class provides the template. Error displays via `pydantic_errors_to_dict` which maps `options` loc to top-level form error. |
</phase_requirements>

## Standard Stack

### Core (already in project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic | v2 | Form validation models (`OptionInput`, `FormInput`) | Already used for all form validation |
| Flask | 3.x | Web framework, routes, templates | Project web layer |
| Jinja2 | 3.x | HTML templates with conditional logic | Flask's template engine |
| HTMX | 2.x | Partial page updates on form changes | Already used for form submission and type switching |
| Playwright | latest | Browser automation for verification tests | Already used in `playwright_verify.py` |
| pytest | latest | Unit test framework | 169 tests already passing |

### No new dependencies needed
This phase modifies existing code only. No new packages required.

## Architecture Patterns

### Pattern 1: Pydantic Field Validator for List Constraints
**What:** `@field_validator` on a list field to enforce length constraints
**When to use:** FORM-05 server-side option count validation
**Example:**
```python
# In FormInput class (forms.py)
@field_validator("options")
@classmethod
def validate_option_count(cls, v: list[OptionInput]) -> list[OptionInput]:
    """Enforce 2-4 option count."""
    if len(v) < 2 or len(v) > 4:
        msg = "Please compare between 2 and 4 financing options."
        raise ValueError(msg)
    return v
```

**Error routing:** `pydantic_errors_to_dict` will produce key `"options"` from the loc tuple. The template displays errors without a field-specific prefix as a top-level form error. The existing error display logic in `index.html` should already handle this -- verify that `errors.get('options')` renders in the general error area.

### Pattern 2: Checkbox with Conditional Visibility (Progressive Disclosure)
**What:** A checkbox that only appears when a parent checkbox is checked
**When to use:** retroactive_interest visible only when deferred_interest is checked
**Example pattern from existing code:**
```html
{# In promo_zero.html #}
<label for="option-{{ opt.idx }}-deferred-interest">
  <input type="checkbox" ... {% if opt.fields.deferred_interest %}checked{% endif %}>
  Interest charges apply retroactively if not paid in full
</label>

{# New retroactive_interest checkbox below #}
{% if opt.fields.deferred_interest %}
<label for="option-{{ opt.idx }}-retroactive-interest">
  <input type="checkbox"
    id="option-{{ opt.idx }}-retroactive-interest"
    name="options[{{ opt.idx }}][retroactive_interest]"
    value="1"
    {% if opt.fields.retroactive_interest is not defined or opt.fields.retroactive_interest %}checked{% endif %}
  >
  Interest calculated from original purchase date
</label>
<small>If not paid in full during the promotional period, interest accrues from the original purchase date</small>
{% endif %}
```

**Key consideration:** The conditional `{% if opt.fields.deferred_interest %}` makes the checkbox visible only when deferred_interest is checked. Since the form round-trips through the server on each submission (no client-side JS toggling), this approach is consistent with the stateless SSR architecture.

### Pattern 3: Checkbox Field in Pydantic Model
**What:** Adding a boolean checkbox field to OptionInput with cross-field validation
**When to use:** retroactive_interest field
**Example:**
```python
# In OptionInput (forms.py)
retroactive_interest: bool = False

# In _CHECKBOX_FIELDS set
_CHECKBOX_FIELDS = {"deferred_interest", "retroactive_interest"}

# In _OPTION_FIELDS tuple
_OPTION_FIELDS = (..., "retroactive_interest")
```

**Cross-field validation:** Add to the existing `validate_by_type` model_validator -- if `retroactive_interest` is True but `deferred_interest` is False or type is not PROMO_ZERO_PERCENT, either silently reset to False or raise an error. Per context decisions: only valid when both conditions met. Since the UI hides the checkbox when deferred_interest is unchecked, a crafted POST is the only way to trigger the mismatch -- silently resetting to False is the safer UX pattern (no error message needed for a field the user never saw).

### Pattern 4: Build Domain Objects Pass-Through
**What:** Extracting the new field in `build_domain_objects` and passing to `FinancingOption`
**When to use:** Connecting form input to domain model
**Example:**
```python
# In build_domain_objects loop
retroactive_interest = bool(opt.retroactive_interest) and bool(opt.deferred_interest)

options.append(
    FinancingOption(
        ...
        deferred_interest=deferred_interest,
        retroactive_interest=retroactive_interest,
        ...
    ),
)
```

### Anti-Patterns to Avoid
- **Client-side visibility toggling:** Do not add JavaScript to show/hide the retroactive checkbox. The server re-renders the template on every interaction via HTMX. Use Jinja2 conditionals only.
- **Silent clamping on option count:** The context explicitly says "reject with validation error, not silent clamping." Always raise ValueError.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Option count validation | Manual len() checks in routes | `@field_validator` on Pydantic model | Single source of truth, consistent error handling |
| Checkbox conditional visibility | Client-side JS toggle | Jinja2 `{% if %}` with server re-render | SSR architecture, no JS duplication |
| Form error display | Custom error rendering | Existing `pydantic_errors_to_dict` pipeline | All validation already flows through this |

## Common Pitfalls

### Pitfall 1: Retroactive Interest Default Mismatch
**What goes wrong:** The domain model `FinancingOption.retroactive_interest` defaults to `True`, but a new checkbox field on `OptionInput` would default to `False` (unchecked). If the form doesn't send the checkbox value, the domain object would get `False` instead of the expected `True`.
**Why it happens:** HTML checkboxes only submit a value when checked. An unchecked checkbox sends nothing.
**How to avoid:** Default `retroactive_interest` to `True` in the template (add `checked` by default when deferred_interest is enabled). The context decision says "Default to checked when deferred_interest is enabled."
**Warning signs:** Tests pass but retroactive interest calculation path is never triggered.

### Pitfall 2: Option Count Error Display Location
**What goes wrong:** The FORM-05 validation error for option count may not display because the template only renders field-specific errors, not top-level form errors.
**Why it happens:** `pydantic_errors_to_dict` maps the loc `("options",)` to key `"options"` but the template may not have a slot for `errors.options`.
**How to avoid:** Check `index.html` for how general form errors are displayed. Add an error display block at the top of the form if one does not exist for the `options` key.
**Warning signs:** Submitting a crafted 1-option POST returns a 200 with no visible error.

### Pitfall 3: Playwright Test Port Mismatch
**What goes wrong:** The existing `playwright_verify.py` uses `BASE_URL = "http://localhost:5001"` but the default app port is 5000.
**Why it happens:** The test may have been written for a specific test server configuration.
**How to avoid:** Ensure the test scenario uses the same port as the running dev server, or make port configurable.
**Warning signs:** Connection refused errors when running Playwright tests.

### Pitfall 4: Return Preset Format String Precision
**What goes wrong:** Using `f"{rate:.2f}"` on a float value like `0.07` could produce unexpected results if the value has been through float arithmetic.
**Why it happens:** `FathomSettings.default_return_rate` is a `float` from pydantic-settings.
**How to avoid:** The fix is straightforward -- `f"{0.07:.2f}"` produces `"0.07"` and `f"{0.10:.2f}"` produces `"0.10"`. Just apply the format string.
**Warning signs:** Radio button not pre-selected on page load.

### Pitfall 5: type:ignore Already Removed
**What goes wrong:** Attempting to remove `# type: ignore` comments that no longer exist.
**Why it happens:** The comments were likely removed during Phase 5 Pydantic refactor.
**How to avoid:** This item is already resolved. Grep confirms no `# type: ignore` or `# noqa` comments exist in `src/fathom/`. Skip this task entirely or include it as a verification-only step.

## Code Examples

### FORM-05: Server-Side Option Count Validator
```python
# Source: existing FormInput class in forms.py, line 221
# Add alongside existing validate_purchase_price

@field_validator("options")
@classmethod
def validate_option_count(cls, v: list[OptionInput]) -> list[OptionInput]:
    """Enforce 2-4 financing options for comparison."""
    if len(v) < 2 or len(v) > 4:
        msg = "Please compare between 2 and 4 financing options."
        raise ValueError(msg)
    return v
```

### Return Preset Format Fix
```python
# Source: routes.py line 156
# Before:
"return_preset": str(fathom_settings.default_return_rate),
# After:
"return_preset": f"{fathom_settings.default_return_rate:.2f}",
```

### README Architecture Tree Addition
```
src/fathom/
  __init__.py      # Entry point
  app.py           # Flask app factory
  config.py        # Application configuration (pydantic-settings)
  routes.py        # HTTP route handlers
  ...
```

### Playwright Cell Value Assertion Pattern
```python
# Extend existing playwright_verify.py
# Use same $10k cash vs loan scenario as fill_valid_form but with known values

# Bar chart data table assertions
bar_table = page.query_selector('.visually-hidden table:has(caption:text("True Total Cost"))')
rows = bar_table.query_selector_all("tbody tr")
for row in rows:
    cells = row.query_selector_all("td")
    name = cells[0].text_content().strip()
    value = cells[1].text_content().strip()
    # Assert exact dollar amounts based on known test scenario
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| UI-only option count enforcement | Server-side Pydantic validation | Phase 6 | Defense-in-depth per FORM-05 |
| Hardcoded retroactive_interest=True | User-controllable via checkbox | Phase 6 | Correct 0% promo modeling |
| str() for float formatting | f-string with format spec | Phase 6 | Fixes radio preset selection bug |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (latest via uv) |
| Config file | pyproject.toml |
| Quick run command | `uv run pytest tests/test_forms.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FORM-05 | Server rejects <2 or >4 options | unit | `uv run pytest tests/test_forms.py -x -k "option_count"` | Wave 0 |
| (gap) retroactive_interest | Form extracts and passes retroactive_interest to domain | unit | `uv run pytest tests/test_forms.py -x -k "retroactive"` | Wave 0 |
| (gap) return_preset | Format produces "0.10" not "0.1" | unit | `uv run pytest tests/test_routes.py -x -k "return_preset"` | Wave 0 |
| (gap) data_table_values | Playwright asserts cell accuracy | browser | `uv run python tests/playwright_verify.py` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_forms.py tests/test_routes.py -x`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green + Playwright verify before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_forms.py` -- add tests for option count validation (2-4 enforcement)
- [ ] `tests/test_forms.py` -- add tests for retroactive_interest field parsing and cross-field validation
- [ ] `tests/test_routes.py` -- add test for return_preset format with 0.10 rate
- [ ] `tests/playwright_verify.py` -- add cell value assertion checks for bar and line chart data tables

## Open Questions

1. **General form error display slot**
   - What we know: Field-specific errors render via `errors.get('options.0.apr')` etc. The option count error would produce key `"options"`.
   - What's unclear: Whether `index.html` has a slot for displaying `errors.options` at the top of the form.
   - Recommendation: Check the template during implementation. If no general error slot exists, add one at the top of the form section.

2. **Playwright test scenario values**
   - What we know: The test uses $25,000 cash vs $20,000 loan at 6%/36mo. The expected calculated values need to be pre-computed.
   - What's unclear: Exact dollar amounts for bar and line chart data table cells.
   - Recommendation: Run the app with the test scenario, capture the rendered values, then hard-code as assertions. Decimal arithmetic ensures deterministic results.

## Sources

### Primary (HIGH confidence)
- Direct code inspection of `forms.py`, `routes.py`, `models.py`, `promo_zero.html`, `playwright_verify.py`, `conftest.py`
- v1.0-MILESTONE-AUDIT.md -- definitive list of gaps and tech debt
- 06-CONTEXT.md -- locked implementation decisions

### Secondary (MEDIUM confidence)
- Pydantic v2 `@field_validator` pattern -- verified in existing codebase usage

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all patterns exist in codebase
- Architecture: HIGH -- every change follows an established pattern in the project
- Pitfalls: HIGH -- identified from direct code inspection and audit findings
- type:ignore item: HIGH -- confirmed already resolved via grep

**Research date:** 2026-03-13
**Valid until:** 2026-04-13 (stable codebase, no external dependency changes)
