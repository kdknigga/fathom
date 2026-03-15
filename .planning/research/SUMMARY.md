# Project Research Summary

**Project:** Fathom — Financing Options Analyzer (v1.2 Code Review Fixes)
**Domain:** Defect remediation in an existing Python SSR financial calculator (Flask/HTMX/Pydantic/Decimal)
**Researched:** 2026-03-15
**Confidence:** HIGH

## Executive Summary

Fathom v1.2 is a targeted defect-fix milestone, not a feature release. A code review conducted on 2026-03-15 identified 15 findings across four risk categories: logic defects that produce materially wrong financial outputs, validation gaps that allow nonsensical inputs, product-contract mismatches between the UI and server behavior, and test coverage holes. All research confirms that every fix is achievable within the existing technology stack — no new Python dependencies, no new JS libraries, no new CSS frameworks are required.

The recommended approach is sequential, ordered by severity and dependency: centralize the shared `quantize_money` utility first (zero-risk refactor that cleans the foundation), fix the two high-severity calculation defects (promo penalty modeling and line chart metric), close the validation gaps for inflation and tax rates, then address medium and low severity items (HTMX boundary enforcement, custom label wiring, toggle visibility), and conclude with a comprehensive test backfill. This order ensures each phase can be independently verified before the next begins, and avoids the cascading risk of touching multiple code areas simultaneously.

The key risk is the promo penalty fix: both branches of `_build_promo_result()` currently produce identical outputs despite modeling different financial scenarios. The fix requires distinguishing retroactive deferred interest (full original principal charged back-interest from month 1) from forward-only interest (only the remaining balance accrues at post-promo APR). Without a written business rule and worked numeric example locked in before coding begins, a developer can produce code that makes the branches different without making them financially correct. Every other fix is low-risk by comparison.

## Key Findings

### Recommended Stack

All nine confirmed defects are fixable within the existing stack. STACK.md (v1.2 section) explicitly documents that no `pyproject.toml` changes are needed — zero `uv add` commands. The stack in play is: Flask 3.1.3, Jinja2 3.1.6, HTMX 2.0.8, Pydantic 2.12.5, Python `decimal` (stdlib), pygal 3.1.0 for SVG charts, Pico CSS 2.1.1, and pytest 9.0.2 with the existing Flask test client.

**Core technologies relevant to v1.2:**
- Python `decimal.Decimal`: all financial arithmetic uses existing quantize patterns — centralized into `money.py`
- Pydantic 2.12.5 `model_validator(mode="after")`: the established `validate_return_rate` pattern is replicated to add inflation and tax bounds
- Flask routes: guard clauses for HTMX add/remove boundaries return HTTP 200 with unchanged content (not 4xx)
- CSS `:has()` (Baseline Widely Available Dec 2023): handles toggle-controlled field visibility with zero JS
- pytest 9.0.2 + Flask test client: all test backfill uses existing infrastructure

**Technologies confirmed not needed:**
- numpy-financial, QuantLib: existing Decimal amortization covers all needed loan math
- Alpine.js, Stimulus: CSS `:has()` solves toggle visibility in 3 lines
- Any new Python package: all fixes use stdlib + already-installed packages

### Expected Features

FEATURES.md frames v1.2 entirely as defect fixes — existing features that must be corrected for the product to be trustworthy. There are no new capabilities.

**Must have (table stakes — confirmed defects):**
- Correct deferred-interest penalty modeling — two branches produce identical outputs today; users comparing promo options get materially wrong cost estimates
- Cumulative true cost line chart — chart is labeled "Cumulative Cost Over Time" but plots payments only, contradicting the recommendation bar chart and producing a wrong winner for cash vs loan scenarios
- Server-side inflation rate validation (0–20% bounds) — negative and extreme values currently pass through to the engine
- Server-side tax rate validation (0–60% bounds) — values above 100% currently produce nonsensical results
- HTMX add/remove boundary enforcement — server allows a 5th option and removal below 2, violating the 2–4 product contract
- Custom label wiring — `custom_label` is parsed but silently discarded; dead product surface
- Toggle-controlled inflation/tax field visibility — fields always visible despite the progressive disclosure toggle existing
- Centralized monetary rounding — `quantize_money()` duplicated in 5 modules with drift risk
- Test backfill for all fixed defects — every fix above shipped without failure-mode test coverage

