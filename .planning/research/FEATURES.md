# Feature Landscape

**Domain:** Code review defect fixes for financing options analyzer (v1.2)
**Researched:** 2026-03-15
**Confidence:** HIGH (defects confirmed by code inspection; domain behavior verified with CFPB, Synchrony, Bankrate)

## Context

This is a subsequent milestone. v1.1 is shipped and working. A production-readiness code review (2026-03-15, `docs/code-review-2026-03-15.md`) identified 15 findings across logic defects, validation gaps, product-contract mismatches, and test coverage holes. This file covers how the FIXED versions of these features should behave, not whether to build them.

---

## Table Stakes

Fixes that must land for the product to be trustworthy. These are existing features with confirmed defects -- not new capabilities.

| Feature | Why Expected | Complexity | Dependencies | Notes |
|---------|--------------|------------|--------------|-------|
| Correct deferred-interest penalty modeling | Users comparing promo options get materially wrong cost estimates. Both code branches produce identical results. Core product trust issue. | High | engine.py `_build_promo_result()` | Review finding #1. Both branches construct identical `FinancingOption`. Must differentiate retroactive vs forward-only interest paths. |
| Server-side inflation rate validation | Negative inflation or extreme values (e.g., -5%) produce meaningless recommendations that look credible. | Low | forms.py `SettingsInput` | Review finding #2. Currently no bounds check at all. |
| Server-side tax rate validation | Tax rates above 100% (e.g., 150%) produce nonsensical results. | Low | forms.py `SettingsInput` | Review finding #2. Currently no bounds check at all. |
| Correct cumulative cost line chart metric | Chart title says "Cumulative Cost Over Time" but plots cumulative payments only, ignoring opportunity cost, tax savings, and inflation. Contradicts the recommendation. | Medium | engine.py monthly data, charts.py `_collect_option_points()` | Review finding #6. `results.py` already computes the correct metric in `_monthly_data_to_rows()`. |
| 2-4 option count enforcement in HTMX endpoints | Server allows 5th option add and removal down to 1 option, violating the 2-4 product contract. | Low | routes.py add/remove handlers | Review finding #3. Guard clauses at boundaries. |
| Custom option upfront cash validation | UI shows "Upfront Cash Required" as first-class but validation ignores it. | Low | forms.py, custom.html | Review finding #4. Make explicitly optional in UI. |
| Wire custom_label into results display | Users enter a custom description that is silently discarded. Dead product surface. | Low | forms.py, models.py, result templates | Review finding #5. |
| Toggle-controlled inflation/tax visibility | Fields always visible despite PRD requiring progressive disclosure. | Low | global_settings.html | Review finding #8. CSS or HTMX toggle. |
| Centralized monetary rounding | `quantize_money()` duplicated in 5 modules. Drift risk. | Low | amortization.py, opportunity.py, inflation.py, tax.py, caveats.py | Review finding #10. |
| Test backfill for all fixed defects | Every fix above shipped without failure-mode test coverage. | Medium | All test modules | Review findings #11-15. |

---

## Feature Detail: Deferred-Interest Promo Penalty Modeling

**Confidence: HIGH** (CFPB, Synchrony, Bankrate, Discover all describe consistent mechanics)

### How deferred-interest works in consumer financing

Consumer deferred-interest promotions have two distinct penalty scenarios that the engine must model differently.

**Scenario A: Deferred interest with retroactive interest (common retail model)**

This is the typical store credit card offer ("No interest if paid in full within 12 months"). The mechanics:

1. During promo period: interest accrues invisibly at the standard APR but is NOT billed.
2. If paid in full before deadline: all accrued interest is forgiven. Effective cost = 0% interest.
3. If ANY balance remains at deadline (even $1): ALL accrued interest from day 1 is charged retroactively on the ORIGINAL purchase amount, not the remaining balance.
4. Post-promo: remaining balance PLUS retroactive interest continues accruing at standard APR.

