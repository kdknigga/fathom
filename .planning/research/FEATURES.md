# Feature Landscape

**Domain:** Financing comparison calculator (consumer-facing, purchase-agnostic)
**Researched:** 2026-03-10
**Confidence:** MEDIUM (based on PRD analysis, competitor site inspection, and domain expertise; web search unavailable for validation)

## Table Stakes

Features users expect from any financing/loan comparison tool. Missing any of these and the product feels broken or amateur.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Loan payment calculation (principal + interest) | Core math every calculator does. Users will test against known values. | Low | Standard amortization formula. Must be exact to the penny. |
| Side-by-side option comparison | The entire point of a comparison tool. Bankrate, NerdWallet, and every competitor does this. | Medium | PRD specifies 2-4 options. Two is the minimum useful comparison. |
| Multiple financing types (cash, loan, promo) | Users arrive with a specific scenario: "should I take 0% or pay cash?" Must support both sides. | Medium | PRD defines 6 types. Cash + traditional loan + 0% promo are the essential three. |
| Monthly payment display | First thing users look for. It's the anchor metric they already understand. | Low | Trivial from amortization calculation. |
| Total interest paid | Second most expected output. Every loan calculator shows this. | Low | Sum of payments minus principal. |
| Clear "winner" recommendation | Users want an answer, not a spreadsheet. "Option B saves you $X" is the minimum. | Medium | PRD calls this the Summary Recommendation Card. Plain English required. |
| Responsive layout (mobile + desktop) | Over 60% of consumer finance traffic is mobile. Non-negotiable. | Medium | PRD specifies two-column desktop, stacked mobile with sticky anchor. |
| Input validation with helpful errors | Financial inputs have constraints (positive numbers, reasonable ranges). Bad input = wrong results = lost trust. | Medium | Validate on server side. Show clear field-level errors. |
| Accessible form controls (WCAG 2.1 AA) | Legal and ethical requirement. PRD mandates it. Screen reader users are a real audience for financial tools. | Medium | Visible labels, proper ARIA, focus management. Not optional. |
| Reset/clear form | Users experiment with multiple scenarios. Must be able to start over easily. | Low | PRD specifies "Reset / Start Over" button. |
| Purchase price as primary input | Universal anchor for all financing types. Every competitor starts here. | Low | Single global field. |

## Differentiators

Features that set Fathom apart from the sea of basic loan calculators. These are why someone would use Fathom instead of Bankrate.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Opportunity cost modeling | **The core differentiator.** No mainstream calculator answers "what if I invested the cash instead?" This is the entire thesis of Fathom. | High | Requires compound growth calculation over the comparison period. Configurable return rate with presets (Conservative 4%, Moderate 7%, Aggressive 10%) plus manual override. |
| True Total Cost metric | Synthesizes payments + opportunity cost - rebates - tax savings +/- inflation into one comparable number. This is what users cannot do in their heads. | High | The novel metric. Must be clearly explained so users trust it. |
| Comparison period normalization | When comparing a 24-month promo vs a 60-month loan, most calculators fail. Fathom models freed-up cash being invested after shorter loans end. | High | Critical for honest comparisons. Without this, shorter terms always look cheaper. |
| Plain-English recommendation with caveats | "Take the 0% financing. This saves you $2,340 because your $18K earns more invested than the loan costs." Competitors show numbers; Fathom explains. | Medium | Requires templated natural language generation. Must handle edge cases (ties, marginal differences, deferred interest warnings). |
| Cumulative cost over time chart | Shows breakeven points visually. "When does paying cash catch up?" is a powerful insight no basic calculator provides. | Medium | Line chart with one series per option over the comparison period. Server-rendered SVG preferred. |
| Inflation adjustment (optional) | For long-term financing (48-60 months), inflation materially affects present-value comparisons. Toggle-able to avoid overwhelming casual users. | Medium | Discount future cash flows to present value. Off by default per PRD. |
| Tax implications modeling (optional) | Mortgage interest deduction and some loan interest is tax-deductible. This changes the calculus for higher-bracket users. | Medium | Marginal tax rate input, applied to interest payments. Off by default. |
| Deferred interest warning | 0% promo deals often have deferred interest clauses that devastate consumers who miss a payment. Flagging this is consumer advocacy. | Low | Boolean toggle per promo option. Surfaces as caveat in recommendation. |
| Live result updates (HTMX) | Change an input, see results update without full page reload. Makes exploration feel instant and encourages "what if" thinking. | Medium | HTMX partial page replacement. Calculate button as fallback. |
| Cost breakdown table | Detailed row-by-row decomposition (payments, interest, opportunity cost, rebates, tax savings, inflation, True Total Cost) with one column per option. | Medium | The "show your work" complement to the recommendation card. Builds trust. |
| True Total Cost bar chart | At-a-glance visual comparison. Winner highlighted. Accessible (patterns + labels, not just color). | Low | Simple bar chart. Server-rendered SVG is straightforward. |

## Anti-Features

