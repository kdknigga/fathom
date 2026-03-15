# Phase 14: Engine Corrections - Research

**Researched:** 2026-03-15
**Domain:** Financial calculation engine bug fixes (promo penalty modeling + chart metric correction)
**Confidence:** HIGH

## Summary

Phase 14 fixes two confirmed bugs in the Fathom calculation engine: (1) `_build_promo_result()` has identical if/else branches for deferred-interest vs forward-only interest, producing no cost differentiation, and (2) `MonthlyDataPoint.cumulative_cost` tracks cumulative payments rather than cumulative true cost, causing the line chart to plot the wrong metric.

Both bugs are well-localized in the existing codebase. The fix for bug (1) requires building a custom two-phase payment schedule (promo period with minimum payments, then post-promo amortization) rather than delegating to `_build_loan_result()` with slightly different parameters. The fix for bug (2) requires changing how `cumulative_cost` is computed in all three engine builders (`_build_cash_result`, `_build_loan_result`, `_build_promo_result`) to use the true cost formula already implemented in `results.py:_monthly_data_to_rows()`.

**Primary recommendation:** Fix the engine builders to compute cumulative true cost inline (matching `_monthly_data_to_rows` formula), then rewrite `_build_promo_result` to construct a two-phase MonthlyDataPoint series for not-paid-on-time scenarios. Both paid and not-paid lines must appear on the chart.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Retroactive (deferred) interest:** When promo expires unpaid, retroactive interest is calculated on the FULL original financed principal (purchase_price - down_payment) at the post-promo APR for the entire promo term. This is added as a lump sum to the remaining balance at the promo boundary (month 13 for a 12-month promo).
- **Forward-only interest:** When promo expires unpaid WITHOUT deferred-interest, post-promo APR applies only to the remaining balance -- no retroactive charges. This makes forward-only strictly cheaper than retroactive.
- **Both branches must produce visibly different costs.** The current bug is that both branches are identical.
- **Minimum payments during promo:** Model realistic minimum payments during the 0% promo period. Minimum payment = `required_monthly / 2` (where `required_monthly = principal / term`).
- **Down payment:** Same down payment applies to both paid and not-paid scenarios (already paid regardless).
- **Post-promo amortization term:** Same duration as the promo term (e.g., 12-month promo -> 12-month post-promo amortization). Total timeline = 2x promo term.
- **Retroactive interest timing:** Added as lump sum at promo boundary (month 13), not spread across post-promo period. Chart will show a sharp cost jump at the transition.
- **Worked Numeric Example (must appear as code comment):**
  - $10K purchase, 24.99% APR, 12-month promo, no down payment
  - `required_monthly = $10,000 / 12 = $833.33`
  - `min_payment = $833.33 / 2 = $416.67`
  - Remaining principal at month 13: `$10,000 - (12 x $416.67) = ~$5,000`
  - **Retroactive:** remaining $5,000 + retroactive interest ($10,000 x 24.99% x 1yr = $2,499) = $7,499 amortized at 24.99% for 12 months
  - **Forward-only:** remaining $5,000 amortized at 24.99% for 12 months (no retroactive interest)
  - **Paid on time:** $10,000 at 0% for 12 months
  - **Required invariant:** retroactive cost > forward-only cost > paid-on-time cost
- **Line chart metric:** Repurpose `MonthlyDataPoint.cumulative_cost` to be cumulative TRUE cost (payment + opportunity_cost - tax_savings + inflation_adjustment). Fix in engine builders so chart and detail table use the same data.
- **Chart label:** Change to "Cumulative True Cost Over Time" to match bar chart/recommendation terminology.
- **Promo options:** Plot BOTH paid-on-time (solid line) and not-paid-on-time (dashed line) as separate lines on the chart.
- **Not-paid line label:** Suffix with "(not paid on time)" -- e.g., "Option 2 (not paid on time)".
- **Single continuous MonthlyDataPoint series** covering both promo period (minimum payments, 0% interest) and post-promo period (full amortization at post-promo APR).
- **Test strategy:** Assert exact Decimal values. Invariant assertions. Worked example as code comment above `_build_promo_result()`.