Critical detail from CFPB: A $400 purchase with $25/month payments leaves $100 unpaid after 12 months. The penalty is NOT interest on $100 -- it is $65 in retroactive interest computed on the full $400 from the purchase date. The consumer then owes $165, not $100.

**Scenario B: True 0% APR (no deferred interest)**

This is the credit card intro APR offer ("0% intro APR on purchases for 12 months"). The mechanics:

1. During promo period: no interest accrues at all.
2. If balance remains after promo expires: interest begins on the REMAINING balance only, going forward only, at the post-promo APR.
3. No retroactive component. Only forward-looking interest on unpaid portion.

### What the current code does wrong

In `_build_promo_result()` (engine.py lines 279-357):
- The `if option.deferred_interest and option.retroactive_interest` branch and the `else` branch construct **identical** `FinancingOption` objects.
- Both use `purchase_price` as principal and `post_apr` as rate.
- The flags change caveat warnings but NOT the cost calculation.
- The inline comment says "assume half the balance remains" but the implementation uses full purchase price in both paths.

### What the fix must do

**Retroactive interest path** (`deferred_interest=True, retroactive_interest=True`):

1. Compute retroactive interest: `full_principal * monthly_rate * promo_term_months`. This represents the interest that accrued invisibly during the promo period on the entire original balance.
2. Estimate remaining balance at promo expiry. Two approaches, in order of preference:
   - **Simple (recommended for v1.2):** Assume minimum payments during promo period do not reduce principal (interest-only equivalent). Remaining balance = full principal. This is conservative and matches the worst-case CFPB scenario.
   - **Complex (defer to future):** Model actual minimum payment schedules (2% of balance, issuer-specific). Excessive complexity for marginal accuracy.
3. Total penalty balance = remaining principal + retroactive interest.
4. Amortize the penalty balance at post-promo APR for the remaining term.

**Forward-only path** (`deferred_interest=False`):

1. No retroactive interest.
2. Estimate remaining balance at promo expiry (same approach as above).
3. Amortize remaining balance at post-promo APR for the remaining term.

**Key difference in outcome:** For a $10,000 purchase, 12-month promo, 24.99% post-promo APR:
- Forward-only: remaining $10,000 amortized at 24.99% for remaining term.
- Retroactive: remaining $10,000 PLUS ~$2,499 retroactive interest ($12,499 total) amortized at 24.99%.

The retroactive penalty should produce a materially higher `not_paid_on_time.true_total_cost` than the forward-only path. The current code produces identical values, which is the confirmed defect.

### Code/comment reconciliation

The comment on line 323 says "assume half the balance remains after promo term" but the code uses `purchase_price` (full balance) on both branches. Decision: use full remaining balance (conservative), update the comment, and document the assumption in a caveat. The "half balance" comment was aspirational, never implemented.

### Sources

