---
phase: 11-detailed-period-breakdown
verified: 2026-03-13T00:00:00Z
status: passed
score: 15/15 must-haves verified
re_verification: false
---

# Phase 11: Detailed Period Breakdown Verification Report

**Phase Goal:** Users can inspect the period-by-period cost composition for each financing option
**Verified:** 2026-03-13
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | MonthlyDataPoint includes per-period opportunity_cost, inflation_adjustment, and tax_savings fields | VERIFIED | `models.py` lines 115–117: all three Decimal fields with `Field(default_factory=lambda: Decimal(0))` |
| 2 | Engine builders populate per-period cost factors for loan, cash, and promo options | VERIFIED | `engine.py` lines 81–112 (_build_cash_result) and 194–257 (_build_loan_result/_build_promo_result) both call `compute_opportunity_cost_per_period` and assign per-period values |
| 3 | Per-period values sum to aggregate totals within rounding tolerance | VERIFIED | Tests in `test_engine.py` assert sums match within 0.05 tolerance; 241 tests pass |
| 4 | Existing tests pass without modification (new fields have Decimal(0) defaults) | VERIFIED | 241 pytest tests pass; new fields default to Decimal(0) confirmed in models.py |
| 5 | User can click a tab to view the detailed period table for each option | VERIFIED | `detailed_breakdown.html`: ARIA tablist with per-option hx-post tabs; `routes.py` line 400: POST /partials/detail/<idx> endpoint; Playwright check 24 confirms tab switching |
| 6 | User can click the Compare tab to see side-by-side Payment and Cumulative True Total Cost per option per period | VERIFIED | `detailed_breakdown.html` line 15–24: Compare tab button; `routes.py` line 434: /partials/detail/compare endpoint; `detailed_compare.html` renders side-by-side; Playwright check 25 confirms |
| 7 | User can toggle column checkboxes to show/hide cost factor columns | VERIFIED | `detail_toggle.js` lines 19–26: change handler on .col-toggle; `detailed_breakdown.html` lines 27–56: checkboxes with data-column; Playwright check 26 confirms hide/show |
| 8 | Column toggle state persists when switching tabs | VERIFIED | `detail_toggle.js` lines 28–33: htmx:afterSwap handler calls applyHidden on new content; Playwright check 26 confirms persistence across tab switch |
| 9 | User can toggle between monthly and annual granularity | VERIFIED | `detail_toggle.js` lines 86–114: granularity change handler triggers htmx.ajax re-fetch with ?granularity=; `results.py` aggregate_annual function (line 377); routes accept ?granularity param; Playwright confirms 36 rows -> 3 "Year N" rows |
| 10 | Table has proper th scope attributes, ARIA tablist, and keyboard-navigable tabs | VERIFIED | `detailed_table.html`: all th elements have scope="col" or scope="colgroup"; `detailed_breakdown.html`: role="tablist" on container, role="tab" on buttons; `detail_toggle.js` lines 36–63: ArrowLeft/Right/Home/End keyboard nav; Playwright check 27 confirms |
| 11 | Sticky totals row visible when scrolling long tables | VERIFIED | `style.css` line 472: `.detail-table tfoot tr { position: sticky; bottom: 0; ... }`; Playwright screenshot captured |
| 12 | Promo options show dual columns (paid on time / not paid on time) | VERIFIED | `detailed_table.html` lines 5–32: promo branch with colspan sub-headers; `results.py` build_detailed_breakdown builds not_paid_rows for promo options |
| 13 | Playwright verifies per-period data, tab switching, compare tab, column toggles, ARIA accessibility, keyboard navigation, and annual granularity | VERIFIED | `tests/playwright_verify.py` verify_detailed_breakdown() function (line 681); called in main (line 1371); covers all 5 DETAIL requirements with 35+ checks |
| 14 | Full test suite passes with zero failures | VERIFIED | `uv run pytest tests/ -x -q`: 241 passed |
| 15 | Linting clean | VERIFIED | `uv run ruff check .`: All checks passed |