**Explicitly out of scope for v1.2:**
- Live-as-you-type result updates — PROJECT.md marks as out of scope; submit-driven HTMX is intentional design
- Minimum payment modeling during promo period — issuer-specific rules; complex for marginal accuracy gain
- Risk-weighted promo ranking — optimistic paid-on-time ranking is intentional; caveats handle risk disclosure
- Sensitivity analysis — new feature, significant UI work, v3+ territory

### Architecture Approach

ARCHITECTURE.md confirms all fixes integrate into the existing layered pipeline without structural changes. The data flow is unchanged: browser HTMX partials → Flask routes (`routes.py`) → form parsing (`forms.py`) → domain object construction (`build_domain_objects()`) → calculation engine (`engine.py`) → result analysis (`results.py`) and chart preparation (`charts.py`) → Jinja2 templates. Each fix touches exactly one or two layers; no fix requires cross-cutting architectural change.

**Major components and their v1.2 changes:**
1. `engine.py` — promo penalty logic fix in `_build_promo_result()` only; retroactive vs forward-only paths must produce materially different `not_paid_on_time.true_total_cost` values
2. `forms.py` — additive validators on `SettingsInput` for inflation/tax bounds; custom label wiring in `build_domain_objects()`
3. `charts.py` — `_collect_option_points()` derives cumulative true cost from per-period factors instead of reading `cumulative_cost` directly
4. `routes.py` — guard clauses at add/remove boundaries + extract shared `_rebuild_option_list()` helper
5. `src/fathom/money.py` (new) — single canonical `quantize_money()` and `CENTS`; 6 modules update their imports
6. Templates + CSS — toggle visibility restructuring in `global_settings.html`; custom option label text

**Key architectural decision confirmed:** `MonthlyDataPoint.cumulative_cost` must not change semantics (it remains "cumulative payments only"). The line chart must derive its own cumulative true cost from per-period factors (`payment + opportunity_cost - tax_savings + inflation_adjustment`), matching what `results.py` already does in `_monthly_data_to_rows()`. Changing the field meaning would cascade into existing tests and the detailed breakdown table.

### Critical Pitfalls

PITFALLS.md identifies 11 pitfalls, 3 critical and 5 moderate.

1. **Promo penalty math without a written spec** — both branches must differ AND be financially correct. Write plain-English business rules with a worked numeric example ($10K purchase, 24.99% APR, 12-month promo) and assert against those expected numbers, not against whatever the code happens to produce.

2. **`cumulative_cost` semantic change breaks chart tests and breakdown table** — do not change the field meaning. Compute cumulative true cost at the chart layer, matching `_monthly_data_to_rows()`. Two independent running sums over Decimal is correct and safe; one broken field definition is not.

3. **Validation bounds reject previously valid input** — bounds must be expressed in percentage units matching form input ("22" = 22%), not decimal units (0.22). The existing `validate_return_rate` pattern must be replicated exactly. Validation must skip disabled fields: `inflation_enabled=False` with `inflation_rate="-5"` must pass validation.

4. **HTMX boundary enforcement returns wrong HTTP status** — returning 4xx on add-at-4 or remove-at-2 prevents HTMX swap, leaving UI broken with no feedback. Return 200 with unchanged content and disabled button.

5. **Toggle visibility loses field values** — using `display: none` removes inputs from HTMX `hx-include` form submission. User enters 5% inflation, disables toggle, submits, re-enables — sees 3% default. Use CSS visibility or sibling combinator so the input remains in the DOM.

## Implications for Roadmap

Research identifies a clear sequential structure driven by dependency and risk. Eight phases, each independently deployable and testable.

### Phase 1: Centralize Monetary Rounding
**Rationale:** Zero-risk foundation refactor. No behavior change whatsoever. Creates the clean `fathom.money` module that all subsequent calculation fixes will import from. Verifiable by: `grep -r "def quantize_money" src/` returns exactly 1 result.
**Delivers:** `src/fathom/money.py` with single `quantize_money()` + `CENTS`; import updates across 6 modules; `tests/test_money.py`
**Addresses:** Finding #10 (duplicate code drift risk)
**Avoids:** Circular imports — new module depends only on `decimal.Decimal`, never imports from the 5 calculation modules

### Phase 2: Promo Penalty Modeling Fix
**Rationale:** Highest severity defect. Core product trust issue. Self-contained in `engine.py`. Must come before the line chart fix because understanding how `MonthlyDataPoint` per-period factors flow is prerequisite context.
**Delivers:** Two distinct penalty code paths in `_build_promo_result()`: retroactive (full principal + back-interest) vs forward-only (remaining balance only). Tests with worked numeric examples asserting the invariant: retroactive > forward-only > paid-on-time.
**Addresses:** Finding #1 (identical promo branches)
**Avoids:** Inventing financial math — write business rules with worked example first, code second