- [CFPB: How to understand special promotional financing offers](https://www.consumerfinance.gov/about-us/blog/how-understand-special-promotional-financing-offers-credit-cards/)
- [Synchrony: Understanding Deferred Interest](https://www.synchrony.com/consumer-resources/deferred-interest)
- [Bankrate: Dangers of Deferred Interest Promotions](https://www.bankrate.com/credit-cards/zero-interest/deferred-interest-promotion-dangers/)
- [Discover: What is Deferred Interest?](https://www.discover.com/credit-cards/card-smarts/what-is-deferred-interest/)

---

## Feature Detail: Validation Bounds for Inflation and Tax Rates

**Confidence: HIGH** (BLS historical data, IRS brackets, Fed targets)

### Inflation Rate Bounds

| Constraint | Value | Rationale |
|------------|-------|-----------|
| Minimum | 0% | Deflation is real but confuses consumer-facing tools. The toggle already allows disabling inflation entirely, which covers the "no inflation" case. |
| Maximum | 20% | US historical peak was ~20% (1917, 1947). Anything above is implausible for financial planning. Covers hyperinflationary edge cases. |
| Default | 3% | Historical US arithmetic mean is 3.2% (1914-2025, per Minneapolis Fed). Fed target is 2%. 3% is a reasonable conservative default. |
| UI hint | "Typical range: 2-4%" | Guides without restricting. |

### Tax Rate Bounds (Marginal)

| Constraint | Value | Rationale |
|------------|-------|-----------|
| Minimum | 0% | Valid for non-deductible interest or zero-income scenarios. |
| Maximum | 50% | Highest US federal bracket is 37%. State income taxes add up to ~13% (CA, NY). 50% covers all plausible combined US scenarios. |
| Default | 22% | Middle federal bracket, most common for median-income filers. Already the current default. |
| UI hint | IRS bracket reference table already exists (v1.1 feature). |

### Validation behavior

- Only validate bounds when the toggle is enabled. When `inflation_enabled=False`, the inflation rate value is irrelevant and should not trigger validation errors.
- When enabled and value is blank, use the default (3% inflation, 22% tax).
- When enabled and value is out of bounds, return a field-specific error matching the existing error pattern (`"inflation_rate:Inflation rate must be between 0% and 20%."`).
- HTML `min`/`max` attributes on inputs for browser-level UX hints, but server-side Pydantic validation is the enforcement layer. No client-side JS validation.

### Sources

- [BLS CPI Inflation Calculator](https://www.bls.gov/data/inflation_calculator.htm)
- [Minneapolis Fed Inflation Calculator](https://www.minneapolisfed.org/about-us/monetary-policy/inflation-calculator)
- [Federal Reserve 2% inflation target](https://www.stlouisfed.org/publications/page-one-economics/2023/01/03/adjusting-for-inflation)

---

## Feature Detail: Cumulative Cost Line Chart Metric

**Confidence: HIGH** (code inspection confirms the discrepancy; the correct formula exists in results.py)

### What the chart currently plots (wrong)

The y-axis uses `MonthlyDataPoint.cumulative_cost`, which is computed in the engine builders as a running sum of payments only:

```python
# In _build_loan_result(), line 229:
cumulative = cumulative + dp.payment
```

This excludes opportunity cost, tax savings, and inflation adjustment -- the very factors that make this tool's recommendation different from a naive payment comparison.

### What the chart must plot (correct)

The y-axis at month M should be the running sum of per-period net true cost:

```
cumulative_true_cost[M] = sum(month 1..M) of:
    payment[m] + opportunity_cost[m] - tax_savings[m] + inflation_adjustment[m]
```

This is exactly what `_monthly_data_to_rows()` in results.py already computes as `cumulative_true_total_cost` for the detailed breakdown tables. The formula exists and is tested in the detailed table context.

### Why this matters

Without this fix:
- Cash appears as a flat line at purchase price from month 1.
- Loans show a steadily rising payment line.
- The crossover point between lines is meaningless because it ignores the factors that drive the recommendation.
- Users see a chart labeled "Cumulative Cost Over Time" that tells a different story than the "True Total Cost" bar chart and recommendation card.

Evidence from code review: for a loan vs cash comparison, `true_total_cost` values were $29,734 (loan) vs $30,885 (cash), but chart endpoints showed $26,904 (loan) vs $25,000 (cash) -- the chart showed the wrong winner.

### Implementation approach

**Option A (recommended): Compute in engine, store in MonthlyDataPoint**

Repurpose `cumulative_cost` in `MonthlyDataPoint` to mean cumulative true cost (not just cumulative payments). Update the engine builders to compute it using the same net-cost formula. Charts read the field directly.

Pros: Single source of truth. Charts, detailed tables, and any future consumer all get the correct metric.
Cons: Changes the semantic meaning of an existing field. Must update engine builders and verify detailed table still works.

**Option B (not recommended): Compute in chart preparation**

Leave `MonthlyDataPoint.cumulative_cost` as payments-only. Have `_collect_option_points()` recompute cumulative true cost from the per-period factors.

Pros: No model changes.
Cons: Duplicates the formula from `_monthly_data_to_rows()`. Two places to maintain.

Recommendation: Option A. The field name `cumulative_cost` should mean the true cost, not just payments. If backward compatibility matters, rename to `cumulative_true_cost` and remove the old field.

---

## Feature Detail: Toggle-Controlled Progressive Disclosure

**Confidence: HIGH** (standard HTML/CSS pattern)

### Expected behavior

1. "Include Inflation" checkbox unchecked: inflation rate input is hidden.
2. "Include Inflation" checkbox checked: inflation rate input appears.
3. Same for "Include Tax Deduction" and tax rate input.
4. When hidden, field value is preserved (not cleared) so toggling back restores previous entry.
5. No server round-trip needed -- this is a pure display concern.

### Implementation

CSS sibling selector approach (if DOM structure allows):

```css
.toggle-target { display: none; }
.toggle-checkbox:checked ~ .toggle-target { display: block; }
```

If checkbox and target are not DOM siblings (likely given form layout), use minimal inline JS (`onchange`) or restructure the template to make them siblings. Given the project uses HTMX, an `hx-trigger="change"` swap is also viable but adds unnecessary server load for a display toggle.

Recommendation: Restructure the template slightly so the checkbox and its controlled field are siblings, then use pure CSS. No JS, no HTMX round-trip.

---

## Feature Detail: Custom Label Wiring

**Confidence: HIGH** (code inspection)

### Current state

- `custom_label` is parsed from form data and stored in `OptionInput.custom_label`.
- It is NOT passed to `FinancingOption` (domain model has no such field).
- It is NOT used anywhere in results, charts, or recommendations.

### Expected behavior

When a user selects "Custom/Other" and enters a label like "Store Credit Card" or "Family Loan", that text should appear as the option name everywhere: results cards, chart labels, breakdown tables, recommendation text, JSON export.

### Implementation (simplest approach)

In `build_domain_objects()`, when building a custom option, use `custom_label` as the `label` if it is non-empty:

```python
if option_type == OptionType.CUSTOM and opt.custom_label.strip():
    label = opt.custom_label.strip()
else:
    label = opt.label or option_type.value
```

No model changes needed. The `label` field on `FinancingOption` already propagates through the entire result chain.

---

## Feature Detail: 2-4 Option Enforcement in HTMX Endpoints

**Confidence: HIGH** (code inspection)

### Expected behavior

- `/partials/option/add`: If 4 options already exist, return the current form state unchanged (HTTP 200, no new option card added). Optionally disable the "Add Option" button when at 4.
- `/partials/option/<idx>/remove`: If only 2 options exist, return the current form state unchanged (HTTP 200, no option removed). Optionally disable "Remove" buttons when at 2.

### Implementation

Guard clauses at the top of each route handler:

```python
if len(options) >= 4:
    # Return current form state without adding
    return render_template(...)

if len(options) <= 2:
    # Return current form state without removing
    return render_template(...)
```

The UI should also reflect the constraint: hide or disable the add button when at max, hide or disable remove buttons when at min. This can be done in the Jinja template with a simple conditional.

---

## Feature Detail: Centralized Monetary Rounding

**Confidence: HIGH** (code inspection)

### Current state

Five modules each define their own `quantize_money()`:
- `amortization.py`
- `opportunity.py`
- `inflation.py`
- `tax.py`
- `caveats.py`

All do the same thing: `Decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`.

### Implementation

Create `src/fathom/money.py` (or add to an existing utils module) with the single canonical implementation. Update all five modules to import from the central location. This is a pure refactor with no behavior change.

---

## Differentiators

Features beyond defect fixes. NOT in scope for v1.2.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Minimum payment modeling for promo remaining balance | More accurate penalty estimation instead of assuming full balance remains | Medium | Would require modeling minimum payment schedules during promo period. Issuer-specific rules make this complex. |
| Sensitivity analysis | Show how results change as return rate, inflation, or tax varies | High | New feature, significant UI work |
| Promo risk-weighted ranking | Show recommendation under pessimistic scenario | Medium | Explicitly out of scope per PROJECT.md |

## Anti-Features

Features to explicitly NOT build in v1.2.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Live-as-you-type result updates | Code review finding #7 flagged this as a PRD mismatch, but PROJECT.md explicitly moved it to Out of Scope. Submit-driven HTMX is the intentional design. | Keep Calculate button. PRD updated to match. |
| Complex minimum payment modeling during promo | Adds complexity for marginal accuracy. Minimum payment rules vary by issuer (2% of balance, $25 minimum, interest-only, etc.). | Assume full principal remains at promo expiry (conservative). Document the assumption in a caveat. |
| Risk-weighted promo ranking | Changing winner selection based on penalty risk adds cognitive complexity and second-guessing. | Keep optimistic (paid-on-time) ranking with clear caveats. Explicit product decision. |
| Client-side validation JS | Would duplicate server bounds in JS, creating divergence risk. Violates architecture constraint. | Server-side Pydantic validation only. HTML `min`/`max` attributes for UX hints but not enforcement. |

---

## Feature Dependencies

```
Centralize quantize_money() ← independent, no deps (do first as foundation)
Toggle visibility (inflation/tax) ← independent, no deps
Validation bounds (inflation/tax) ← independent, no deps
Custom label wiring ← independent, no deps
Custom option validation reconciliation ← independent, no deps
2-4 option enforcement ← independent, no deps
Deferred-interest penalty fix ← benefits from centralized rounding (minor dep)
Cumulative cost chart fix ← touches engine monthly data (same area as deferred-interest fix)
Test backfill ← depends on ALL fixes above being complete
```

---

## Implementation Order Recommendation

Based on dependency analysis, severity, and complexity:

| Order | Feature | Severity | Complexity | Rationale |
|-------|---------|----------|------------|-----------|
| 1 | Centralize `quantize_money()` | Low | Low | Foundation refactor. No behavior change. Enables clean fixes elsewhere. |
| 2 | Fix deferred-interest penalty modeling | High | High | Highest severity, most complex, core to product trust. |
| 3 | Fix cumulative cost chart metric | High | Medium | Connected to engine data; benefits from deferred-interest changes landing first. |
| 4 | Add inflation/tax validation bounds | High | Low | High severity, low complexity, independent. Quick win. |
| 5 | Enforce 2-4 option boundaries | Medium | Low | Server contract enforcement. Quick win. |
| 6 | Reconcile custom option validation + wire custom_label | Medium+Low | Low | Grouped because they touch the same form/model area. |
| 7 | Toggle-controlled field visibility | Low | Low | Pure template/CSS change. |
| 8 | Test backfill | High | Medium | Must come last. Each test targets a specific fix above. Should include regression tests that FAIL before the fix and PASS after. |

---

## Sources

- [CFPB: How to understand special promotional financing offers](https://www.consumerfinance.gov/about-us/blog/how-understand-special-promotional-financing-offers-credit-cards/)
- [Synchrony: Understanding Deferred Interest](https://www.synchrony.com/consumer-resources/deferred-interest)
- [Bankrate: Dangers of Deferred Interest Promotions](https://www.bankrate.com/credit-cards/zero-interest/deferred-interest-promotion-dangers/)
- [Discover: What is Deferred Interest?](https://www.discover.com/credit-cards/card-smarts/what-is-deferred-interest/)
- [BLS CPI Inflation Calculator](https://www.bls.gov/data/inflation_calculator.htm)
- [Minneapolis Fed Inflation Calculator](https://www.minneapolisfed.org/about-us/monetary-policy/inflation-calculator)
- [St. Louis Fed: Adjusting for Inflation](https://www.stlouisfed.org/publications/page-one-economics/2023/01/03/adjusting-for-inflation)
- Code inspection: `src/fathom/engine.py`, `src/fathom/forms.py`, `src/fathom/charts.py`, `src/fathom/results.py`, `src/fathom/models.py`
- Code review: `docs/code-review-2026-03-15.md`

---
*Feature research for: Fathom v1.2 -- code review defect fixes*
*Researched: 2026-03-15*
