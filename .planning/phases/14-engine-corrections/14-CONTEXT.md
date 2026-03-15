# Phase 14: Engine Corrections - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix promo penalty modeling so deferred-interest flags actually change the calculation path, and correct the line chart to plot cumulative true cost instead of cumulative payments. Includes tests proving correctness with specific dollar amounts.

Requirements: ENG-01, ENG-02, TEST-01, TEST-02

</domain>

<decisions>
## Implementation Decisions

### Deferred-Interest Business Rule
- **Retroactive (deferred) interest:** When promo expires unpaid, retroactive interest is calculated on the FULL original financed principal (purchase_price - down_payment) at the post-promo APR for the entire promo term. This is added as a lump sum to the remaining balance at the promo boundary (month 13 for a 12-month promo).
- **Forward-only interest:** When promo expires unpaid WITHOUT deferred-interest, post-promo APR applies only to the remaining balance — no retroactive charges. This makes forward-only strictly cheaper than retroactive.
- **Both branches must produce visibly different costs.** The current bug is that both branches are identical.

### Promo Not-Paid-On-Time Modeling
- **Minimum payments during promo:** Model realistic minimum payments during the 0% promo period. Minimum payment = `required_monthly / 2` (where `required_monthly = principal / term`).
- **Down payment:** Same down payment applies to both paid and not-paid scenarios (already paid regardless).
- **Post-promo amortization term:** Same duration as the promo term (e.g., 12-month promo → 12-month post-promo amortization). Total timeline = 2× promo term.
- **Retroactive interest timing:** Added as lump sum at promo boundary (month 13), not spread across post-promo period. Chart will show a sharp cost jump at the transition.

### Worked Numeric Example (must appear as code comment)
- $10K purchase, 24.99% APR, 12-month promo, no down payment
- `required_monthly = $10,000 / 12 = $833.33`
- `min_payment = $833.33 / 2 = $416.67`
- Remaining principal at month 13: `$10,000 - (12 × $416.67) = ~$5,000`
- **Retroactive:** remaining $5,000 + retroactive interest ($10,000 × 24.99% × 1yr = $2,499) = $7,499 amortized at 24.99% for 12 months
- **Forward-only:** remaining $5,000 amortized at 24.99% for 12 months (no retroactive interest)
- **Paid on time:** $10,000 at 0% for 12 months
- **Required invariant:** retroactive cost > forward-only cost > paid-on-time cost

### Line Chart Metric
- **Fix at the source:** Repurpose `MonthlyDataPoint.cumulative_cost` to be cumulative TRUE cost (payment + opportunity_cost - tax_savings + inflation_adjustment). Fix in engine builders so chart and detail table use the same data.
- **Chart label:** Change to "Cumulative True Cost Over Time" to match bar chart/recommendation terminology.
- **Promo options:** Plot BOTH paid-on-time (solid line) and not-paid-on-time (dashed line) as separate lines on the chart.
- **Not-paid line label:** Suffix with "(not paid on time)" — e.g., "Option 2 (not paid on time)".

### Not-Paid-On-Time Data Points
- Single continuous MonthlyDataPoint series covering both promo period (minimum payments, 0% interest) and post-promo period (full amortization at post-promo APR).
- Chart will show a flat-then-steep curve for penalty scenarios.

### Test Strategy
- **Exact cent precision:** Assert exact Decimal values for dollar amounts — engine uses Decimal arithmetic and should be deterministic.
- **Invariant assertions:** Tests must assert `retroactive_cost > forward_only_cost > paid_on_time_cost` using specific dollar amounts from the worked example.
- **Worked example as code comment** above `_build_promo_result()`, with tests asserting against those specific expected values.
- **Chart tests:** Claude's discretion on endpoint-only vs all-points assertions.

### Claude's Discretion
- Chart test thoroughness (endpoint match vs all data points)
- Internal implementation of the two-phase MonthlyDataPoint construction
- How to handle edge cases (e.g., promo term = comparison period, post_promo_apr = 0)
- SVG styling details for dashed penalty lines

</decisions>

<specifics>
## Specific Ideas

- The retroactive interest lump sum at promo boundary should create a visible "cliff" on the chart — this is the whole point of showing both lines
- The worked numeric example in the code comment is a success criterion, not optional
- Both `ty` and `pyrefly` must pass clean — no inline suppressions

</specifics>

<code_context>
## Existing Code Insights

### Key Files to Modify
- `src/fathom/engine.py`: `_build_promo_result()` (lines 279-357) — both if/else branches are identical, this is the core bug
- `src/fathom/charts.py`: `_collect_option_points()` (line 184) reads `dp.cumulative_cost` — currently cumulative payments only
- `src/fathom/models.py`: `MonthlyDataPoint.cumulative_cost` (line 113) — needs to become cumulative true cost

### Reusable Assets
- `src/fathom/money.py`: Canonical `quantize_money()` — all new monetary calculations must import from here (Phase 13)
- `src/fathom/amortization.py`: Existing amortization schedule builder — can be reused for post-promo amortization
- `src/fathom/results.py`: `_monthly_data_to_rows()` already computes correct cumulative true cost formula — reference implementation

### Established Patterns
- Engine builders (`_build_cash_result`, `_build_loan_result`, `_build_promo_result`) all return typed result objects
- `PromoResult` has `paid_on_time` and `not_paid_on_time` fields — structure already supports dual outcomes
- Decimal arithmetic throughout — no floats in financial calculations
- Chart code converts Decimal to float only at the SVG rendering boundary (`_to_float()`)

### Integration Points
- `_collect_option_points()` handles `PromoResult` via `_get_option_result()` — will need to emit both paid and not-paid lines
- `_build_line_dataset()` takes name, index, points — can be called twice per promo option (solid + dashed)
- Existing `LINE_PATTERNS` and `DASH_PATTERNS` constants for line styling

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 14-engine-corrections*
*Context gathered: 2026-03-15*