### Claude's Discretion
- Chart test thoroughness (endpoint match vs all data points)
- Internal implementation of the two-phase MonthlyDataPoint construction
- How to handle edge cases (e.g., promo term = comparison period, post_promo_apr = 0)
- SVG styling details for dashed penalty lines

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ENG-01 | Promo penalty modeling produces distinct costs for deferred-interest (retroactive) vs forward-only interest scenarios | Bug confirmed: both branches of `_build_promo_result()` lines 328-347 construct identical `FinancingOption` objects. Fix requires building custom two-phase MonthlyDataPoint series with minimum payments during promo, then different post-promo amortization depending on deferred_interest flag. |
| ENG-02 | Line chart plots cumulative true cost per period, not cumulative payments | Bug confirmed: `_build_loan_result()` line 239 sets `cumulative_cost=quantize_money(cumulative)` where `cumulative` is `down + sum(payments)`. Must change to use true cost formula: `payment + opportunity_cost - tax_savings + inflation_adjustment`. Reference implementation exists in `results.py:_monthly_data_to_rows()` lines 358-359. |
| TEST-01 | Tests prove deferred-interest flags materially change not_paid_on_time results | Tests must use the locked worked example ($10K, 24.99% APR, 12-month promo) and assert specific dollar amounts for retroactive vs forward-only vs paid-on-time. Invariant: retroactive > forward-only > paid-on-time. |
| TEST-02 | Tests assert line chart data points match cumulative true cost metric | Tests must verify that `MonthlyDataPoint.cumulative_cost` equals the running sum of `payment + opportunity_cost - tax_savings + inflation_adjustment`, not just cumulative payments. |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python Decimal | stdlib | All monetary arithmetic | Already used throughout; no floats in financial calcs |
| Pydantic | existing | Frozen model validation (MonthlyDataPoint, OptionResult, PromoResult) | Already used; ConfigDict(frozen=True) on all models |
| pytest | existing | Test framework | Already configured in pyproject.toml |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| fathom.money.quantize_money | Phase 13 | Cent-precision rounding | Every monetary calculation result |
| fathom.amortization.amortization_schedule | existing | Standard amortization generation | Post-promo amortization after promo boundary |
| fathom.amortization.monthly_payment | existing | Monthly payment calculation | Verifying amortization amounts in tests |

### Alternatives Considered
None -- this phase modifies existing code, no new libraries needed.

## Architecture Patterns

### Key Bug #1: Identical Promo Branches (ENG-01)

**Current broken code** (engine.py lines 328-347):
```python
if option.deferred_interest and option.retroactive_interest:
    not_paid_option = FinancingOption(
        option_type=OptionType.TRADITIONAL_LOAN,
        label=option.label,
        purchase_price=option.purchase_price,  # SAME
        apr=post_apr,                           # SAME
        term_months=remaining_term,             # SAME
        down_payment=option.down_payment,       # SAME
    )
else:
    not_paid_option = FinancingOption(
        option_type=OptionType.TRADITIONAL_LOAN,
        label=option.label,
        purchase_price=option.purchase_price,  # IDENTICAL!
        apr=post_apr,                           # IDENTICAL!
        term_months=remaining_term,             # IDENTICAL!
        down_payment=option.down_payment,       # IDENTICAL!
    )
```

Both branches create the exact same FinancingOption and pass it to `_build_loan_result()`. The fix cannot simply adjust parameters -- it requires building a custom two-phase schedule.

**Required fix pattern:**
1. Cannot delegate to `_build_loan_result()` for the not-paid scenario because the payment structure is fundamentally different (minimum payments during promo, then amortization of a different principal).
2. Must build MonthlyDataPoint series manually:
   - Months 1-12: minimum payments at 0% interest
   - Month 13: retroactive interest lump sum added to remaining balance (deferred) or not (forward-only)
   - Months 13-24: standard amortization of the post-promo balance at post_promo_apr
3. Can reuse `amortization_schedule()` for the post-promo portion only.

### Key Bug #2: Wrong Cumulative Cost Metric (ENG-02)

**Current broken code** (engine.py `_build_loan_result` line 228-239):
```python
cumulative = down
for i, dp in enumerate(schedule):
    cumulative = cumulative + dp.payment  # <-- cumulative PAYMENTS only
    monthly_data.append(
        MonthlyDataPoint(
            cumulative_cost=quantize_money(cumulative),  # <-- wrong metric
            ...
        ),
    )
```

**Reference implementation** (results.py `_monthly_data_to_rows` line 358-359):
```python
net = dp.payment + dp.opportunity_cost - dp.tax_savings + dp.inflation_adjustment
cumulative += net
```

The fix must apply the true cost formula in all three engine builders. The `_monthly_data_to_rows` function in results.py already computes the correct metric for the detail table -- the engine builders must match this.

### Pattern: Two-Phase MonthlyDataPoint Construction

For the not-paid-on-time scenario:

```python
# Phase 1: Promo period (months 1 to promo_term)
# - payment = min_payment = required_monthly / 2
# - interest_portion = Decimal(0)  (0% APR during promo)
# - principal_portion = min_payment
# - remaining_balance decreases by min_payment each month

# Promo boundary (month promo_term + 1):
# - remaining = principal - (promo_term * min_payment)
# - IF deferred_interest: balance = remaining + (principal * post_apr * promo_term/12)
# - IF forward_only: balance = remaining (no retroactive charge)

# Phase 2: Post-promo (months promo_term+1 to 2*promo_term)
# - Use amortization_schedule(post_promo_balance, post_apr, promo_term)
# - Month numbers continue from promo_term+1
```