**Score:** 15/15 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/fathom/models.py` | Extended MonthlyDataPoint with 3 new Decimal fields | VERIFIED | Lines 115–117: opportunity_cost, inflation_adjustment, tax_savings — all with Decimal(0) defaults |
| `src/fathom/opportunity.py` | Per-period opportunity cost computation | VERIFIED | `compute_opportunity_cost_per_period` (line 157): returns list[Decimal] of length comparison_period |
| `src/fathom/engine.py` | Engine builders populating per-period cost factors | VERIFIED | Both _build_cash_result and _build_loan_result import and call compute_opportunity_cost_per_period; assign per-period values to MonthlyDataPoint |
| `src/fathom/results.py` | build_detailed_breakdown, aggregate_annual, build_compare_data functions | VERIFIED | All three functions present at lines 377, 437, 527 |
| `src/fathom/routes.py` | HTMX endpoints for tab switching and granularity toggle | VERIFIED | POST /partials/detail/<idx> (line 400) and POST /partials/detail/compare (line 434) |
| `src/fathom/templates/partials/results/detailed_breakdown.html` | Tab container with checkbox row and tab panel | VERIFIED | Substantive: role="tablist", hx-post per-tab, fieldset with col-toggle checkboxes, granularity radios, #detail-panel |
| `src/fathom/templates/partials/results/detailed_table.html` | Per-option period table partial | VERIFIED | Substantive: thead with scope attrs, tbody rows with CSS col-* classes, tfoot sticky totals, promo dual-column branch |
| `src/fathom/templates/partials/results/detailed_compare.html` | Compare tab with side-by-side columns | VERIFIED | Substantive: per-option colspan headers, Payment+Cumulative sub-columns, tfoot totals |
| `src/fathom/static/detail_toggle.js` | Column toggle JS with HTMX afterSwap integration | VERIFIED | Substantive IIFE: hiddenCols state, applyHidden, htmx:afterSwap handler, tab keyboard nav, granularity toggle |
| `src/fathom/static/style.css` | Tab, sticky totals, checkbox, and dark mode styles | VERIFIED | .detail-tabs, [role="tab"], .detail-table tfoot (position: sticky), .col-toggles, .detail-table-scroll all present |
| `tests/playwright_verify.py` | Playwright browser verification for all DETAIL requirements | VERIFIED | verify_detailed_breakdown() with 35 checks, called from main |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/fathom/engine.py` | `src/fathom/opportunity.py` | `compute_opportunity_cost_per_period` import | WIRED | Line 25: `from fathom.opportunity import ... compute_opportunity_cost_per_period`; called at lines 81, 194 |
| `src/fathom/engine.py` | `src/fathom/models.py` | MonthlyDataPoint construction with new fields | WIRED | Lines 108, 111–112, 233–235, 253–257: opportunity_cost=, inflation_adjustment=, tax_savings= assignments |
| `src/fathom/templates/partials/results/detailed_breakdown.html` | `src/fathom/routes.py` | hx-post to /partials/detail/<idx> and /partials/detail/compare | WIRED | Template lines 9, 20 contain hx-post="/partials/detail/..."; routes.py lines 400, 434 handle these |
| `src/fathom/static/detail_toggle.js` | `src/fathom/templates/partials/results/detailed_table.html` | CSS class toggling on .col-* cells | WIRED | JS uses querySelectorAll("." + cls) to find col-* elements; template applies col-payment, col-interest, etc. classes to all td/th cells |
| `src/fathom/routes.py` | `src/fathom/results.py` | build_detailed_breakdown call | WIRED | Line 34: `from fathom.results import analyze_results, build_compare_data, build_detailed_breakdown`; called at lines 359, 424 |
| `tests/playwright_verify.py` | `src/fathom/routes.py` | HTTP requests to running app | WIRED | Line 1371: verify_detailed_breakdown(browser) called from main; navigates to localhost and exercises all HTMX endpoints |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| DETAIL-01 | 11-01, 11-03 | User can view per-period cost breakdown for each option showing all cost factors | SATISFIED | MonthlyDataPoint has all fields; engine populates them; detailed_table.html renders all columns; Playwright check 23 confirms 36 rows, non-zero opp cost, totals row |
| DETAIL-02 | 11-02, 11-03 | User can switch between options via tabs, with one tab per option | SATISFIED | detailed_breakdown.html has per-option tabs with hx-post; /partials/detail/<idx> endpoint renders correct table; Playwright check 24 confirms content change and aria-selected state |
| DETAIL-03 | 11-02, 11-03 | User can view a Compare tab showing key totals side-by-side across all options per period | SATISFIED | Compare tab button in detailed_breakdown.html; /partials/detail/compare endpoint; detailed_compare.html shows Payment+Cumulative per option; Playwright check 25 confirms |
| DETAIL-04 | 11-02, 11-03 | User can toggle individual cost factor columns on/off | SATISFIED | col-toggle checkboxes in detailed_breakdown.html; JS hiddenCols state + htmx:afterSwap persistence; Playwright check 26 confirms hide, persistence, and re-show |
| DETAIL-05 | 11-02, 11-03 | Detailed breakdown table is accessible (proper table headers, scope attributes, ARIA labels) | SATISFIED | th scope="col"/scope="colgroup" throughout; role="tablist"/"tab"/"tabpanel"; aria-label on fieldset; keyboard nav with ArrowLeft/Right/Home/End; Playwright check 27 confirms |

No orphaned requirements. All 5 DETAIL requirements from REQUIREMENTS.md are accounted for in plans 11-01, 11-02, and 11-03.

---

### Anti-Patterns Found

None. No TODO/FIXME/placeholder comments, no empty implementations, no stubs found in phase 11 files. The `return []` at `results.py:393` is a guard clause in `aggregate_annual` for empty input, not a stub.

---

### Human Verification Required

None. All verification has been automated via Playwright MCP. The Playwright suite covers:

- Visual rendering of the detailed table (screenshots captured to tests/screenshots/)
- Tab switching behavior and aria-selected state changes
- Compare tab side-by-side column rendering
- Column toggle show/hide and state persistence across HTMX swaps
- ARIA attributes (role, aria-selected, aria-labelledby, scope)
- Keyboard navigation (ArrowRight, Enter key activation)
- Annual granularity toggle (36 rows -> 3 "Year N" rows)
- Sticky totals row screenshot

---

### Summary

Phase 11 fully achieves its goal. Users can inspect period-by-period cost composition for each financing option through a complete, working implementation:

- **Data layer (Plan 01):** MonthlyDataPoint carries per-period opportunity_cost, inflation_adjustment, and tax_savings. All three engine builders populate these fields. compute_opportunity_cost_per_period returns per-month values that sum to aggregate totals within rounding tolerance.

- **UI layer (Plan 02):** A tabbed interface below the summary breakdown renders an HTMX-driven table for each option. The Compare tab shows side-by-side Payment and Cumulative True Total Cost. Column toggle checkboxes control visibility with state persisting across tab switches via htmx:afterSwap. Monthly/annual granularity toggle works via htmx.ajax re-fetch. Promo options render dual paid/not-paid columns. All elements are accessible with proper ARIA attributes and keyboard navigation.

- **Browser verification (Plan 03):** Playwright confirms all 5 DETAIL requirements end-to-end in a real browser with 35 checks.

All 241 pytest tests pass. Ruff linting is clean. All 10 commits from the 3 plans are present in git history.

---

_Verified: 2026-03-13_
_Verifier: Claude (gsd-verifier)_