### Phase 3: Validation Bounds
**Rationale:** High severity, low complexity, fully independent. The established `validate_return_rate` pattern makes this a straightforward extension. No dependency on engine or chart fixes.
**Delivers:** Inflation rate bounded to 0–20%; tax rate bounded to 0–60%; bounds-aware tests including disabled-field passthrough and boundary edge cases
**Addresses:** Finding #2 (unbounded inflation and tax inputs)
**Avoids:** Unit mismatch — express bounds in percentage points (20, not 0.20) matching form input conventions

### Phase 4: Line Chart Metric Correction
**Rationale:** High severity. Best done after Phase 2 (promo fix) because reading the engine's per-period factor structure provides context for the chart formula. The fix touches only `charts.py:_collect_option_points()`.
**Delivers:** Line chart plots cumulative true cost (running sum of payment + opportunity_cost - tax_savings + inflation_adjustment) instead of cumulative payments; integration test asserting chart endpoint equals `true_total_cost`
**Addresses:** Finding #6 (chart contradicts recommendation)
**Avoids:** Changing `MonthlyDataPoint.cumulative_cost` semantics — derive at the chart layer, leave the field alone

### Phase 5: HTMX Boundary Enforcement
**Rationale:** Medium severity, self-contained in `routes.py`. No dependency on calculation fixes. Fast win.
**Delivers:** Guard clauses in `add_option()` and `remove_option()` returning 200 with unchanged state at limits; `_rebuild_option_list()` shared helper; Add/Remove buttons disabled in templates at boundaries; route tests
**Addresses:** Finding #3 (5th option allowed; removal below 2 allowed)
**Avoids:** HTTP 4xx response — HTMX does not swap non-200 content, leaving UI broken

### Phase 6: Custom Option Cleanup
**Rationale:** Low-medium severity. Two small changes that touch the same form/model area: label wiring in `build_domain_objects()` and template label text for upfront cash. Group them to minimize context switching.
**Delivers:** `custom_label` propagates as `label` on `FinancingOption` with uniqueness check; custom option template clarifies upfront cash is optional; tests confirm custom label appears in results
**Addresses:** Findings #4 and #5 (custom label discarded; upfront cash validation mismatch)
**Avoids:** Label collision — validate uniqueness or auto-disambiguate before using as results dict key

### Phase 7: Toggle-Controlled Field Visibility
**Rationale:** Low severity, template/CSS only. No Python logic changes. Placed after higher-priority fixes to avoid blocking them.
**Delivers:** `global_settings.html` restructured so CSS sibling combinator or `:has()` can hide rate field when toggle unchecked; `@supports` fallback for browsers without `:has()`; Playwright test verifying field appears/disappears and value is preserved after submit
**Addresses:** Finding #8 (always-visible fields despite progressive disclosure toggle)
**Avoids:** `display: none` losing field values — use CSS visibility or sibling combinator with field remaining in DOM

### Phase 8: Test Backfill
**Rationale:** Strictly last. All fixes are in place. This phase adds regression tests that would have caught each defect, plus invariant assertions that survive future refactors.
**Delivers:** Engine tests (retroactive > forward-only invariant); form tests (bounds, disabled-field passthrough); route tests (add-at-4, remove-at-2); chart tests (endpoint matches `true_total_cost`); Playwright browser tests (toggle value preservation, button disabled state)
**Addresses:** Findings #11–15 (test coverage holes across all fixed areas)
**Avoids:** Tests that assert current behavior rather than business invariants — write at two levels: behavioral (different values) and invariant (correct relationship between values)

### Phase Ordering Rationale

- Phase 1 first: purely additive, no behavior change, eliminates a source of future drift before fixes compound on it
- Phase 2 before Phase 4: understanding how `MonthlyDataPoint` per-period factors flow is context for the chart formula
- Phases 3, 5, 6, 7 are fully independent but ordered by severity (high before low)
- Phase 8 strictly last: tests target fixed defects and must have the fixes in place to be written correctly
- No phase requires another's output except Phase 8 (depends on all) and Phase 4 (benefits from Phase 2 context)

### Research Flags

Phases needing extra care during implementation:
- **Phase 2 (promo penalty):** Write the business rule and worked numeric example in a code comment before touching any code. This is the only phase where inventing plausible-but-wrong math is a realistic risk. Invariant tests (retroactive > forward-only > paid-on-time) must use specific dollar amounts, not just "different values."
- **Phase 7 (toggle visibility):** Validate in Playwright that form values survive the cycle: enter custom rate → uncheck toggle → submit → re-check toggle → verify value preserved. CSS visibility vs `display: none` distinction is easy to get wrong silently.

