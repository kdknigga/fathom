# Phase 3: Results Display and Charts - Context

**Gathered:** 2026-03-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete, accessible results view with recommendation card, cost breakdown table, SVG charts, and HTMX live updates. Users see which financing option wins, why, and how the numbers break down — all updating dynamically when inputs change. No new input capabilities; this phase renders the output of the Phase 1 engine through the Phase 2 form.

</domain>

<decisions>
## Implementation Decisions

### Recommendation card
- Hero card with callout at top of results area — large, prominent, visually distinct from breakdown
- Winner name in bold, savings vs next-best in big text, plain-English "why" sentence below
- Conversational insight tone: "Your money earns more invested than you'd pay in interest." — knowledgeable friend, not data dump
- PromoResult dual outcomes: use paid-on-time result for ranking; penalty scenario shown as caveat ("If not paid off by month X, cost jumps to $Y — pay $Z/mo to avoid this")
- Caveats displayed as inline warnings below the explanation, severity-based styling (amber for warning, red for critical)
- Only caveats for the winning option on the hero card; other options' caveats appear in the breakdown section

### Cost breakdown table
- One column per option showing all engine-computed components: Total Payments, Total Interest, Rebates, Opportunity Cost, Tax Savings, Inflation Adjustment, True Total Cost
- Zero-value rows hidden when a component is $0 for ALL options (e.g., rebates row hidden if no option has rebates)
- PromoResult options get two sub-columns: "If paid on time" and "If not" — other options span both sub-columns
- Winner highlighted with bold + star on True Total Cost cell; winning column header gets subtle background tint
- Mobile: horizontal scroll with sticky row labels (component names) pinned on left

### Chart approach
- Server-rendered SVG for both bar chart and line chart — zero client-side JS for charts
- Python generates SVG markup from ComparisonResult data, rendered inline in Jinja templates
- Accessibility: each option gets unique SVG fill pattern (solid, hatched, dotted, crosshatch) alongside color
- Direct labels on bars/lines (no legend-only identification)
- Line chart: different dash patterns (solid, dashed, dotted) with direct labels at line endpoints
- Hidden data table (visually-hidden, sr-only) below each chart with the same data for screen readers
- SVG has `<title>` and `<desc>` elements for summary screen reader access
- Line chart X-axis: monthly data points from MonthlyDataPoint, labeled at year boundaries (12, 24, 36...)
- Line chart endpoint labels show final True Total Cost per option

### HTMX live updates
- Button-click only: results update when user clicks "Compare Options" — no debounced auto-update
- Convert existing form to HTMX POST: `hx-post="/compare" hx-target="#results" hx-swap="innerHTML"`
- Progressive enhancement: server detects HX-Request header — HTMX requests return results partial, non-JS falls back to full page render
- Loading indicator: button text changes to "Calculating..." with spinner during request, button disabled
- Mobile auto-scroll: first calculation auto-scrolls to #results; subsequent calculations stay in place (user is tweaking); sticky "View Results" anchor always available

### Verification approach
- All browser-based verification automated via Playwright MCP — no manual browser checks
- Visual layout verification: navigate + screenshot + DOM assertions
- HTMX partial swap verification: click Compare, assert DOM changed without full reload
- Responsive design verification: resize viewport, assert layout changes (table scroll, stacked layout)
- Chart rendering: verify SVG content, ARIA attributes, pattern elements
- Accessibility: query ARIA roles/labels, verify hidden data tables, check color-not-only compliance

### Claude's Discretion
- SVG chart dimensions, colors, and exact pattern definitions
- Exact CSS styling for hero card, table, and charts (within Pico CSS framework)
- How caveats for non-winning options are displayed in breakdown section
- Loading spinner implementation details
- SVG generation approach (template-based vs string building vs library)

</decisions>

<specifics>
## Specific Ideas

- Hero card star icon consistent with winner star in breakdown table — same visual language
- Conversational insight examples: "Your money earns more invested than you'd pay in interest," "Paying cash means missing out on $X in returns," "The 0% promo saves the most IF you pay it off in 12 months"
- Promo penalty caveat should include both the cost jump AND the required monthly payment to avoid it — actionable, not just a warning
- Clean utility-tool aesthetic inherited from Phase 2 — not flashy, just informative

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ComparisonResult` dataclass (models.py:164): `results` dict mapping option names to `OptionResult|PromoResult`, `comparison_period_months`, `caveats` list
- `OptionResult` dataclass (models.py:116): all cost components (total_payments, total_interest, opportunity_cost, tax_savings, inflation_adjustment, rebates, true_total_cost) + `monthly_data` list
- `PromoResult` dataclass (models.py:135): `paid_on_time` and `not_paid_on_time` OptionResults, `required_monthly_payment`, `break_even_month`
- `MonthlyDataPoint` dataclass (models.py:99): month, payment, interest/principal portions, remaining_balance, investment_balance, cumulative_cost — ready for line chart
- `Caveat` dataclass (models.py:150): caveat_type (CaveatType enum), message, severity (Severity enum)
- `compare()` function (engine.py): accepts FinancingOptions + GlobalSettings, returns ComparisonResult
- `compare_options` route (routes.py:292): already calls engine, passes results to template context
- `_build_template_context` helper (routes.py): already accepts optional `results` parameter

### Established Patterns
- Pico CSS framework (CDN) for base styling, custom styles in `static/style.css`
- HTMX 2.0.8 already loaded in `base.html`
- Jinja2 templates with partials pattern (`templates/partials/`)
- Card-based UI sections (`<article>` elements per Pico conventions)
- Form HTMX already proven: type-switching uses `hx-post`/`hx-target`/`hx-swap` pattern

### Integration Points
- Results render inside `<article id="results">` in index.html (currently placeholder text)
- Form `action="/compare"` and existing `compare_options()` route need HTMX enhancement (hx-post, HX-Request detection)
- Sticky `.sticky-results-anchor` already exists for mobile scroll
- Results partial template needs to be created and returned conditionally based on HX-Request header

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-results-display-and-charts*
*Context gathered: 2026-03-10*
