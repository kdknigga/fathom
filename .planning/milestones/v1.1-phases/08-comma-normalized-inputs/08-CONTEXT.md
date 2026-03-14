# Phase 8: Comma-Normalized Inputs - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Accept, parse, and display comma-formatted numbers in all monetary input fields. Format on blur, strip on focus, parse on server. No real-time formatting while typing (explicitly excluded in REQUIREMENTS.md). US number format only.

</domain>

<decisions>
## Implementation Decisions

### Field scope
- Comma formatting applies to **monetary fields only** — purchase price, monthly payment, cash-back amount, price reduction, custom monthly payment
- Rate fields (APR, return rate, inflation rate, tax rate) and term fields (months) are excluded — too small to benefit from commas
- Rule is simple: any field where a user enters a dollar amount gets comma formatting
- Support decimal places as-entered — '25000' shows '25,000', '25000.50' shows '25,000.50'. Don't add or remove decimal places

### Focus/blur behavior
- **On focus:** strip commas so user sees raw number (e.g., '25,000' → '25000'). Avoids cursor position issues when editing mid-number
- **On blur:** add commas to the value (e.g., '25000' → '25,000'). This is the only time formatting happens client-side
- No real-time formatting while typing (REQUIREMENTS.md exclusion)

### Restored value display
- **Server renders monetary values with commas** in the HTML value attribute — user sees '25,000' immediately after HTMX results load, no JS needed for initial display
- **Initial page load defaults also show commas** — '25,000' from the moment the page loads, via Jinja filter
- **HTMX-swapped fields arrive pre-formatted** — switching option types renders new fields with comma-formatted defaults
- Consistency rule: every server-rendered monetary value goes through the comma formatter

### Paste handling
- **Client-side:** strip `$`, commas, and spaces on paste event. Field shows clean number (e.g., paste '$100,000' → '100000'). Commas added on subsequent blur
- **Server-side:** also strip `$`, commas, and spaces before Decimal conversion — belt and suspenders, never silently fails
- **US format only** — commas are thousands separators, dots are decimal points. No European format detection (PROJECT.md scopes to US-centric)
- Paste strips junk immediately, formatting waits for blur — consistent with blur-only rule

### Claude's Discretion
- JS implementation approach: data attribute vs class-based selector for identifying monetary inputs
- Event delegation vs per-element listeners for HTMX compatibility
- Jinja filter implementation for server-side comma formatting
- Exact list of which template fields are "monetary" (Claude identifies from codebase)

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. The key constraint is consistency: every monetary field should behave identically whether on initial load, after HTMX swap, or after user interaction.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`forms.py` parse_form_data()**: Central parsing function that reads `request.form` — comma/dollar stripping goes here
- **`forms.py` extract_form_data()**: Extracts raw form data for re-rendering — comma formatting goes here
- **Jinja template system**: Can add a custom filter (e.g., `{{ value|comma }}`) for server-side formatting

### Established Patterns
- Most monetary fields already use `type="text"` with `inputmode="decimal"` — these accept commas natively
- Some fields use `type="number"` (term months in promo_zero, custom, traditional, promo_price) — these are NOT monetary and should stay as-is
- Decimal arithmetic throughout (`from decimal import Decimal`) — commas must be stripped before conversion

### Integration Points
- **Templates**: All option field templates in `src/fathom/templates/partials/option_fields/` — add comma formatting to value attributes
- **`global_settings.html`**: Return rate custom, inflation rate, tax rate — NOT monetary, no changes
- **`index.html`**: Purchase price field — IS monetary, needs formatting
- **`forms.py`**: Both `parse_form_data()` and `extract_form_data()` need comma handling
- **Static JS**: New file or inline script for blur/focus/paste event handling

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 08-comma-normalized-inputs*
*Context gathered: 2026-03-13*
