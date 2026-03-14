# Phase 11: Detailed Period Breakdown - Research

**Researched:** 2026-03-13
**Domain:** Server-side table rendering, HTMX tab navigation, CSS column toggling
**Confidence:** HIGH

## Summary

This phase surfaces per-period cost data that the engine already computes (or nearly computes) into a tabbed, toggleable breakdown table. The primary work is (1) extending `MonthlyDataPoint` with per-period opportunity cost, inflation adjustment, and tax savings fields, (2) computing those values in the engine builders, (3) building a new results module function to prepare detailed breakdown data, (4) creating HTMX-driven tab UI with a compare view, and (5) adding client-side column toggle JS.

The existing codebase provides strong patterns to follow: `_build_breakdown_rows()` for row construction, `breakdown_table.html` for promo dual-column layout, event delegation in `formatting.js` for HTMX-compatible JS, and CSS custom properties for dark mode. The biggest technical risk is correctly computing per-period opportunity cost (the engine currently only tracks aggregates), but `compute_opportunity_cost()` already has the per-month loop structure -- it just needs to emit per-month values instead of a single sum.

**Primary recommendation:** Extend `MonthlyDataPoint` with three new Decimal fields, modify the three engine builder functions to populate them, then build the tab/table/toggle UI as a new section below the existing breakdown table.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Default view is **monthly rows**; user can toggle to **annual summary** (12-month aggregation)
- Monthly/annual toggle uses **HTMX server-side aggregation** -- server computes annual sums from monthly data
- All options show rows for the **full comparison period**, padded with zeros for months beyond the option's term
- Cash options show full comparison period with zero-payment rows, making opportunity cost accrual visible over time
- **Cumulative True Total Cost column** always visible -- shows cost building over time per period
- **Sticky totals row** at the bottom -- always visible when scrolling long tables (60+ months)
- Promo options use **dual columns** (paid on time / not paid on time) -- matching existing breakdown_table.html pattern
- **HTMX tab switching** -- each tab click fetches the table via HTMX partial swap
- **One tab per configured option** + a **Compare tab**
- **Compare tab** shows per-period rows with **Payment + Cumulative True Total Cost** per option (2 columns per option = max 8 data columns + period column)
- **Placement:** below existing summary breakdown table
- **Checkbox row above the table** -- horizontal row of labeled checkboxes, one per cost factor
- **All columns on by default** -- user sees full picture immediately
- **Client-side JS** for toggle visibility -- CSS class toggling, no server round-trip
- **Column toggle state persists across tab switches** -- JS stores hidden column state, applies to each newly loaded tab
- **Extend MonthlyDataPoint** with per-period `opportunity_cost`, `inflation_adjustment`, and `tax_savings` fields
- Engine stores per-month results instead of only aggregates
- Single source of truth: per-period values sum to the totals on OptionResult

### Claude's Discretion
- Tab styling (underline tabs, pill tabs, etc.) -- should feel native to Pico CSS
- Checkbox row styling and dark mode variants
- Sticky totals row implementation (CSS position: sticky)
- How column toggle JS interacts with HTMX-swapped content (likely needs event delegation or htmx:afterSwap hook)
- MonthlyDataPoint field naming for new per-period cost factors
- Annual aggregation endpoint design (query parameter vs. separate route)
- Compare tab column header formatting when option names are long
- Whether to hide all-zero columns automatically (like breakdown table hides all-zero rows)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DETAIL-01 | Per-period (monthly/annual) cost breakdown with all cost factors | Engine extension for per-period opp cost/inflation/tax; server-side annual aggregation; new template |
| DETAIL-02 | Tab switching between options | HTMX partial swap pattern (already established); new route returning per-option table partial |
| DETAIL-03 | Compare tab with side-by-side key totals | New compare template showing Payment + Cumulative True Total Cost per option per period |
| DETAIL-04 | Column toggle on/off | Client-side JS with CSS class toggling; state persistence across HTMX swaps via htmx:afterSwap |
| DETAIL-05 | Accessible table (th scope, ARIA, keyboard tabs) | Standard HTML table accessibility; ARIA tablist pattern for tab navigation |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Flask | existing | Route handling for tab endpoints | Already in use |
| Jinja2 | existing | Server-side template rendering | Already in use |
| HTMX | existing (vendored) | Tab switching via partial swaps | Already in use for form updates |
| Pydantic | existing | MonthlyDataPoint model extension | Already in use for all models |
| Pico CSS | existing (vendored) | Base styling for tabs and tables | Already in use |

