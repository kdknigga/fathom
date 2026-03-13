# Phase 2: Web Layer and Input Forms - Context

**Gathered:** 2026-03-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Flask app with form handling for all 6 financing option types, responsive two-column layout, server-side validation, and form repopulation after submission. Users can fill out a complete comparison form and submit for calculation. Results display, charts, and HTMX live updates are Phase 3.

</domain>

<decisions>
## Implementation Decisions

### Option management UX
- Form starts with 2 options pre-filled: Option 1 = "Pay in Full", Option 2 = "Traditional Loan"
- Each option has a custom editable name field, defaulting to the type name (e.g., "Traditional Loan")
- Users can rename options to anything (e.g., "Best Buy Card", "Credit Union Loan")
- "+" Add financing option" text button below the last option, disappears at 4 options
- New options default to "Traditional Loan" type
- Remove via small x icon in option header, no confirmation dialog
- Remove button hidden when only 2 options remain (minimum enforced)
- No reordering — options stay in the order added; results handle ordering

### Dynamic field reveal
- Changing option type instantly swaps fields (HTMX server-side swap, no animation)
- Switching type clears all type-specific field values (clean slate, no stale data)
- Type selector dropdown lives in the option card header, next to the editable name and remove button
- "Pay in Full" card body shows brief explanation text ("Full purchase price paid upfront. No additional fields needed.") rather than empty/collapsed

### Form visual style
- Card-based sections: (1) Purchase Price card at top, (2) Financing Options card containing sub-cards per option, (3) Global Settings as collapsible section
- Global settings (return rate, inflation, tax) collapsed by default with smart defaults applied (Moderate 7% return, inflation off, tax off) and "Using defaults" hint visible when collapsed
- Clean and neutral aesthetic: white/light gray background, subtle borders, system font stack, professional utility tool feel
- CSS approach: Claude's discretion — pick what integrates best with Flask SSR + HTMX

### Validation and feedback
- Validation fires on submit only (server-side, fits SSR model naturally)
- Errors displayed inline under each offending field with red text and clear message
- Page scrolls to first error if needed
- Reasonable range validation: APR 0-40%, term 1-360 months, down payment <= purchase price, return rate 0-30%
- Submit button label: "Compare Options"

### Claude's Discretion
- CSS framework/approach (Tailwind, plain CSS, classless library — whatever integrates best)
- Exact spacing, typography, and border styles
- Form field widths and input formatting (e.g., currency prefix, percentage suffix)
- How the "Reset / Start Over" button looks and where it sits
- Mobile sticky "View Results" anchor implementation details

</decisions>

<specifics>
## Specific Ideas

- Option cards should feel like a well-designed calculator — clean, functional, not flashy
- The mockup layout: editable name + type dropdown + remove button in card header; type-specific fields in card body
- Default scenario (Cash vs Loan) immediately communicates what the tool does without any setup
- "Using defaults" hint on collapsed settings section — transparency without visual clutter

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `FinancingOption` dataclass with `OptionType` enum and optional fields (src/fathom/models.py) — form fields map directly to this model
- `GlobalSettings` dataclass (src/fathom/models.py) — maps to the global settings section
- `compare()` function (src/fathom/engine.py) — accepts list of FinancingOption + GlobalSettings, returns ComparisonResult
- `OptionType` enum values define the 6 types the form dropdown must offer

### Established Patterns
- Pure Python package in src/fathom/ with Decimal arithmetic throughout
- pyproject.toml configured with ruff (including D docstring rules), ty, pyrefly, prek
- Python 3.14, uv for package management
- No web framework installed yet — Flask needs to be added as dependency

### Integration Points
- Form submission creates FinancingOption instances + GlobalSettings from POST data
- Calls `compare()` and passes ComparisonResult to results template (Phase 3 renders it)
- Phase 2 needs a "results placeholder" — form submits but full results display is Phase 3
- HTMX for type-switching field swaps (partial page replacement of option card body)

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-web-layer-and-input-forms*
*Context gathered: 2026-03-10*
