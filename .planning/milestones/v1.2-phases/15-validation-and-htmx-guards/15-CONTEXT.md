# Phase 15: Validation and HTMX Guards - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Bound inflation/tax rates and enforce the 2-4 option contract server-side, with appropriate client-side hints. Users cannot submit impossible values or violate option limits through the UI or crafted requests.

Requirements: VAL-01, VAL-02, VAL-03, VAL-04, TEST-03, TEST-04

</domain>

<decisions>
## Implementation Decisions

### Error display style
- Inline errors next to inflation/tax fields using the existing `<small class="field-error">` pattern with `aria-invalid="true"` on the input
- Consistent with how APR, term, and other fields already show errors
- Exact bounds in error messages: "Inflation rate must be between 0% and 20%", "Tax rate must be between 0% and 60%"
- Separate message for non-numeric input: "Must be a number" (two-step validation like return rate)
- When toggle is OFF (inflation_enabled/tax_enabled = false), skip validation entirely — no inline error shown for disabled fields (SC5)

### HTMX option limit guards
- Server-side guard in `add_option`: count options from raw form keys BEFORE calling `extract_form_data`. If >= 4, return unchanged form with flash-style warning banner above options: "Maximum 4 options allowed"
- Server-side guard in `remove_option`: same approach. If <= 2, return unchanged form with banner: "Minimum 2 options required"
- Warning banner renders at top of `option_list.html` partial, disappears on next HTMX interaction (re-render clears it)
- The `/compare` submit endpoint relies on existing Pydantic `FormInput.validate_option_count` — no duplication needed

### Client-side HTML5 hints
- Change inflation_rate input to `type="number" min="0" max="20" step="0.1"`
- Change tax_rate input to `type="number" min="0" max="60" step="1"`
- Also add `type="number" min="0" max="30" step="0.01"` to the custom return rate field for consistency
- Add HTML `disabled` attribute to inflation/tax inputs when their toggle is OFF — greys out field, prevents interaction, and excludes from form submission

### Claude's Discretion
- Exact implementation of the raw form key counting (regex pattern for option indices)
- How to wire the disabled attribute to toggle state (JS listener or HTMX swap)
- Test structure and assertion patterns for the new validation
- Warning banner styling (color, icon, animation)

</decisions>

<specifics>
## Specific Ideas

- The two-step validation (non-numeric vs out-of-range) should mirror the existing `validate_return_rate` pattern in `SettingsInput`
- The flash banner for option limits is a new pattern in the app — keep it minimal and consistent with PicoCSS
- Since buttons are already conditionally hidden in templates (`options|length < 4` for Add, `options|length > 2` for Remove), the server guard only fires for crafted requests

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SettingsInput` (forms.py:84-115): Already has `validate_return_rate` model validator — inflation/tax validators follow the same pattern
- `FormInput.validate_option_count` (forms.py:352-359): Already validates 2-4 at submit time
- `pydantic_errors_to_dict` (forms.py): Converts Pydantic errors to template-friendly dict
- `_try_decimal` (forms.py): Existing helper for safe string-to-Decimal conversion

### Established Patterns
- Inline errors: `<small class="field-error">` + `aria-invalid="true"` on inputs (used in all option field templates)
- Results error banner: `partials/results.html` shows error list when `has_errors` is true
- HTMX partials: endpoints return re-rendered HTML fragments targeting `#options-container`
- Template conditionals: `option_list.html` already hides Add button at 4, `option_card.html` hides Remove at 2

### Integration Points
- `SettingsInput` class: Add `@model_validator` for inflation/tax rate bounds
- `add_option` route (routes.py:209-263): Add early count check before `extract_form_data`
- `remove_option` route (routes.py:266-311): Add early count check before `extract_form_data`
- `global_settings.html` partial: Add error display and update input types
- `option_list.html` partial: Add optional warning banner slot

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 15-validation-and-htmx-guards*
*Context gathered: 2026-03-15*