### Supporting
No new dependencies needed. This phase uses only existing libraries.

## Architecture Patterns

### Recommended Project Structure
```
src/fathom/
  models.py              # Extend MonthlyDataPoint with 3 new fields
  engine.py              # Modify _build_*_result() to compute per-period values
  results.py             # New function to build detailed breakdown data
  routes.py              # New HTMX endpoints for tab switching + annual toggle
  templates/
    partials/results.html                    # Add detailed breakdown section include
    partials/results/detailed_breakdown.html # Tab container + checkbox row
    partials/results/detailed_table.html     # Per-option period table (HTMX partial)
    partials/results/detailed_compare.html   # Compare tab table (HTMX partial)
  static/
    detail_toggle.js     # Column toggle logic
    style.css            # Tab, sticky, checkbox styles added
```

### Pattern 1: Extending MonthlyDataPoint
**What:** Add `opportunity_cost`, `inflation_adjustment`, and `tax_savings` Decimal fields to MonthlyDataPoint.
**When to use:** Required for DETAIL-01.
**Example:**
```python
class MonthlyDataPoint(BaseModel):
    model_config = ConfigDict(frozen=True)
    month: int
    payment: Decimal
    interest_portion: Decimal
    principal_portion: Decimal
    remaining_balance: Decimal
    investment_balance: Decimal
    cumulative_cost: Decimal
    # New per-period cost factors
    opportunity_cost: Decimal = Field(default_factory=lambda: Decimal(0))
    inflation_adjustment: Decimal = Field(default_factory=lambda: Decimal(0))
    tax_savings: Decimal = Field(default_factory=lambda: Decimal(0))
```

**Key consideration:** Using defaults of Decimal(0) ensures backward compatibility -- existing MonthlyDataPoint construction in tests and engine code that doesn't set these fields will still work. The `frozen=True` config means construction must pass all values; however, the default_factory approach handles this cleanly.

### Pattern 2: Per-Period Opportunity Cost Computation
**What:** Extract per-month opportunity cost from the existing loop in `compute_opportunity_cost()`.
**When to use:** Required for accurate per-period breakdown.
**Implementation approach:** The function `compute_opportunity_cost()` in `opportunity.py` already iterates month-by-month computing `growth = pool * monthly_rate`. Create a new function `compute_opportunity_cost_per_period()` that returns a `list[Decimal]` of per-month growth values instead of a single aggregate. The sum of the list must equal the existing aggregate.

```python
def compute_opportunity_cost_per_period(
    option: FinancingOption,
    settings: GlobalSettings,
    comparison_period: int,
) -> list[Decimal]:
    """Return per-month opportunity cost (investment growth) for each period."""
    # Same loop as compute_opportunity_cost but collecting per-month growth
    monthly_rate = settings.return_rate / 12
    pool = ...  # same setup as compute_opportunity_cost
    per_period: list[Decimal] = []
    for _month in range(loan_months):
        growth = pool * monthly_rate
        per_period.append(quantize_money(growth))
        pool = pool + growth - monthly_deduction
        if pool < Decimal(0):
            pool = Decimal(0)
    # Phase 2 freed-cash similarly
    return per_period
```

### Pattern 3: Per-Period Inflation Adjustment
**What:** Compute per-month inflation adjustment (nominal - discounted) for each payment.
**Implementation:** The `inflation.py` module already has `discount_cash_flows()` that returns per-month discounted values. Per-period adjustment = `nominal_payment - discounted_payment` for each month.

