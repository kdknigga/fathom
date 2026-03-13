# Roadmap: Fathom

## Milestones

- ✅ **v1.0 MVP** — Phases 1-6 (shipped 2026-03-13)
- **v1.1 Deeper Insights** — Phases 7-11 (in progress)

## Phases

<details>
<summary>v1.0 MVP (Phases 1-6) — SHIPPED 2026-03-13</summary>

- [x] Phase 1: Calculation Engine (3/3 plans) — completed 2026-03-10
- [x] Phase 2: Web Layer and Input Forms (3/3 plans) — completed 2026-03-10
- [x] Phase 3: Results Display and Charts (3/3 plans) — completed 2026-03-10
- [x] Phase 4: Deployment and Polish (3/3 plans) — completed 2026-03-12
- [x] Phase 5: Pydantic Refactor (2/2 plans) — completed 2026-03-12
- [x] Phase 6: Bug Fixes and Tech Debt (2/2 plans) — completed 2026-03-13

</details>

### v1.1 Deeper Insights

- [ ] **Phase 7: Dark Mode** — OS-preference dark mode across all pages and SVG charts
- [ ] **Phase 8: Comma-Normalized Inputs** — Accept, parse, and display comma-formatted numbers in all monetary fields
- [ ] **Phase 9: Tooltips and Tax Guidance** — Popover explanations on all form fields and result terms, plus tax bracket reference
- [ ] **Phase 10: JSON Export/Import** — Download current inputs as JSON, upload to restore
- [ ] **Phase 11: Detailed Period Breakdown** — Per-option period-by-period cost table with tabs, compare view, and column toggles

## Phase Details

### Phase 7: Dark Mode
**Goal**: Application adapts to OS dark mode preference with no visual regressions
**Depends on**: Phase 6 (v1.0 complete)
**Requirements**: DARK-01, DARK-02, DARK-03
**Success Criteria** (what must be TRUE):
  1. User on a dark-mode OS sees a dark-themed application automatically, with no flash of light content
  2. All custom CSS (caveat cards, form highlights, status badges) renders correctly in both light and dark modes
  3. SVG chart text, axes, and grid lines are legible in both light and dark modes
**Plans**: TBD

### Phase 8: Comma-Normalized Inputs
**Goal**: Users can enter and see large numbers with commas without any silent parsing failures
**Depends on**: Phase 7
**Requirements**: INPUT-01, INPUT-02, INPUT-03
**Success Criteria** (what must be TRUE):
  1. User can type or paste "100,000" into any monetary field and the calculation processes it as 100000
  2. After leaving a numeric field, the displayed value shows comma formatting (e.g., "100,000")
  3. Server-side Decimal parsing never silently returns None for comma-containing input — it either strips commas and parses or returns a visible error
**Plans**: TBD

### Phase 9: Tooltips and Tax Guidance
**Goal**: Users understand every financial term in the form and results without leaving the page
**Depends on**: Phase 8
**Requirements**: TIPS-01, TIPS-02, TIPS-03, TAX-01, TAX-02
**Success Criteria** (what must be TRUE):
  1. User can click a `?` icon next to any jargon form field (APR, opportunity cost rate, marginal tax rate, etc.) and see a plain-English explanation in a popover
  2. User can click a `?` icon next to any result metric (True Total Cost, Opportunity Cost, Inflation Adjustment) and see an explanation
  3. All tooltips are keyboard-focusable, dismissable with Escape, and hoverable without disappearing (WCAG 1.4.13)
  4. User can expand a tax bracket reference near the tax rate field showing 2025 IRS brackets for Single and Married Filing Jointly across all 7 federal rates
**Plans**: TBD

### Phase 10: JSON Export/Import
**Goal**: Users can save and restore their form inputs via JSON files
**Depends on**: Phase 8
**Requirements**: DATA-01, DATA-02, DATA-03
**Success Criteria** (what must be TRUE):
  1. User can click "Export" and receive a downloaded `.json` file containing all current form inputs
  2. User can upload a previously exported `.json` file and see all form fields restored to the saved values
  3. Uploading an invalid or tampered JSON file shows a clear error message instead of silently failing or crashing
**Plans**: TBD

### Phase 11: Detailed Period Breakdown
**Goal**: Users can inspect the period-by-period cost composition for each financing option
**Depends on**: Phase 9, Phase 10
**Requirements**: DETAIL-01, DETAIL-02, DETAIL-03, DETAIL-04, DETAIL-05
**Success Criteria** (what must be TRUE):
  1. User can view a table showing per-period (monthly or annual) rows with columns for principal, interest, opportunity cost, inflation adjustment, and tax savings for each option
  2. User can switch between options via tabs, with one tab per configured option
  3. User can view a "Compare" tab showing key period totals side-by-side across all options
  4. User can toggle individual cost factor columns on and off to focus on specific factors
  5. Table uses proper `<th>` scope attributes, ARIA labels, and keyboard-navigable tabs
**Plans**: TBD

## Progress

**Execution Order:** 7 → 8 → 9 → 10 → 11

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Calculation Engine | v1.0 | 3/3 | Complete | 2026-03-10 |
| 2. Web Layer and Input Forms | v1.0 | 3/3 | Complete | 2026-03-10 |
| 3. Results Display and Charts | v1.0 | 3/3 | Complete | 2026-03-10 |
| 4. Deployment and Polish | v1.0 | 3/3 | Complete | 2026-03-12 |
| 5. Pydantic Refactor | v1.0 | 2/2 | Complete | 2026-03-12 |
| 6. Bug Fixes and Tech Debt | v1.0 | 2/2 | Complete | 2026-03-13 |
| 7. Dark Mode | v1.1 | 0/0 | Not started | - |
| 8. Comma-Normalized Inputs | v1.1 | 0/0 | Not started | - |
| 9. Tooltips and Tax Guidance | v1.1 | 0/0 | Not started | - |
| 10. JSON Export/Import | v1.1 | 0/0 | Not started | - |
| 11. Detailed Period Breakdown | v1.1 | 0/0 | Not started | - |
