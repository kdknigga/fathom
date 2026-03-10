# Requirements: Fathom

**Defined:** 2026-03-10
**Core Value:** Users can instantly see which financing option truly costs least when opportunity costs, inflation, and taxes are factored in.

## v1 Requirements

### Input Form

- [ ] **FORM-01**: User can enter purchase price as primary input
- [ ] **FORM-02**: User can set investment return rate via presets (Conservative 4%, Moderate 7%, Aggressive 10%) or manual override
- [ ] **FORM-03**: User can toggle inflation adjustment and enter custom inflation rate (default 3%)
- [ ] **FORM-04**: User can toggle tax implications and enter marginal tax rate (default 22%)
- [ ] **FORM-05**: User can define 2-4 financing options to compare
- [ ] **FORM-06**: User can select option type which reveals relevant fields for that type
- [ ] **FORM-07**: User can reset form to defaults via "Reset / Start Over" button

### Option Types

- [ ] **OPTY-01**: User can configure "Pay in Full (Cash)" option (no additional fields)
- [ ] **OPTY-02**: User can configure "Traditional Loan" option (APR, term, down payment)
- [ ] **OPTY-03**: User can configure "0% Promotional Financing" option (promo term, down payment, deferred interest toggle)
- [ ] **OPTY-04**: User can configure "Promo with Cash-Back Rebate" option (APR, term, cash-back amount, down payment)
- [ ] **OPTY-05**: User can configure "Promo with Price Reduction" option (discounted price, APR, term, down payment)
- [ ] **OPTY-06**: User can configure "Custom/Other" option (effective APR, term, upfront cash, optional label)

### Calculation Engine

- [ ] **CALC-01**: System computes total payments (principal + interest) for each option using standard amortization
- [ ] **CALC-02**: System computes opportunity cost of upfront cash (down payment or full price) invested at user-specified return rate
- [ ] **CALC-03**: System normalizes all options to the same comparison period (longest term among active options)
- [ ] **CALC-04**: System models freed-up cash (after shorter loan ends) as invested for remainder of comparison period
- [ ] **CALC-05**: System computes True Total Cost = total payments + opportunity cost - rebates - tax savings ± inflation adjustment
- [ ] **CALC-06**: System applies inflation adjustment when enabled (discount future cash flows to present value)
- [ ] **CALC-07**: System computes tax savings when enabled (deductible interest × marginal tax rate)
- [ ] **CALC-08**: System uses Decimal arithmetic for all monetary calculations (no float for money)

### Results Display

- [ ] **RSLT-01**: User sees a summary recommendation card naming the winning option with plain-English explanation
- [ ] **RSLT-02**: User sees savings amount compared to next-best option in plain English
- [ ] **RSLT-03**: User sees caveats flagged on the recommendation (e.g., deferred interest risk)
- [ ] **RSLT-04**: User sees cost breakdown table with one column per option showing: total payments, total interest, rebates, opportunity cost, tax savings, inflation adjustment, True Total Cost
- [ ] **RSLT-05**: User sees True Total Cost bar chart comparing all options with winner highlighted
- [ ] **RSLT-06**: User sees cumulative cost over time line chart showing month-by-month out-of-pocket evolution
- [ ] **RSLT-07**: Results update via HTMX partial page replacement when inputs change
- [ ] **RSLT-08**: A visible "Calculate" button is always present as fallback

### Accessibility

- [ ] **A11Y-01**: All form inputs have visible labels (WCAG 2.1 AA)
- [ ] **A11Y-02**: Charts include accessible text alternatives (data tables or ARIA labels)
- [ ] **A11Y-03**: Color is not the sole differentiator in charts (patterns or labels used as well)

### Layout & UX

- [ ] **LYOT-01**: Desktop displays two-column layout (inputs left, results right)
- [ ] **LYOT-02**: Mobile/tablet displays single-column stacked layout with sticky "View Results" anchor
- [ ] **LYOT-03**: All labels and copy use plain, consumer-friendly language (no jargon)