```python
def compute_inflation_adjustment_per_period(
    nominal_payments: list[Decimal],
    annual_inflation: Decimal,
) -> list[Decimal]:
    discounted = discount_cash_flows(nominal_payments, annual_inflation)
    return [
        quantize_money(nom - disc)
        for nom, disc in zip(nominal_payments, discounted)
    ]
```

### Pattern 4: Per-Period Tax Savings
**What:** Per-month tax savings = `interest_portion * tax_rate`.
**Implementation:** Trivially `quantize_money(interest * tax_rate)` for each month.

### Pattern 5: HTMX Tab Switching
**What:** Tab navigation that loads per-option detailed tables via HTMX partial swap.
**When to use:** DETAIL-02, DETAIL-03.
**Implementation:** Use the ARIA tablist pattern with HTMX:

```html
<div role="tablist" aria-label="Detailed breakdown by option">
  {% for opt in display.options_data %}
  <button role="tab"
          id="tab-{{ loop.index0 }}"
          aria-selected="{% if loop.first %}true{% else %}false{% endif %}"
          aria-controls="detail-panel"
          hx-get="/partials/detail/{{ loop.index0 }}"
          hx-target="#detail-panel"
          hx-swap="innerHTML"
          hx-include="#comparison-form"
          class="{% if loop.first %}active{% endif %}">
    {{ opt.name }}
  </button>
  {% endfor %}
  <button role="tab" id="tab-compare"
          aria-selected="false"
          aria-controls="detail-panel"
          hx-get="/partials/detail/compare"
          hx-target="#detail-panel"
          hx-swap="innerHTML"
          hx-include="#comparison-form">
    Compare
  </button>
</div>
<div id="detail-panel" role="tabpanel" aria-labelledby="tab-0">
  {# First tab content loaded inline, others via HTMX #}
</div>
```

**Critical:** The tab endpoints need the full form data (via `hx-include="#comparison-form"`) to recompute results and extract the relevant option's detailed data. Alternatively, the detailed data can be computed once on form submission and passed as template context for the initial tab, with subsequent tabs fetched via HTMX using the same form data.

**Better approach:** Compute all detailed data on form submission in `compare_options()`, include the first option's table inline in the results template, and have tab clicks POST the form to a detail endpoint that returns just the table partial. This avoids needing to cache results server-side.

### Pattern 6: Column Toggle with HTMX Compatibility
**What:** Client-side JS that toggles CSS classes on table columns, surviving HTMX content swaps.
**Implementation:** Use `htmx:afterSwap` event to re-apply hidden column state after tab switches.

```javascript
(function() {
  "use strict";
  var hiddenCols = {};  // { "col-opp-cost": true, ... }

  function applyHidden(container) {
    Object.keys(hiddenCols).forEach(function(cls) {
      var cells = container.querySelectorAll("." + cls);
      for (var i = 0; i < cells.length; i++) {
        cells[i].style.display = hiddenCols[cls] ? "none" : "";
      }
    });
  }

  document.addEventListener("htmx:afterSwap", function(evt) {
    if (evt.detail.target.id === "detail-panel") {
      applyHidden(evt.detail.target);
    }
  });

  // Checkbox change handler (delegated)
  document.addEventListener("change", function(e) {
    if (!e.target.matches(".col-toggle")) return;
    var col = e.target.dataset.column;
    hiddenCols[col] = !e.target.checked;
    applyHidden(document.getElementById("detail-panel"));
  });
})();
```

### Pattern 7: Annual Aggregation
**What:** Server-side aggregation of monthly data into 12-month groups.
**Implementation:** Use a query parameter `?granularity=annual` on the detail endpoints. Server groups MonthlyDataPoint by `(month - 1) // 12` and sums Decimal fields per group.

