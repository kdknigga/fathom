# Phase 16: Custom Option Cleanup - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire `custom_label` into results display so custom options show user-provided names everywhere, clarify that upfront cash is optional, and add tests. Requirements: CUST-01, CUST-02, TEST-05.

</domain>

<decisions>
## Implementation Decisions

### Label collision handling
- Auto-disambiguate all label collisions with parenthetical numeric suffix: "My Plan", "My Plan (2)", "My Plan (3)"
- Applies universally — custom-vs-custom AND custom-vs-default-label collisions (e.g., user types "Traditional Loan" as custom label)
- Disambiguation runs in `build_domain_objects()` (forms.py) — labels are unique before reaching the engine
- Results dict keyed by `option.label` (engine.py:710-722) depends on uniqueness, so this must happen upstream

### Custom label display scope
- Full replacement — custom label becomes the option name everywhere: recommendation card, breakdown table, bar chart, line chart
- No "(Custom)" subtitle or type indicator in results
- Implementation: set `label = custom_label.strip()` in `build_domain_objects()` when type is CUSTOM and label is non-empty
- Rename form field label from "Description (optional)" to "Option Name (optional)"
- Update placeholder from "Notes about this option" to something like "e.g., Store Credit Card"
- No tooltip needed on the option name field

### Upfront cash optionality
- Rename field label from "Upfront Cash Required" to "Down Payment (optional)" — consistent with other option types
- Update tooltip text to reflect optional nature (e.g., "Optional upfront payment toward the purchase price. Leave blank if none.")
- Tooltip popover ID naming: Claude's discretion

### Empty label fallback
- When `custom_label` is empty or whitespace, fall back to "Custom" (matches OptionType.CUSTOM enum value, title-cased)
- Same auto-disambiguation rules apply to fallback labels — two empty custom options become "Custom", "Custom (2)"
- Add HTML `maxlength` attribute (soft limit, ~40 chars) on the custom label input to prevent chart layout breakage

### Claude's Discretion
- Exact maxlength value for custom label input
- Tooltip popover ID naming convention
- Placeholder text wording (given the "e.g., Store Credit Card" direction)
- Test structure and assertion patterns
- How to handle edge cases (whitespace-only labels, special characters)

</decisions>

<specifics>
## Specific Ideas

- The disambiguation should feel like file system naming ("Copy", "Copy (2)") — familiar pattern
- "Down Payment (optional)" label aligns custom options with how loan/promo options show the same field
- Renaming the input to "Option Name" communicates that the text appears in results, not just as internal notes

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `build_domain_objects()` (forms.py:616): Already sets `label = opt.label or option_type.value` — the custom_label wire-in is a one-line change at this point
- `OptionInput.custom_label` (forms.py:342): Field already parsed from form data, just not used downstream
- `custom.html` template: Already renders the custom_label input field (lines 67-74)

### Established Patterns
- Labels flow through the entire display pipeline via `option.label` — recommendation, breakdown, charts all use it
- Results dict keyed by label (engine.py:710-722) — uniqueness is required
- Other option types use `option_type.value` as default label (e.g., "traditional_loan", "promo_cash_back")
- Inline `<small class="field-error">` + `aria-invalid` for form errors (Phase 15 pattern)
- Tooltip pattern: `<div class="label-with-tip">` + `<button class="tip" popovertarget="...">` + `<div popover>`

### Integration Points
- `forms.py:build_domain_objects()` — wire custom_label into label, add disambiguation loop
- `custom.html` template — rename field label, update placeholder, add maxlength, update tooltip text
- `tests/test_forms.py` — test custom_label flows into FinancingOption.label
- `tests/test_routes.py` — test custom_label appears in rendered HTML results (TEST-05)

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 16-custom-option-cleanup*
*Context gathered: 2026-03-15*
