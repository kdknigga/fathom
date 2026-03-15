# Roadmap: Fathom

## Milestones

- ✅ **v1.0 MVP** — Phases 1-6 (shipped 2026-03-13)
- ✅ **v1.1 Deeper Insights** — Phases 7-12 (shipped 2026-03-14)
- **v1.2 Address Code Review** — Phases 13-16 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-6) — SHIPPED 2026-03-13</summary>

- [x] Phase 1: Calculation Engine (3/3 plans) — completed 2026-03-10
- [x] Phase 2: Web Layer and Input Forms (3/3 plans) — completed 2026-03-10
- [x] Phase 3: Results Display and Charts (3/3 plans) — completed 2026-03-10
- [x] Phase 4: Deployment and Polish (3/3 plans) — completed 2026-03-12
- [x] Phase 5: Pydantic Refactor (2/2 plans) — completed 2026-03-12
- [x] Phase 6: Bug Fixes and Tech Debt (2/2 plans) — completed 2026-03-13

</details>

<details>
<summary>✅ v1.1 Deeper Insights (Phases 7-12) — SHIPPED 2026-03-14</summary>

- [x] Phase 7: Dark Mode (2/2 plans) — completed 2026-03-14
- [x] Phase 8: Comma-Normalized Inputs (2/2 plans) — completed 2026-03-14
- [x] Phase 9: Tooltips and Tax Guidance (2/2 plans) — completed 2026-03-14
- [x] Phase 10: JSON Export/Import (2/2 plans) — completed 2026-03-14
- [x] Phase 11: Detailed Period Breakdown (3/3 plans) — completed 2026-03-14
- [x] Phase 12: Python Linting Cleanup (2/2 plans) — completed 2026-03-14

</details>

### v1.2 Address Code Review (In Progress)

**Milestone Goal:** Fix all confirmed defects and test coverage gaps from the 2026-03-15 production-readiness code review.

- [x] **Phase 13: Centralize Monetary Rounding** - Extract single `money.py` module replacing 5 duplicate `quantize_money()` definitions (completed 2026-03-15)
- [ ] **Phase 14: Engine Corrections** - Fix promo penalty modeling and line chart metric with tests proving correctness
- [ ] **Phase 15: Validation and HTMX Guards** - Bound inflation/tax rates and enforce 2-4 option limits with tests
- [ ] **Phase 16: Custom Option Cleanup** - Wire custom_label into results and clarify upfront cash with tests

## Phase Details

### Phase 13: Centralize Monetary Rounding
**Goal**: All monetary rounding flows through a single canonical utility, eliminating drift risk across calculation modules
**Depends on**: Phase 12 (v1.1 complete)
**Requirements**: ENG-03
**Success Criteria** (what must be TRUE):
  1. A single `quantize_money()` function exists in `src/fathom/money.py` and no other module defines its own rounding helper
  2. All existing tests pass with zero behavior change — this is a pure refactor
  3. Quality gates (ruff, ty, pyrefly) pass clean with no new inline suppressions
**Plans**: 1 plan
Plans:
- [ ] 13-01-PLAN.md — Create money.py and centralize all quantize_money imports

### Phase 14: Engine Corrections
**Goal**: Users comparing promo financing options see materially different costs for deferred-interest vs forward-only scenarios, and the line chart accurately plots cumulative true cost
**Depends on**: Phase 13 (rounding centralized so engine fixes import from canonical module)
**Requirements**: ENG-01, ENG-02, TEST-01, TEST-02
**Success Criteria** (what must be TRUE):
  1. Submitting a promo option with deferred-interest enabled produces a visibly different (higher) "not paid on time" cost than the same option with forward-only interest
  2. A written business rule with worked numeric example ($10K purchase, 24.99% APR, 12-month promo) exists as a code comment before implementation, and tests assert against those specific expected dollar amounts
  3. The line chart data points for each option match cumulative true cost (payments + opportunity cost - tax savings + inflation adjustment), not cumulative payments
  4. Tests assert the invariant: retroactive penalty cost > forward-only penalty cost > paid-on-time cost, using specific dollar amounts
**Plans**: TBD

### Phase 15: Validation and HTMX Guards
**Goal**: Users cannot submit impossible inflation/tax values or violate the 2-4 option contract through the UI
**Depends on**: Phase 13 (no dependency on engine fixes; ordered by severity after Phase 14)
**Requirements**: VAL-01, VAL-02, VAL-03, VAL-04, TEST-03, TEST-04
**Success Criteria** (what must be TRUE):
  1. Submitting an inflation rate outside 0-20% returns a clear error message and does not reach the calculation engine
  2. Submitting a tax rate outside 0-60% returns a clear error message and does not reach the calculation engine
  3. Clicking "Add Option" when 4 options exist returns HTTP 200 with the form unchanged (no 5th option appears)
  4. Clicking "Remove Option" when 2 options exist returns HTTP 200 with the form unchanged (neither option is removed)
  5. Disabling the inflation toggle with an out-of-range value in the field does not trigger a validation error (disabled fields bypass bounds checking)
**Plans**: TBD

### Phase 16: Custom Option Cleanup
**Goal**: Users who select the "Custom/Other" option type see their custom label in results and understand that upfront cash is optional
**Depends on**: Phase 13 (no dependency on engine or validation fixes)
**Requirements**: CUST-01, CUST-02, TEST-05
**Success Criteria** (what must be TRUE):
  1. A custom option's user-provided label appears as the option name in the recommendation card, breakdown table, and charts
  2. The custom option form clearly indicates that the upfront cash field is optional (not required)
  3. Tests verify the custom label text appears in rendered HTML results
**Plans**: TBD

## Progress

**Execution Order:** Phases 13 > 14 > 15 > 16

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Calculation Engine | v1.0 | 3/3 | Complete | 2026-03-10 |
| 2. Web Layer and Input Forms | v1.0 | 3/3 | Complete | 2026-03-10 |
| 3. Results Display and Charts | v1.0 | 3/3 | Complete | 2026-03-10 |
| 4. Deployment and Polish | v1.0 | 3/3 | Complete | 2026-03-12 |
| 5. Pydantic Refactor | v1.0 | 2/2 | Complete | 2026-03-12 |
| 6. Bug Fixes and Tech Debt | v1.0 | 2/2 | Complete | 2026-03-13 |
| 7. Dark Mode | v1.1 | 2/2 | Complete | 2026-03-14 |
| 8. Comma-Normalized Inputs | v1.1 | 2/2 | Complete | 2026-03-14 |
| 9. Tooltips and Tax Guidance | v1.1 | 2/2 | Complete | 2026-03-14 |
| 10. JSON Export/Import | v1.1 | 2/2 | Complete | 2026-03-14 |
| 11. Detailed Period Breakdown | v1.1 | 3/3 | Complete | 2026-03-14 |
| 12. Python Linting Cleanup | v1.1 | 2/2 | Complete | 2026-03-14 |
| 13. Centralize Monetary Rounding | 1/1 | Complete   | 2026-03-15 | - |
| 14. Engine Corrections | v1.2 | 0/? | Not started | - |
| 15. Validation and HTMX Guards | v1.2 | 0/? | Not started | - |
| 16. Custom Option Cleanup | v1.2 | 0/? | Not started | - |