### Pattern 8: Sticky Totals Row
**What:** CSS `position: sticky; bottom: 0` on the `<tfoot>` row.
**Implementation:**
```css
.detail-table tfoot tr {
  position: sticky;
  bottom: 0;
  background: var(--pico-background-color);
  font-weight: 700;
  border-top: 2px solid var(--pico-color);
  z-index: 1;
}
```

### Anti-Patterns to Avoid
- **Client-side calculation:** Do not compute per-period costs in JS. All financial math stays server-side.
- **Caching results:** Do not try to store ComparisonResult in a session or global. Re-compute from form data on each request (stateless architecture).
- **Separate monthly_data list:** Do not create a parallel data structure. Extend the existing MonthlyDataPoint -- single source of truth.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tab accessibility | Custom keyboard handlers | ARIA tablist pattern with `role="tab"`, `aria-selected`, keyboard activation | Standard pattern, tested with screen readers |
| Number formatting | String concatenation | Jinja `comma` filter (already exists) | Consistent with existing breakdown table |
| Dark mode colors | Hardcoded hex values | CSS custom properties with `@media (prefers-color-scheme: dark)` | Established pattern in style.css |
| Table scroll | JS scroll handlers | `overflow-x: auto` wrapper (already used in breakdown_table.html) | CSS-only, works everywhere |

## Common Pitfalls

### Pitfall 1: Per-Period Values Not Summing to Aggregates
**What goes wrong:** Rounding each per-period value individually can cause the sum to differ from the aggregate by a few cents.
**Why it happens:** `quantize_money()` applied per-period introduces rounding error accumulation.
**How to avoid:** Compute all per-period values, sum them, then adjust the last period by the difference (epsilon correction). Or accept the tiny discrepancy and document it.
**Warning signs:** Test that asserts `sum(monthly.opportunity_cost for monthly in monthly_data) == result.opportunity_cost` fails by 1-2 cents.

### Pitfall 2: HTMX Tab Content Missing Form Data
**What goes wrong:** Tab click sends GET request without form data, server cannot recompute results.
**Why it happens:** Tabs often use `hx-get` which doesn't include form data by default.
**How to avoid:** Use `hx-post` for tab switching, or use `hx-include="#comparison-form"` with `hx-get`. POST is cleaner since the form data can be large.
**Warning signs:** Tab endpoint returns error or empty table.

### Pitfall 3: Column Toggle Lost After Tab Switch
**What goes wrong:** User hides a column, clicks a different tab, column reappears.
**Why it happens:** HTMX replaces the table DOM, new DOM has no hidden state.
**How to avoid:** Store hidden column state in JS variable, re-apply in `htmx:afterSwap` handler.
**Warning signs:** Checkboxes show "unchecked" but columns are visible after tab switch (or vice versa). Keep checkboxes outside the HTMX swap target.

### Pitfall 4: Frozen Pydantic Model with New Required Fields
**What goes wrong:** Adding required fields to MonthlyDataPoint breaks all existing construction sites.
**Why it happens:** `frozen=True` and no defaults means every constructor call must provide the new fields.
**How to avoid:** Use `Field(default_factory=lambda: Decimal(0))` for new fields. This makes them optional at construction time while still present in the model.
**Warning signs:** Dozens of test failures and engine code errors after model change.

### Pitfall 5: Promo Options Need Dual Detailed Tables
**What goes wrong:** Promo tab shows only one scenario.
**Why it happens:** PromoResult has `paid_on_time` and `not_paid_on_time`, each with their own `monthly_data`.
**How to avoid:** Follow the existing dual-column pattern from `breakdown_table.html`. For the detailed table, show two value columns per row (or two sub-tables within the tab).
**Warning signs:** User sees detailed breakdown for promo option but cannot compare both outcomes.

### Pitfall 6: Table Height with 60+ Monthly Rows
**What goes wrong:** Table becomes extremely long, unusable without scrolling.
**Why it happens:** 60-month loan = 60 rows minimum.
**How to avoid:** The sticky totals row (locked decision) helps. Annual aggregation toggle (locked decision) reduces to 5 rows. Consider a max-height with vertical scroll on the table container.
**Warning signs:** User must scroll past the table to see charts or other content.

