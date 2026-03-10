# Requirements: Fathom

**Defined:** 2026-03-10
**Core Value:** Users can instantly see which financing option truly costs least when opportunity costs, inflation, and taxes are factored in.

## v1 Requirements

### Input Form

- [x] **FORM-01**: User can enter purchase price as primary input
- [x] **FORM-02**: User can set investment return rate via presets (Conservative 4%, Moderate 7%, Aggressive 10%) or manual override
- [x] **FORM-03**: User can toggle inflation adjustment and enter custom inflation rate (default 3%)
- [x] **FORM-04**: User can toggle tax implications and enter marginal tax rate (default 22%)
- [x] **FORM-05**: User can define 2-4 financing options to compare
- [x] **FORM-06**: User can select option type which reveals relevant fields for that type
- [x] **FORM-07**: User can reset form to defaults via "Reset / Start Over" button

### Option Types

- [x] **OPTY-01**: User can configure "Pay in Full (Cash)" option (no additional fields)
- [x] **OPTY-02**: User can configure "Traditional Loan" option (APR, term, down payment)
- [x] **OPTY-03**: User can configure "0% Promotional Financing" option (promo term, down payment, deferred interest toggle)
- [x] **OPTY-04**: User can configure "Promo with Cash-Back Rebate" option (APR, term, cash-back amount, down payment)
- [x] **OPTY-05**: User can configure "Promo with Price Reduction" option (discounted price, APR, term, down payment)
- [x] **OPTY-06**: User can configure "Custom/Other" option (effective APR, term, upfront cash, optional label)

### Calculation Engine

- [x] **CALC-01**: System computes total payments (principal + interest) for each option using standard amortization
- [x] **CALC-02**: System computes opportunity cost of upfront cash (down payment or full price) invested at user-specified return rate
- [x] **CALC-03**: System normalizes all options to the same comparison period (longest term among active options)
- [x] **CALC-04**: System models freed-up cash (after shorter loan ends) as invested for remainder of comparison period
- [x] **CALC-05**: System computes True Total Cost = total payments + opportunity cost - rebates - tax savings ± inflation adjustment
- [x] **CALC-06**: System applies inflation adjustment when enabled (discount future cash flows to present value)
- [x] **CALC-07**: System computes tax savings when enabled (deductible interest × marginal tax rate)
- [x] **CALC-08**: System uses Decimal arithmetic for all monetary calculations (no float for money)

### Results Display

- [x] **RSLT-01**: User sees a summary recommendation card naming the winning option with plain-English explanation
- [x] **RSLT-02**: User sees savings amount compared to next-best option in plain English
- [x] **RSLT-03**: User sees caveats flagged on the recommendation (e.g., deferred interest risk)
- [x] **RSLT-04**: User sees cost breakdown table with one column per option showing: total payments, total interest, rebates, opportunity cost, tax savings, inflation adjustment, True Total Cost
- [x] **RSLT-05**: User sees True Total Cost bar chart comparing all options with winner highlighted
- [x] **RSLT-06**: User sees cumulative cost over time line chart showing month-by-month out-of-pocket evolution
- [x] **RSLT-07**: Results update via HTMX partial page replacement when inputs change
- [x] **RSLT-08**: A visible "Calculate" button is always present as fallback

### Accessibility

- [x] **A11Y-01**: All form inputs have visible labels (WCAG 2.1 AA)
- [x] **A11Y-02**: Charts include accessible text alternatives (data tables or ARIA labels)
- [x] **A11Y-03**: Color is not the sole differentiator in charts (patterns or labels used as well)

### Layout & UX

- [x] **LYOT-01**: Desktop displays two-column layout (inputs left, results right)
- [x] **LYOT-02**: Mobile/tablet displays single-column stacked layout with sticky "View Results" anchor
- [x] **LYOT-03**: All labels and copy use plain, consumer-friendly language (no jargon)

### Technical