### Pattern: Dual Lines for Promo Options on Chart

**Current `_collect_option_points`** (charts.py line 144-145):
```python
if isinstance(result, PromoResult):
    return result.paid_on_time  # Only plots paid-on-time!
```

Must change `_collect_option_points` and `prepare_line_chart` to:
1. Detect PromoResult
2. Emit two entries in the sorted_options/all_points lists: one for paid-on-time (solid), one for not-paid-on-time (dashed)
3. The not-paid line should use a dashed pattern
4. The not-paid line label should be suffixed with "(not paid on time)"

**Integration point:** `routes.py` line 350-353 builds `sorted_options` for charts. This needs to include not-paid entries for promo options as additional (name, cost) tuples.

### Anti-Patterns to Avoid
- **Delegating not-paid to `_build_loan_result()`:** The whole bug is that this delegation flattens the two-phase structure. Must build the MonthlyDataPoint series directly.
- **Spreading retroactive interest across months:** Per locked decision, retroactive interest is a lump sum at the promo boundary. Do not amortize it.
- **Using floats anywhere in calculations:** All monetary math must use Decimal. Convert to float only at SVG rendering boundary (`_to_float()`).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Post-promo amortization schedule | Custom month-by-month interest/principal split | `amortization_schedule(post_promo_balance, post_apr, promo_term)` | Handles final-payment adjustment, rounding, edge cases |
| Cent-precision rounding | Inline `Decimal.quantize()` calls | `quantize_money()` from `fathom.money` | Canonical source per Phase 13 |
| Per-period opportunity cost | Manual investment pool tracking | `compute_opportunity_cost_per_period()` | Already handles pool depletion, freed-cash phases |

**Key insight:** The post-promo amortization (Phase 2 of not-paid scenario) is a standard amortization and should use the existing `amortization_schedule()`. Only the promo period (Phase 1) and the boundary calculation need custom logic.

## Common Pitfalls

### Pitfall 1: Comparison Period Mismatch
**What goes wrong:** The not-paid-on-time scenario has a 24-month timeline (12 promo + 12 post-promo) but the comparison period might be only 12 months (set by `_determine_comparison_period` from term_months).
**Why it happens:** `_determine_comparison_period` uses `opt.term_months` which for promo is the promo term (12), not the full not-paid timeline (24).
**How to avoid:** The comparison period is already determined before `_build_promo_result` runs. The not-paid scenario naturally extends beyond it. Either: (a) ensure comparison_period accounts for 2x promo term, or (b) let the not-paid MonthlyDataPoint series be longer than comparison_period and handle in chart code. Per the existing pattern of padding shorter loans (engine.py line 247), option (a) is more consistent.
**Warning signs:** Not-paid line stops at month 12 instead of showing the full 24-month arc.

### Pitfall 2: Frozen Pydantic Models
**What goes wrong:** Trying to mutate `MonthlyDataPoint` or `OptionResult` after creation fails because `ConfigDict(frozen=True)`.
**Why it happens:** All models use frozen config.
**How to avoid:** Compute all field values before constructing the MonthlyDataPoint. Cannot use `model_copy(update={...})` pattern implicitly -- must construct new instances.

### Pitfall 3: Month Numbering Continuity
**What goes wrong:** Post-promo months start from month 1 instead of month `promo_term + 1`, creating duplicate month numbers.
**Why it happens:** `amortization_schedule()` always starts from month 1.
**How to avoid:** When reusing `amortization_schedule()` for the post-promo portion, adjust the month numbers by adding `promo_term` as an offset.

### Pitfall 4: Opportunity Cost for Not-Paid Scenario
**What goes wrong:** Computing opportunity cost for not-paid-on-time using the wrong payment stream (standard loan payments vs minimum payments then amortization).
**Why it happens:** The current code delegates to `_build_loan_result()` which computes opportunity cost based on a single-phase loan.
**How to avoid:** Compute opportunity cost for the not-paid scenario using the actual two-phase payment stream: minimum payments during promo, then amortization payments post-promo. May need to compute manually or use a synthetic FinancingOption that matches the real cash flows.

### Pitfall 5: Chart sorted_options Must Include Not-Paid Entries
**What goes wrong:** Not-paid lines don't appear on chart because `sorted_options` only has one entry per option name.
**Why it happens:** `routes.py` builds sorted_options from `options_data` which has one entry per option.
**How to avoid:** When building chart-specific sorted_options, detect promo options and add an extra tuple for the not-paid scenario with the suffixed label.

## Code Examples

### Cumulative True Cost Formula (from results.py -- reference implementation)
```python
# Source: src/fathom/results.py lines 358-359
net = dp.payment + dp.opportunity_cost - dp.tax_savings + dp.inflation_adjustment
cumulative += net
```