### Technical

- [ ] **TECH-01**: All financial calculations are server-side Python — no client-side JS calculation logic
- [ ] **TECH-02**: No user data persisted on server beyond single request/response cycle
- [ ] **TECH-03**: Form inputs repopulated on response so values are not lost between submissions
- [ ] **TECH-04**: Application runs as single deployable Python process with no external database
- [ ] **TECH-05**: Dockerfile provided for containerized self-hosting
- [ ] **TECH-06**: Configuration overridable via environment variables (default rates, branding)
- [ ] **TECH-07**: README with clear self-hosting instructions
- [ ] **TECH-08**: Open-source license (MIT or Apache 2.0)

### Performance

- [ ] **PERF-01**: Results page rendered within 300ms of form submission

## v2 Requirements

### Enhancements

- **ENH-01**: Print-friendly CSS for results page
- **ENH-02**: Dark mode / `prefers-color-scheme` support
- **ENH-03**: Advanced input validation (reasonable ranges, "did you mean percent not decimal?")
- **ENH-04**: Exportable PDF or shareable reports
- **ENH-05**: Scenario comparison (save multiple parameter sets for side-by-side)

## Out of Scope

| Feature | Reason |
|---------|--------|
| User accounts or cloud-synced history | Conflicts with privacy-first, stateless design |
| Live interest rate feeds / bank API integration | External dependency risk, staleness, API costs |
| More than 4 simultaneous options | UI becomes unreadable, diminishing returns |
| Business calculations (depreciation, write-offs) | Different product for different audience |
| Mobile native app | Web-first approach, responsive design sufficient |
| Offline support | Server-rendered application |
| Multi-currency support | Adds complexity for minimal user base; math is currency-agnostic |
| Amortization schedule display | Noise for comparison tool; cumulative chart conveys same info better |
| Wizard/multi-step form | Hides context; single-page comparison needs all options visible |
| Client-side calculation logic | Creates divergence bugs; server is source of truth |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FORM-01 | — | Pending |
| FORM-02 | — | Pending |
| FORM-03 | — | Pending |
| FORM-04 | — | Pending |
| FORM-05 | — | Pending |
| FORM-06 | — | Pending |
| FORM-07 | — | Pending |
| OPTY-01 | — | Pending |
| OPTY-02 | — | Pending |
| OPTY-03 | — | Pending |
| OPTY-04 | — | Pending |
| OPTY-05 | — | Pending |
| OPTY-06 | — | Pending |
| CALC-01 | — | Pending |
| CALC-02 | — | Pending |
| CALC-03 | — | Pending |
| CALC-04 | — | Pending |
| CALC-05 | — | Pending |
| CALC-06 | — | Pending |
| CALC-07 | — | Pending |
| CALC-08 | — | Pending |
| RSLT-01 | — | Pending |
| RSLT-02 | — | Pending |
| RSLT-03 | — | Pending |
| RSLT-04 | — | Pending |
| RSLT-05 | — | Pending |
| RSLT-06 | — | Pending |
| RSLT-07 | — | Pending |
| RSLT-08 | — | Pending |
| A11Y-01 | — | Pending |
| A11Y-02 | — | Pending |
| A11Y-03 | — | Pending |
| LYOT-01 | — | Pending |
| LYOT-02 | — | Pending |
| LYOT-03 | — | Pending |
| TECH-01 | — | Pending |
| TECH-02 | — | Pending |
| TECH-03 | — | Pending |
| TECH-04 | — | Pending |
| TECH-05 | — | Pending |
| TECH-06 | — | Pending |
| TECH-07 | — | Pending |
| TECH-08 | — | Pending |
| PERF-01 | — | Pending |

**Coverage:**
- v1 requirements: 42 total
- Mapped to phases: 0
- Unmapped: 42 ⚠️

---
*Requirements defined: 2026-03-10*
*Last updated: 2026-03-10 after initial definition*