- [x] **TECH-01**: All financial calculations are server-side Python — no client-side JS calculation logic
- [x] **TECH-02**: No user data persisted on server beyond single request/response cycle
- [x] **TECH-03**: Form inputs repopulated on response so values are not lost between submissions
- [x] **TECH-04**: Application runs as single deployable Python process with no external database
- [x] **TECH-05**: Dockerfile provided for containerized self-hosting
- [x] **TECH-06**: Configuration overridable via environment variables (default rates, branding)
- [x] **TECH-07**: README with clear self-hosting instructions
- [x] **TECH-08**: Open-source license (MIT or Apache 2.0)

### Code Quality

- [x] **QUAL-01**: All code passes `ruff check` with zero errors (no `# noqa` suppression)
- [x] **QUAL-02**: All code passes `ruff format` (Black-compatible, double quotes, 88 char lines)
- [x] **QUAL-03**: All code passes `ty check` with zero errors (no `# type: ignore` suppression)
- [x] **QUAL-04**: All code passes `pyrefly check` with zero errors (no error suppression)
- [x] **QUAL-05**: All public modules, classes, and functions have docstrings (ruff `D` rules)
- [x] **QUAL-06**: `prek` pre-commit hooks pass on all commits

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
| CALC-01 | Phase 1 | Complete |
| CALC-02 | Phase 1 | Complete |
| CALC-03 | Phase 1 | Complete |
| CALC-04 | Phase 1 | Complete |
| CALC-05 | Phase 1 | Complete |
| CALC-06 | Phase 1 | Complete |
| CALC-07 | Phase 1 | Complete |
| CALC-08 | Phase 1 | Complete |
| TECH-01 | Phase 1 | Complete |
| TECH-02 | Phase 1 | Complete |
| TECH-04 | Phase 1 | Complete |
| QUAL-01 | Phase 1 | Complete |
| QUAL-02 | Phase 1 | Complete |
| QUAL-03 | Phase 1 | Complete |
| QUAL-04 | Phase 1 | Complete |
| QUAL-05 | Phase 1 | Complete |
| QUAL-06 | Phase 1 | Complete |
| FORM-01 | Phase 2 | Complete |
| FORM-02 | Phase 2 | Complete |
| FORM-03 | Phase 2 | Complete |
| FORM-04 | Phase 2 | Complete |
| FORM-05 | Phase 2 | Complete |
| FORM-06 | Phase 2 | Complete |
| FORM-07 | Phase 2 | Complete |
| OPTY-01 | Phase 2 | Complete |
| OPTY-02 | Phase 2 | Complete |
| OPTY-03 | Phase 2 | Complete |
| OPTY-04 | Phase 2 | Complete |
| OPTY-05 | Phase 2 | Complete |
| OPTY-06 | Phase 2 | Complete |
| A11Y-01 | Phase 2 | Complete |
| LYOT-01 | Phase 2 | Complete |
| LYOT-02 | Phase 2 | Complete |
| LYOT-03 | Phase 2 | Complete |
| TECH-03 | Phase 2 | Complete |
| RSLT-01 | Phase 3 | Complete |
| RSLT-02 | Phase 3 | Complete |
| RSLT-03 | Phase 3 | Complete |
| RSLT-04 | Phase 3 | Complete |
| RSLT-05 | Phase 3 | Complete |
| RSLT-06 | Phase 3 | Complete |
| RSLT-07 | Phase 3 | Complete |
| RSLT-08 | Phase 3 | Complete |
| A11Y-02 | Phase 3 | Complete |
| A11Y-03 | Phase 3 | Complete |
| TECH-05 | Phase 4 | Complete |
| TECH-06 | Phase 4 | Complete |
| TECH-07 | Phase 4 | Complete |
| TECH-08 | Phase 4 | Complete |
| PERF-01 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 48 total
- Mapped to phases: 48
- Unmapped: 0

---
*Requirements defined: 2026-03-10*
*Last updated: 2026-03-10 after roadmap creation*
