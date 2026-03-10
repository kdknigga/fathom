# Roadmap: Fathom

## Overview

Fathom delivers a financing options analyzer in four phases: first the calculation engine (the product's core differentiator), then the web form layer, then the results display with charts, and finally deployment hardening. Each phase delivers a coherent, testable capability. The calculation engine comes first because every other component depends on its output types and correctness.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Calculation Engine** - Domain models, financial calculation logic with Decimal arithmetic, code quality tooling (ruff, ty, pyrefly, prek) (completed 2026-03-10)
- [x] **Phase 2: Web Layer and Input Forms** - Flask app, form handling, all option types, responsive layout (completed 2026-03-10)
- [x] **Phase 3: Results Display and Charts** - Recommendation card, cost breakdown, SVG charts, HTMX live updates (completed 2026-03-10)
- [ ] **Phase 4: Deployment and Polish** - Dockerfile, README, env config, performance verification, open-source license

## Phase Details

### Phase 1: Calculation Engine
**Goal**: Users' financing options can be computed correctly with full True Total Cost modeling, verified by automated tests against known values
**Depends on**: Nothing (first phase)
**Requirements**: CALC-01, CALC-02, CALC-03, CALC-04, CALC-05, CALC-06, CALC-07, CALC-08, TECH-01, TECH-02, TECH-04, QUAL-01, QUAL-02, QUAL-03, QUAL-04, QUAL-05, QUAL-06
**Success Criteria** (what must be TRUE):
  1. Given a set of financing options and global settings, the engine returns a ComparisonResult with True Total Cost for each option, computed using Decimal arithmetic (never float for money)
  2. Standard amortization produces correct values verified against known check ($10,000 / 6% APR / 36 months = $304.22/month)
  3. Opportunity cost is computed correctly: full purchase price for cash, down payment only for loans, with freed-up cash invested for remainder of comparison period
  4. The engine normalizes all options to the longest term and models post-payoff cash flows as invested
  5. Inflation adjustment and tax savings toggles produce correct present-value discounting and interest deduction calculations respectively
  6. All code passes ruff check, ruff format, ty check, pyrefly check, and prek hooks with zero errors — no suppression comments
**Plans**: 3 plans

Plans:
- [x] 01-01-PLAN.md — Test infrastructure, domain models, and failing test stubs
- [x] 01-02-PLAN.md — Core calculation modules (amortization, opportunity cost, inflation, tax)
- [x] 01-03-PLAN.md — Engine orchestrator, caveats, and full quality gate

### Phase 2: Web Layer and Input Forms
**Goal**: Users can fill out a complete financing comparison form with all 6 option types, see validation errors, and submit for calculation
**Depends on**: Phase 1
**Requirements**: FORM-01, FORM-02, FORM-03, FORM-04, FORM-05, FORM-06, FORM-07, OPTY-01, OPTY-02, OPTY-03, OPTY-04, OPTY-05, OPTY-06, A11Y-01, LYOT-01, LYOT-02, LYOT-03, TECH-03
**Success Criteria** (what must be TRUE):
  1. User can enter purchase price, configure 2-4 financing options (selecting from all 6 types), set global parameters (return rate, inflation, tax), and submit the form
  2. Selecting an option type reveals only the fields relevant to that type (e.g., "Traditional Loan" shows APR, term, down payment; "Pay in Full" shows nothing extra)
  3. Form displays on desktop as two-column layout (inputs left, results right) and on mobile as stacked single-column with sticky "View Results" anchor
  4. All form inputs have visible labels using plain consumer-friendly language, and form values are repopulated after submission
  5. User can reset the form to defaults via "Reset / Start Over" button
**Plans**: 3 plans

Plans:
- [ ] 02-01-PLAN.md — Flask app factory, templates, responsive layout, and all option field templates
- [ ] 02-02-PLAN.md — Form parsing, validation, HTMX interactivity, and submission handler
- [ ] 02-03-PLAN.md — Quality gate enforcement and visual verification

### Phase 3: Results Display and Charts
**Goal**: Users see a complete, accessible results view with recommendation, cost breakdown, and visualizations that update dynamically
**Depends on**: Phase 2
**Requirements**: RSLT-01, RSLT-02, RSLT-03, RSLT-04, RSLT-05, RSLT-06, RSLT-07, RSLT-08, A11Y-02, A11Y-03
**Success Criteria** (what must be TRUE):
  1. User sees a summary recommendation card naming the cheapest option with plain-English explanation of why it wins, savings vs. next-best option, and caveats (e.g., deferred interest risk)
  2. User sees a cost breakdown table with one column per option showing: total payments, total interest, rebates, opportunity cost, tax savings, inflation adjustment, and True Total Cost
  3. User sees a True Total Cost bar chart comparing all options (winner highlighted) and a cumulative cost over time line chart showing month-by-month evolution
  4. Charts include accessible text alternatives (data tables or ARIA labels) and use patterns or labels alongside color for differentiation
  5. Results update via HTMX partial page replacement when inputs change, with a visible "Calculate" button always present as fallback
  6. All browser-based verification (visual layout, HTMX behavior, chart rendering, responsive design, accessibility) is automated via Playwright MCP — no manual browser checks
**Plans**: 3 plans

Plans:
- [ ] 03-01-PLAN.md — Results analysis module, recommendation hero card, and cost breakdown table
- [ ] 03-02-PLAN.md — SVG chart data preparation, bar and line chart templates, accessible data tables
- [ ] 03-03-PLAN.md — HTMX partial page replacement, loading indicator, and full integration wiring

### Phase 4: Deployment and Polish
**Goal**: Application is ready for self-hosting with documentation, containerization, and verified performance
**Depends on**: Phase 3
**Requirements**: TECH-05, TECH-06, TECH-07, TECH-08, PERF-01
**Success Criteria** (what must be TRUE):
  1. A Dockerfile builds and runs the application as a single process with no external database dependency
  2. Configuration (default rates, branding) is overridable via environment variables
  3. README provides clear self-hosting instructions and the project ships with an open-source license (MIT or Apache 2.0)
  4. Results render within 300ms of form submission under typical usage
  5. All browser-based verification (visual, responsive, functional) is automated via Playwright MCP — no manual browser checks
**Plans**: TBD

Plans:
- [ ] 04-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Calculation Engine | 3/3 | Complete   | 2026-03-10 |
| 2. Web Layer and Input Forms | 3/3 | Complete   | 2026-03-10 |
| 3. Results Display and Charts | 3/3 | Complete    | 2026-03-10 |
| 4. Deployment and Polish | 0/1 | Not started | - |
