# Phase 11: Detailed Period Breakdown - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can inspect the period-by-period cost composition for each financing option. Per-option tabs with monthly/annual rows showing all cost factors (principal, interest, opportunity cost, inflation adjustment, tax savings). Compare tab for side-by-side view. Column toggles for focusing on specific factors. No new calculation features — this surfaces existing engine data at finer granularity.

</domain>

<decisions>
## Implementation Decisions

### Period granularity
- Default view is **monthly rows**; user can toggle to **annual summary** (12-month aggregation)
- Monthly/annual toggle uses **HTMX server-side aggregation** — server computes annual sums from monthly data, consistent with "all calculations server-side" constraint
- All options show rows for the **full comparison period**, padded with zeros for months beyond the option's term — consistent with how the engine already pads MonthlyDataPoint
- Cash options show full comparison period with zero-payment rows, making opportunity cost accrual visible over time

### Table structure
- **Cumulative True Total Cost column** always visible — shows cost building over time per period
- **Sticky totals row** at the bottom — always visible when scrolling long tables (60+ months), shows column sums
- Promo options use **dual columns** (paid on time / not paid on time) — matching the existing breakdown_table.html pattern with sub-header row

### Tab & compare layout
- **HTMX tab switching** — each tab click fetches the table via HTMX partial swap, consistent with existing codebase patterns (form updates, option type switching)
- **One tab per configured option** + a **Compare tab**
- **Compare tab** shows per-period rows with **Payment + Cumulative True Total Cost** per option (2 columns per option = max 8 data columns + period column)
- **Placement:** below existing summary breakdown table — summary stays as-is, detailed table appears below as a "drill-down"

### Column toggles
- **Checkbox row above the table** — horizontal row of labeled checkboxes, one per cost factor
- **All columns on by default** — user sees full picture immediately, can turn off what they don't need
- **Client-side JS** for toggle visibility — CSS class toggling, no server round-trip for a purely visual concern
- **Column toggle state persists across tab switches** — JS stores hidden column state, applies to each newly loaded tab

### Data gap: engine enhancements
- **Extend MonthlyDataPoint** with per-period `opportunity_cost`, `inflation_adjustment`, and `tax_savings` fields
- Engine already has the per-month payment/interest lists used to compute totals — store per-month results instead of only aggregates
- Single source of truth: per-period values sum to the totals on OptionResult

### Claude's Discretion
- Tab styling (underline tabs, pill tabs, etc.) — should feel native to Pico CSS
- Checkbox row styling and dark mode variants
- Sticky totals row implementation (CSS position: sticky)
- How column toggle JS interacts with HTMX-swapped content (likely needs event delegation or htmx:afterSwap hook)
- MonthlyDataPoint field naming for new per-period cost factors
- Annual aggregation endpoint design (query parameter vs. separate route)
- Compare tab column header formatting when option names are long
- Whether to hide all-zero columns automatically (like breakdown table hides all-zero rows)

</decisions>

<specifics>
## Specific Ideas

No specific references — open to standard approaches. The key principle is that the detailed table is a drill-down companion to the existing summary breakdown table, not a replacement.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`MonthlyDataPoint` model** (`models.py:98-113`): Pydantic BaseModel with per-month payment, interest, principal, remaining_balance, investment_balance, cumulative_cost — needs extension with opp_cost, inflation_adj, tax_savings
- **`OptionResult` model** (`models.py:116-133`): Contains `monthly_data: list[MonthlyDataPoint]` — the data source for detailed tables
- **`_build_breakdown_rows()`** (`results.py:115-170`): Builds the existing summary table rows — pattern for building detailed rows
- **`_BREAKDOWN_COMPONENTS`** (`results.py:69-77`): Label-to-attribute mapping for cost factors — extend or reuse for column definitions
- **`_TOOLTIP_TEXT`** (`results.py`): Existing tooltips for cost factors — reuse in detailed table column headers
- **`breakdown_table.html`**: Existing template with promo dual-column pattern, winner highlighting, tooltip popovers — reference for styling consistency
- **Event delegation pattern** (`formatting.js`): Delegated listeners on `#comparison-form` that survive HTMX swaps — same pattern for column toggles
- **CSS variables system** (`style.css`): Dark mode variables established — new table styles follow same pattern

### Established Patterns
- HTMX partial rendering for dynamic content updates
- Server-side computation with Jinja template rendering
- Pico CSS base styling with custom CSS overrides
- `@media (prefers-color-scheme: dark)` for dark mode variants
- Popover API for tooltips (Phase 9)
- `|comma` Jinja filter for number formatting (Phase 8)

### Integration Points
- **`engine.py`**: `_build_loan_result()`, `_build_cash_result()`, `_build_promo_result()` — extend to compute per-period opp cost, inflation, tax savings
- **`models.py`**: Extend `MonthlyDataPoint` with new Decimal fields
- **`results.py`**: New function to build detailed breakdown data structure from OptionResult.monthly_data
- **`routes.py`**: New HTMX endpoint(s) for tab switching and monthly/annual toggle
- **Templates**: New `detailed_breakdown.html` partial with tab UI, checkbox row, and period table
- **`style.css`**: New styles for tabs, sticky totals row, checkbox row, with dark mode variants
- **New JS file**: Column toggle logic with HTMX afterSwap integration

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 11-detailed-period-breakdown*
*Context gathered: 2026-03-14*