## Code Examples

### Engine Builder Modification (for _build_loan_result)
```python
# In _build_loan_result, after computing schedule:
# Compute per-period values
opp_per_period = compute_opportunity_cost_per_period(option, settings, comparison_period)
inflation_per_period = (
    compute_inflation_adjustment_per_period(
        [dp.payment for dp in schedule], settings.inflation_rate
    )
    if settings.inflation_enabled
    else [Decimal(0)] * len(schedule)
)
tax_per_period = (
    [quantize_money(dp.interest_portion * settings.tax_rate) for dp in schedule]
    if settings.tax_enabled
    else [Decimal(0)] * len(schedule)
)

# Pad to comparison_period length
while len(opp_per_period) < comparison_period:
    opp_per_period.append(Decimal(0))
# ... same for inflation and tax

# Build monthly_data with new fields
cumulative = down
for i, dp in enumerate(schedule):
    cumulative += dp.payment
    monthly_data.append(
        MonthlyDataPoint(
            month=dp.month,
            payment=dp.payment,
            interest_portion=dp.interest_portion,
            principal_portion=dp.principal_portion,
            remaining_balance=dp.remaining_balance,
            investment_balance=Decimal(0),
            cumulative_cost=quantize_money(cumulative),
            opportunity_cost=opp_per_period[i],
            inflation_adjustment=inflation_per_period[i] if i < len(inflation_per_period) else Decimal(0),
            tax_savings=tax_per_period[i] if i < len(tax_per_period) else Decimal(0),
        ),
    )
```

### Annual Aggregation Helper
```python
def aggregate_annual(monthly_data: list[MonthlyDataPoint]) -> list[dict]:
    """Group monthly data into annual summaries."""
    years: list[dict] = []
    for year_idx in range(0, len(monthly_data), 12):
        chunk = monthly_data[year_idx : year_idx + 12]
        years.append({
            "period": f"Year {year_idx // 12 + 1}",
            "payment": sum(dp.payment for dp in chunk),
            "interest_portion": sum(dp.interest_portion for dp in chunk),
            "principal_portion": sum(dp.principal_portion for dp in chunk),
            "opportunity_cost": sum(dp.opportunity_cost for dp in chunk),
            "inflation_adjustment": sum(dp.inflation_adjustment for dp in chunk),
            "tax_savings": sum(dp.tax_savings for dp in chunk),
            "cumulative_cost": chunk[-1].cumulative_cost,
        })
    return years
```

### Tab Styling (Pico CSS Native Feel)
```css
/* Underline tabs matching Pico's design language */
.detail-tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid var(--pico-muted-border-color);
  margin-bottom: 1rem;
  overflow-x: auto;
}

.detail-tabs [role="tab"] {
  all: unset;
  padding: 0.5rem 1rem;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  white-space: nowrap;
  color: var(--pico-muted-color);
  font-size: 0.95rem;
}

.detail-tabs [role="tab"][aria-selected="true"] {
  color: var(--pico-primary);
  border-bottom-color: var(--pico-primary);
  font-weight: 600;
}

.detail-tabs [role="tab"]:hover {
  color: var(--pico-primary);
}

.detail-tabs [role="tab"]:focus-visible {
  outline: 2px solid var(--pico-primary);
  outline-offset: -2px;
}
```

