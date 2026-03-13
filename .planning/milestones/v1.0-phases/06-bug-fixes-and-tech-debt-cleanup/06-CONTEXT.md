# Phase 6: Bug Fixes and Tech Debt Cleanup - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Close all gaps identified by the v1.0 milestone audit: expose retroactive_interest in the form UI, add server-side option count validation, fix return_preset format bug, remove type:ignore comments, add config.py to README, and harden Playwright data table tests with cell value assertions.

</domain>

<decisions>
## Implementation Decisions

### Retroactive interest UI
- Add a separate checkbox for retroactive_interest, visible only when deferred_interest is checked
- Label: "Interest calculated from original purchase date" with a `<small>` help text explaining the impact (matches existing post-promo APR hint pattern)
- Default to checked when deferred_interest is enabled (most real-world 0% promos are retroactive)
- Toggling the checkbox triggers HTMX live recalculation (consistent with existing inflation/tax toggles)
- Add `retroactive_interest: bool` field to `OptionInput` Pydantic model with cross-field validation: only valid when `deferred_interest` is True and `option_type` is `PROMO_ZERO_PERCENT`
- Template changes in `promo_zero.html`; form parsing in `forms.py`; `build_domain_objects` passes value to `FinancingOption`

### Server-side option count validation
- Add `@field_validator` on `FormInput.options` enforcing 2-4 option count
- Reject with validation error (not silent clamping) — consistent with all other validation
- Error message: "Please compare between 2 and 4 financing options." (consumer-friendly tone)
- `min_length=2` naturally catches 0 and 1 options; same message covers all out-of-range cases
- Error displays at top of form as a general form error (not field-specific)

### return_preset format fix
- Change `routes.py:156` from `str(fathom_settings.default_return_rate)` to `f"{fathom_settings.default_return_rate:.2f}"`
- Ensures radio button pre-selection works for all rate values including 0.10

### type:ignore removal
- Remove `# type: ignore[arg-type]` comments from `forms.py` (lines 410-411 area)
- Both ty and pyrefly pass clean without them — these are unnecessary suppression comments violating CLAUDE.md policy

### README architecture tree
- Add `config.py` line to the architecture tree in README.md with description comment (e.g., `config.py  # Application configuration (pydantic-settings)`)

### Playwright data table test hardening
- Extend existing `playwright_verify.py` to assert cell value accuracy in accessible data tables
- Full cell-by-cell verification for both bar chart AND line chart data tables
- Use the same known test scenario as existing calculation tests ($10k / 6% / 36mo)
- Assert exact formatted dollar amounts (no tolerance) — Decimal arithmetic ensures deterministic values
- Verify data tables have visually-hidden class AND correct aria attributes
- Add dedicated regression test for the A11Y-02 defect (line chart data table correctness)

### Claude's Discretion
- Exact help text wording for retroactive interest checkbox
- HTMX trigger attributes for the new checkbox (likely matches existing checkbox pattern)
- Specific cell assertions and test structure in playwright_verify.py
- Order of fixes within plans

</decisions>

<specifics>
## Specific Ideas

- The retroactive interest checkbox should feel natural alongside the existing deferred interest checkbox — progressive disclosure (check deferred → see retroactive option)
- Server validation error for option count should be indistinguishable from other validation errors in the UI — same styling, same behavior
- Playwright test should use the same $10k cash vs loan scenario that the known-value calculation tests use, so expected values are already verified

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `promo_zero.html`: Template already has deferred_interest checkbox — retroactive checkbox goes below it with conditional visibility
- `OptionInput` Pydantic model in `forms.py`: Already has `deferred_interest` field — add `retroactive_interest` alongside
- `playwright_verify.py`: Existing Playwright test infrastructure for browser-based assertions
- `config.py`: `FathomSettings` pydantic-settings model — `default_return_rate` field used in format fix

### Established Patterns
- Conditional field visibility via `{% if %}` in Jinja2 templates (used for type-specific fields)
- HTMX live update via `hx-trigger` on checkboxes (used by inflation/tax toggles)
- Consumer-friendly validation messages (e.g., "APR must be between 0% and 40%")
- `@field_validator` and `@model_validator` patterns in `forms.py` OptionInput/FormInput
- Visually-hidden data tables alongside SVG charts for accessibility

### Integration Points
- `forms.py`: OptionInput model + build_domain_objects for retroactive_interest extraction
- `routes.py:156`: Format fix for return_preset
- `promo_zero.html`: New checkbox + conditional visibility
- `README.md`: Architecture tree update
- `playwright_verify.py` or new test file: Data table value assertions

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-bug-fixes-and-tech-debt-cleanup*
*Context gathered: 2026-03-13*
