# Phase 9: Tooltips and Tax Guidance - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Users understand every financial term in the form and results without leaving the page. Popover explanations on all form fields and result terms, plus a tax bracket reference widget. No new calculation features, no new form fields — only explanatory content layered onto existing UI.

</domain>

<decisions>
## Implementation Decisions

### Tooltip mechanism
- Native HTML `popover` attribute + `popovertarget` for show/hide — zero custom JS for core behavior
- `popover="auto"` (default) — browser auto-closes other popovers, only one open at a time
- Click/tap only to open — no hover behavior. Consistent across mouse, keyboard, and touch
- CSS Anchor Positioning API for popover placement near trigger — graceful fallback to top-center viewport for older browsers
- Escape to dismiss, click-outside to dismiss — all handled natively by popover API

### Content depth
- Short paragraph + concrete example for every tooltip (2-3 sentences: definition + why it matters + example)
- Same style for both form field tooltips and result metric tooltips — consistent experience
- Claude drafts all tooltip copy during implementation, based on the calculation engine's actual logic
- Every form field gets a tooltip — including self-explanatory ones like Purchase Price (brief note) alongside complex ones like Deferred Interest (detailed explanation)

### Tooltip trigger and placement
- Styled `<button class="tip">?</button>` — small circle, muted color, ~16px, vertically centered with label
- Dark mode variant via CSS variables (consistent with existing dark mode system)
- Placed after the label text, before the input field: "Annual Interest Rate (APR) ?"
- Proper focus ring for keyboard accessibility

### Result metric tooltips
- ? icon after each row label in the breakdown table (Interest, Opportunity Cost, Inflation Adj, Tax Savings, True Total Cost)
- ? icon next to "True Total Cost" in the recommendation card — same popover content as the breakdown table
- Chart titles do NOT get tooltips — charts are visual aids, the table explanations suffice

### Tax bracket widget
- Expandable HTML `<details>` element below the tax rate field — "What's my bracket?"
- Shows 2025 IRS brackets for Single and Married Filing Jointly side-by-side in one table
- All 7 federal rates (10%–37%) with income ranges
- Bracket data defined in Python (list of dicts), rendered via Jinja template — single source of truth, easy to update yearly
- Clicking a bracket row auto-fills the tax rate input with that rate — rows highlight on hover, cursor: pointer
- Uses existing `|comma` Jinja filter for income range formatting (from Phase 8)

### Accessibility (WCAG 1.4.13 compliance)
- All tooltips are keyboard-focusable via the `<button>` trigger
- Escape dismisses any open popover (native popover API)
- Content is persistent until explicitly dismissed (click-only, no auto-timeout)
- Popover content is hoverable without disappearing (native behavior — popover stays open until light-dismiss)
- Tax bracket table rows are keyboard-activatable (Enter/Space to select rate)

### Claude's Discretion
- Exact tooltip copy for all fields and metrics
- Popover arrow/caret styling (or no arrow)
- Popover max-width and padding
- Whether to add a small close button inside popovers or rely entirely on light-dismiss
- Dark mode color palette for popover background/border
- Tax bracket table styling details (borders, spacing, selected-row highlight color)

</decisions>

<specifics>
## Specific Ideas

No specific references — open to standard approaches. The goal is clear, plain-English financial education embedded directly in the UI. Tooltips should feel like having a knowledgeable friend explain each term, not reading a textbook.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- **HTML `<details>` pattern**: Already used in Global Settings collapse — proven pattern for the tax bracket widget
- **Event delegation on `#comparison-form`**: `formatting.js` demonstrates delegated listeners that survive HTMX swaps — same pattern if any tooltip JS needed
- **`.visually-hidden` utility**: Exists in `style.css` for screen-reader-only text
- **`|comma` Jinja filter**: From Phase 8 — reuse for formatting income ranges in tax bracket table
- **CSS custom properties system**: Dark mode variables already established — tooltip styles can follow same pattern

### Established Patterns
- **ARIA usage**: `aria-label`, `aria-labelledby`, `role="alert"`, `role="group"`, `scope="col"` all in use
- **Inline helper text**: `<small>` elements already used on some promo fields for brief explanations — tooltips replace/supplement this pattern
- **Pico CSS framework**: Provides base styling; no built-in tooltip component
- **No existing tooltip/popover library**: This will be the first popover implementation

### Integration Points
- **Form field templates**: All option field templates in `src/fathom/templates/partials/option_fields/` — add ? buttons next to labels
- **Global settings**: `src/fathom/templates/partials/global_settings.html` — add ? buttons + tax bracket widget
- **Recommendation card**: `src/fathom/templates/partials/results/recommendation.html` — add ? next to True Total Cost
- **Breakdown table**: `src/fathom/templates/partials/results/breakdown_table.html` — add ? next to row labels
- **`style.css`**: New tooltip/popover styles including dark mode variants
- **Python context**: Tax bracket data needs to be passed to templates via Flask route context

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 09-tooltips-and-tax-guidance*
*Context gathered: 2026-03-13*