### Minimum Payment Calculation
```python
# Per locked decision
required_monthly = quantize_money(principal / term)  # already in engine.py line 308
min_payment = quantize_money(required_monthly / 2)
```

### Retroactive Interest Lump Sum
```python
# Per locked decision
retroactive_interest = quantize_money(principal * post_apr * Decimal(term) / Decimal(12))
# Added at promo boundary: post_promo_balance = remaining + retroactive_interest
```

### Post-Promo Amortization Reuse
```python
# Reuse existing amortization_schedule for post-promo period
post_schedule = amortization_schedule(post_promo_balance, post_apr, term)
# Adjust month numbers
for dp in post_schedule:
    # Construct new MonthlyDataPoint with month = dp.month + promo_term
    ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Both promo branches delegate to `_build_loan_result` | Custom two-phase schedule construction | This phase | Enables distinct deferred vs forward-only costs |
| `cumulative_cost` = sum of payments | `cumulative_cost` = cumulative true cost | This phase | Chart and detail table use same metric |
| Chart shows one line per promo option | Chart shows two lines (paid + not-paid) | This phase | Users see penalty scenario visually |

## Open Questions

1. **Comparison period for promo not-paid scenarios**
   - What we know: `_determine_comparison_period` returns 12 for a 12-month promo, but not-paid spans 24 months.
   - What's unclear: Should comparison_period be updated to 24 months when a promo option is present? Or should the not-paid MonthlyDataPoint series simply extend beyond comparison_period?
   - Recommendation: Update `_determine_comparison_period` to account for 2x promo term when promo options exist, since the not-paid scenario is a core part of the analysis. This ensures padding, chart axes, and opportunity cost calculations all align. Alternatively, the not-paid scenario can simply produce a longer series and the chart code can handle variable-length series (it already downsamples).

2. **Opportunity cost computation for two-phase payment stream**
   - What we know: `compute_opportunity_cost()` expects a single FinancingOption and derives a flat monthly payment.
   - What's unclear: How to compute opportunity cost when payments vary (minimum during promo, then amortization payments post-promo).
   - Recommendation: Compute opportunity cost manually using the actual payment stream, following the same pool-growth-minus-deduction logic as `compute_opportunity_cost()` but with the variable payment amounts. Or simplify by computing per-period opportunity cost inline.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (configured in pyproject.toml) |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/test_engine.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ENG-01 | Deferred-interest produces higher cost than forward-only | unit | `uv run pytest tests/test_engine.py::test_deferred_interest_higher_than_forward_only -x` | No -- Wave 0 |
| ENG-01 | Forward-only produces higher cost than paid-on-time | unit | `uv run pytest tests/test_engine.py::test_forward_only_higher_than_paid_on_time -x` | No -- Wave 0 |
| ENG-01 | Worked numeric example exact values | unit | `uv run pytest tests/test_engine.py::test_promo_worked_example_exact_values -x` | No -- Wave 0 |
| ENG-02 | Cumulative cost equals true cost formula | unit | `uv run pytest tests/test_engine.py::test_cumulative_cost_is_true_cost -x` | No -- Wave 0 |
| TEST-01 | Deferred-interest flag changes results | unit | Same as ENG-01 tests | No -- Wave 0 |
| TEST-02 | Chart data points match cumulative true cost | unit | `uv run pytest tests/test_charts.py::test_line_chart_uses_true_cost -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_engine.py tests/test_charts.py -x`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] New test functions in `tests/test_engine.py` -- covers ENG-01, TEST-01 (promo penalty invariants and worked example)
- [ ] New test functions in `tests/test_charts.py` -- covers ENG-02, TEST-02 (cumulative true cost in chart data)
- [ ] Fixture for forward-only promo option (deferred_interest=False) in `tests/conftest.py`

## Sources

### Primary (HIGH confidence)
- Direct code inspection of `src/fathom/engine.py` -- confirmed identical branches (lines 328-347)
- Direct code inspection of `src/fathom/results.py` -- confirmed correct true cost formula (lines 358-359)
- Direct code inspection of `src/fathom/charts.py` -- confirmed `_get_option_result` only uses paid_on_time (line 145)
- Direct code inspection of `src/fathom/models.py` -- confirmed frozen Pydantic models, field structure
- Direct code inspection of `src/fathom/amortization.py` -- confirmed reusable for post-promo amortization

### Secondary (MEDIUM confidence)
- CONTEXT.md locked decisions -- user-validated business rules for deferred vs forward-only interest

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new libraries, all existing code
- Architecture: HIGH - bugs confirmed via direct code inspection, fix patterns clear
- Pitfalls: HIGH - identified from actual code structure and frozen model constraints

**Research date:** 2026-03-15
**Valid until:** 2026-04-15 (stable domain, internal codebase)