Features to explicitly NOT build. Each one was considered and rejected for good reasons.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| User accounts and saved scenarios | Conflicts with privacy-first design. Adds authentication complexity, database dependency, GDPR concerns. The entire value prop is "quick anonymous comparison." | Stateless per-request. Users bookmark or screenshot results. |
| PDF export or shareable links | Significant complexity for v1 (PDF rendering, URL-encoded state, link rot). Users have screenshots. | Defer to v2 if demand materializes. Ensure the results page prints cleanly with CSS `@media print`. |
| Live interest rate feeds / bank API integration | External dependency risk, rate staleness, API costs, maintenance burden. Rates change daily; stale data is worse than user-entered data. | User enters their quoted rates. Add helper text: "Check your lender's current rate." |
| More than 4 simultaneous options | UI becomes unreadable. Table columns overflow. Chart legends crowd. Diminishing returns -- most decisions are between 2-3 options. | Hard cap at 4 per PRD. Two columns minimum. |
| Business/commercial calculations | Depreciation, asset write-offs, Section 179 deductions are a different product for a different audience. Scope creep that dilutes consumer focus. | Keep "consumer" in the tagline. Business users have accountants. |
| Amortization schedule display | Full month-by-month amortization tables are table stakes for dedicated loan calculators but noise for a comparison tool. Users get lost in 60 rows of data. | Show the cumulative cost chart instead -- it conveys the same temporal information in a more useful format. |
| Multi-currency support | Adds complexity (exchange rates, formatting) for minimal user base. Loan math is currency-agnostic -- just numbers. | Use locale-appropriate number formatting. No currency conversion. |
| Wizard/multi-step form flow | Hides context. Users need to see all options simultaneously to understand the comparison. Multi-step flows increase abandonment. | Single-page form per PRD. All inputs visible. Conditional fields shown/hidden by option type. |
| Client-side calculation logic | Duplicating Python math in JavaScript creates divergence bugs. Server is the source of truth. | All math server-side. HTMX handles the request/response cycle. Minimal JS for UI interactions only. |
| Dark mode (v1) | Nice-to-have that adds CSS complexity and testing burden. Not a launch blocker for a utility tool. | Ship with a clean light theme. Respect `prefers-color-scheme` in v2 if requested. |

## Feature Dependencies

```
Purchase Price input --> All calculation outputs (nothing works without it)
Option Type selector --> Conditional field display (fields depend on type)
Financing option inputs --> Payment calculations --> Total interest
Payment calculations --> True Total Cost calculation
Investment Return Rate --> Opportunity cost calculation --> True Total Cost
Inflation toggle --> Inflation rate input visibility
Inflation rate + cash flows --> Inflation-adjusted True Total Cost
Tax toggle --> Tax rate input visibility
Tax rate + interest payments --> Tax savings --> True Total Cost
True Total Cost (all options) --> Comparison period normalization
True Total Cost (all options) --> Summary recommendation card
True Total Cost (all options) --> Cost breakdown table
True Total Cost (all options) --> Bar chart
Monthly cash flow series --> Cumulative cost over time line chart
HTMX integration --> Live result updates (requires server endpoints returning HTML fragments)
```

## MVP Recommendation

Prioritize in this order:

1. **Calculation engine with opportunity cost** -- This is the product. Without accurate True Total Cost math, nothing else matters. Build and thoroughly test the core: amortization, opportunity cost, comparison period normalization.

2. **Input form with 3 core option types** -- Cash, traditional loan, and 0% promotional financing cover the overwhelming majority of consumer scenarios. Add the other 3 types (cash-back, price reduction, custom) in a fast follow.

3. **Summary recommendation card** -- The plain-English "here's what to do" is what makes Fathom accessible to non-financial users. This is the primary output.

4. **Cost breakdown table** -- Shows the math behind the recommendation. Builds trust. Straightforward to render server-side.

5. **True Total Cost bar chart** -- Simple visual comparison. Server-rendered SVG keeps it dependency-free.

6. **Cumulative cost over time line chart** -- More complex to render but delivers the breakeven insight that no competitor offers.

7. **HTMX live updates** -- Upgrade from full-page form submission to partial updates. Can ship with a Calculate button first and add HTMX progressively.

8. **Optional toggles (inflation, tax)** -- These refine accuracy but add cognitive load. Ship them disabled by default, behind toggles, after the core flow works.

**Defer:**
- Cash-back rebate and price reduction option types: lower frequency scenarios, add after core 3 types are solid
- Custom/Other option type: escape hatch for edge cases, lowest priority
- Print-friendly CSS: nice to have, not launch-critical
- Advanced input validation (reasonable ranges, "did you mean percent not decimal?"): ship basic validation first, refine based on user confusion

## Competitive Landscape Notes

Existing financing calculators (Bankrate, NerdWallet, Calculator.net, Dinkytown) universally focus on single-loan analysis or simple side-by-side payment comparison. None of them model opportunity cost, and none normalize across different term lengths. Fathom's "True Total Cost" framing -- accounting for what your cash could have earned -- is genuinely novel in the consumer calculator space. The closest concept exists in financial advisor tools and spreadsheet templates shared in personal finance communities, but not as an accessible web app.

The risk is not competition; it is explanation. Users must understand and trust the True Total Cost metric, or they will default to the familiar "lowest monthly payment" heuristic. The plain-English recommendation and the visual charts are not just nice UI -- they are essential for the product to deliver its value.

## Sources

- Fathom PRD (docs/PRD.md) -- primary source for requirements and scope decisions
- Fathom PROJECT.md (.planning/PROJECT.md) -- validated requirements and constraints
- NerdWallet loan calculator (nerdwallet.com) -- competitor inspection (limited detail from fetch)
- Dinkytown loan comparison calculator (dinkytown.net) -- competitor inspection (limited detail from fetch)
- Domain expertise: standard loan calculator features, consumer finance UX patterns, amortization math
- Confidence: MEDIUM overall. Competitor analysis was limited by inability to fully scrape calculator UIs. Feature categorization is based on domain knowledge and PRD analysis rather than systematic competitive audit.