Phases with well-established patterns:
- **Phase 1 (rounding centralization):** Standard Python module extraction. Run quality gates after; Ruff will catch leftover imports.
- **Phase 3 (validation bounds):** Copy-extend the existing `validate_return_rate` model validator. One validator becomes three.
- **Phase 4 (chart metric):** The correct formula already exists in `results.py:_monthly_data_to_rows()`. Replicate it in `charts.py:_collect_option_points()`.
- **Phase 5 (HTMX guards):** Standard Flask early-return pattern. Return 200, not 4xx.
- **Phase 6 (custom label):** One line change in `build_domain_objects()` plus uniqueness check.
- **Phase 8 (test backfill):** pytest + Flask test client; patterns exist in the test suite for every area.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All findings verified by direct code inspection and runtime version checks; no new dependencies required |
| Features | HIGH | Defects confirmed by code review with specific line number citations; domain behavior verified against CFPB, Synchrony, Bankrate |
| Architecture | HIGH | All integration points identified by direct source inspection of engine.py, forms.py, charts.py, routes.py, results.py |
| Pitfalls | HIGH | Derived from actual code structure (dict key collision risk, CSS visibility vs display, Pydantic frozen model constraints, HTMX HTTP status behavior); not theoretical |

**Overall confidence:** HIGH

### Gaps to Address

- **Retroactive interest numeric model — minor inconsistency:** FEATURES.md recommends "full principal remains at promo expiry (conservative, worst-case)" for the retroactive path; ARCHITECTURE.md suggests "half principal" for the forward-only path but the comments are swapped in places. Resolve before Phase 2: use full principal for retroactive path (FEATURES.md is correct), document "half principal" assumption explicitly for forward-only path, and verify the two paths produce different dollar amounts with a worked example.

- **Tax rate upper bound inconsistency across research files:** STACK.md and FEATURES.md say 50%; ARCHITECTURE.md says 60%. Use 60% as the final bound (most permissive, covers combined state/federal rates in high-tax jurisdictions). Apply consistently across all three validators in `forms.py` and update HTML `max` attribute hints.

- **Toggle visibility implementation choice:** STACK.md recommends CSS `:has()` (with `@supports` fallback requiring less HTML restructuring); FEATURES.md and ARCHITECTURE.md describe the CSS sibling combinator (requiring checkbox and target to share a parent). Both achieve the same outcome. Resolve during Phase 7 planning based on the actual DOM structure in `global_settings.html` at implementation time.

## Sources

### Primary (HIGH confidence)
- `docs/code-review-2026-03-15.md` — all 15 findings, line-number citations, severity ratings
- `src/fathom/engine.py` (lines 279–357) — confirmed `_build_promo_result()` identical branches
- `src/fathom/forms.py` — confirmed `validate_return_rate` pattern; confirmed `custom_label` not wired through
- `src/fathom/charts.py` (line 185) — confirmed `cumulative_cost` read directly without per-period factors
- `src/fathom/results.py:_monthly_data_to_rows()` — confirmed correct cumulative true cost formula exists here already
- `src/fathom/routes.py` (lines 210–312) — confirmed missing add/remove boundary guards
- `grep -r "def quantize_money" src/` — confirmed 5 identical definitions across calculation modules

### Secondary (HIGH confidence — external domain verification)
- [CFPB: Promotional financing offers](https://www.consumerfinance.gov/about-us/blog/how-understand-special-promotional-financing-offers-credit-cards/) — retroactive interest mechanics
- [Synchrony: Deferred Interest](https://www.synchrony.com/consumer-resources/deferred-interest) — consumer product behavior
- [Bankrate: Dangers of Deferred Interest Promotions](https://www.bankrate.com/credit-cards/zero-interest/deferred-interest-promotion-dangers/) — penalty cost modeling
- [BLS CPI data](https://www.bls.gov/data/inflation_calculator.htm) — inflation rate historical bounds
- [IRS Federal Tax Brackets 2026](https://www.irs.gov/filing/federal-income-tax-rates-and-brackets) — tax rate upper bounds
- [CSS `:has()` — Baseline Widely Available Dec 2023](https://caniuse.com) — browser support confirmed
- PROJECT.md — confirmed live updates and promo ranking are explicitly out of scope

---
*Research completed: 2026-03-15*
*Ready for roadmap: yes*