### Column Toggle Checkbox Row
```html
<fieldset class="col-toggles" aria-label="Toggle visible columns">
  <label><input type="checkbox" class="col-toggle" data-column="col-payment" checked> Payment</label>
  <label><input type="checkbox" class="col-toggle" data-column="col-interest" checked> Interest</label>
  <label><input type="checkbox" class="col-toggle" data-column="col-principal" checked> Principal</label>
  <label><input type="checkbox" class="col-toggle" data-column="col-opp-cost" checked> Opportunity Cost</label>
  <label><input type="checkbox" class="col-toggle" data-column="col-inflation" checked> Inflation Adj.</label>
  <label><input type="checkbox" class="col-toggle" data-column="col-tax" checked> Tax Savings</label>
</fieldset>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Aggregate-only cost factors | Per-period cost factors in MonthlyDataPoint | This phase | Enables granular inspection of cost buildup |
| Summary table only | Summary + detailed drill-down tables | This phase | Users can validate and understand the numbers |

## Open Questions

1. **Cumulative True Total Cost per-period computation**
   - What we know: The formula is `total_payments + opp_cost - rebates - tax_savings + inflation_adj` aggregated
   - What's unclear: For cumulative per-period, should it be `cumulative_payments + cumulative_opp_cost - cumulative_tax_savings + cumulative_inflation_adj`? This would require running sums of each factor.
   - Recommendation: Yes, compute running cumulative for each factor and sum them. This matches the "cost building over time" intent from the user decision.

2. **Tab data re-computation vs. form re-submission**
   - What we know: Tabs need the comparison result data. The server is stateless.
   - What's unclear: Whether to re-POST the entire form for each tab switch or find a lighter approach.
   - Recommendation: Use `hx-post` with `hx-include="#comparison-form"` so the full form is resubmitted. The computation is fast (sub-second). This is consistent with the stateless architecture. The endpoint parses, validates, computes, and returns only the requested tab's table partial.

3. **Max-height for table container**
   - What we know: 60+ month tables will be very long.
   - What's unclear: Whether to cap height with vertical scroll.
   - Recommendation: Add `max-height: 70vh; overflow-y: auto` to the table container. Combined with sticky totals row and the annual toggle option, this keeps the page navigable.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2+ |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/ -x -q` |
| Full suite command | `uv run pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DETAIL-01 | Per-period cost factors in MonthlyDataPoint; annual aggregation | unit | `uv run pytest tests/test_engine.py tests/test_models.py -x` | Partial (existing test files, new tests needed) |
| DETAIL-02 | Tab switching returns correct option's table | integration | `uv run pytest tests/test_routes.py -x -k detail` | Needs new tests |
| DETAIL-03 | Compare tab shows side-by-side totals | integration | `uv run pytest tests/test_routes.py -x -k compare` | Needs new tests |
| DETAIL-04 | Column toggle JS works, persists across tab switches | e2e (Playwright) | Playwright MCP automation | Needs new test |
| DETAIL-05 | Table accessibility (th scope, ARIA, keyboard tabs) | e2e (Playwright) | Playwright MCP automation | Needs new test |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/ -x -q`
- **Per wave merge:** `uv run pytest tests/ -v`
- **Phase gate:** Full suite green + Playwright browser verification before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] New tests in `tests/test_engine.py` for per-period cost factor computation
- [ ] New tests in `tests/test_models.py` for extended MonthlyDataPoint
- [ ] New tests in `tests/test_routes.py` for detail tab endpoints
- [ ] Playwright verification for column toggles, tab keyboard navigation, accessibility

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `models.py`, `engine.py`, `opportunity.py`, `inflation.py`, `tax.py`, `results.py`, `routes.py`
- Codebase analysis: existing templates (`breakdown_table.html`, `results.html`, `index.html`)
- Codebase analysis: existing JS patterns (`formatting.js`, `tooltips.js`)
- Codebase analysis: existing CSS patterns (`style.css`)

### Secondary (MEDIUM confidence)
- HTMX `hx-include` for form data with tab switches -- standard HTMX feature, verified from project's existing usage
- ARIA tablist pattern -- WAI-ARIA standard, well-established

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all existing libraries, no new dependencies
- Architecture: HIGH -- extends existing patterns (model/engine/route/template), well-understood codebase
- Pitfalls: HIGH -- identified from direct code analysis of existing MonthlyDataPoint construction, HTMX swap behavior, and Pydantic frozen model constraints

**Research date:** 2026-03-13
**Valid until:** 2026-04-13 (stable -- no external dependency changes)
