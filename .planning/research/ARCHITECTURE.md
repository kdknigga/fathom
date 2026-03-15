# Architecture: v1.2 Code Review Fix Integration

**Domain:** Defect fixes and quality gaps in existing Flask/HTMX SSR financing analyzer
**Researched:** 2026-03-15
**Confidence:** HIGH (all findings based on direct source code inspection)

---

## Existing Architecture (Unchanged)

```
Browser
  HTMX partials + Pico CSS + Popover tooltips + minimal JS (tabs, comma format)
    |
Flask routes.py (Blueprint)
  POST /compare          — full calculation + results render
  POST /partials/option/add|remove  — HTMX option list management
  GET  /partials/option-fields/<idx> — HTMX type switch
  POST /partials/detail/<idx>       — HTMX detailed breakdown tab
  POST /partials/detail/compare     — HTMX compare tab
  POST /export | /import            — JSON file operations
    |
Python Pipeline:
  forms.py: parse_form_data() -> FormInput (Pydantic)
  forms.py: build_domain_objects() -> [FinancingOption], GlobalSettings
  engine.py: compare() -> ComparisonResult
  results.py: analyze_results() -> display dict
  charts.py: prepare_charts() -> SVG coordinate data
    |
Calculation Modules:
  amortization.py | opportunity.py | inflation.py | tax.py | caveats.py
  (each has own quantize_money() copy)
    |
Domain Models (models.py):
  FinancingOption, GlobalSettings, MonthlyDataPoint,
  OptionResult, PromoResult, ComparisonResult
```

---

## Fix Areas: Integration Map

### Fix 1: Promo Penalty Modeling (engine.py)

**The bug:** `_build_promo_result()` lines 327-346 have two branches for `deferred_interest + retroactive_interest` vs forward-only, but both branches construct identical `FinancingOption` objects. The only difference is the branch comment -- the actual `purchase_price`, `apr`, `term_months`, and `down_payment` are the same in both paths.

**Root cause:** The retroactive-interest scenario should apply the post-promo APR to the *full original principal from month 1*, while the forward-only scenario should apply it to only the *remaining unpaid balance* after the promo term. The current code uses `option.purchase_price` (full price) in both branches.

**Integration approach -- modify `_build_promo_result()` only:**

The fix lives entirely within `engine.py:_build_promo_result()`. No model changes, no route changes, no template changes.

Two distinct penalty calculation paths:

```
Path A: Retroactive interest (deferred_interest=True, retroactive_interest=True)
  - Interest accrues on full original principal from month 1
  - Penalty: full principal amortized at post_promo_apr for remaining_term
  - purchase_price for not_paid_option = original purchase_price (current behavior)

Path B: Forward-only interest (deferred_interest=False, or retroactive_interest=False)
  - Interest starts only on remaining balance after promo term
  - Must estimate remaining balance (e.g., assume minimum payments during promo)
  - purchase_price for not_paid_option = estimated remaining balance
  - down_payment for not_paid_option = Decimal(0) (already paid during promo)
```

**Key modeling decision needed:** What balance remains after the promo period for Path B? Options:
1. **Half the principal** (current comment says this but code doesn't do it)
2. **Full principal minus minimum payments** (most realistic -- minimum payments during promo reduce principal)
3. **Full principal** (worst case, what happens if only interest is owed and no principal payments made)

**Recommendation:** Use approach (1) for simplicity -- assume half the balance remains. This is a penalty scenario estimate, not a precise amortization. The key requirement is that Path A and Path B produce *different* numbers, which the current code fails to do.

**Concrete change:**

```python
# Path A: retroactive -- full principal at post_promo_apr
not_paid_option = FinancingOption(
    option_type=OptionType.TRADITIONAL_LOAN,
    label=option.label,
    purchase_price=option.purchase_price,  # full original price
    apr=post_apr,
    term_months=remaining_term if remaining_term > 0 else term,
    down_payment=option.down_payment,
)

# Path B: forward-only -- half remaining balance at post_promo_apr
remaining_balance = quantize_money(principal / 2)
not_paid_option = FinancingOption(
    option_type=OptionType.TRADITIONAL_LOAN,
    label=option.label,
    purchase_price=remaining_balance,  # only remaining balance
    apr=post_apr,
    term_months=remaining_term if remaining_term > 0 else term,
    down_payment=Decimal(0),  # no additional down payment on penalty loan
)
```

**Also fix:** Remove or correct the misleading inline comment about "assume half the balance remains" -- it currently doesn't apply to either branch.

**Files modified:** `engine.py` only.
**Files for tests:** `tests/test_engine.py` -- add tests proving deferred_interest flags produce different `not_paid_on_time.true_total_cost` values.

---

### Fix 2: Validation Bounds for Inflation and Tax Rates (forms.py)

**The bug:** `SettingsInput` validates `return_rate` (0-30% range) but applies no bounds to `inflation_rate` or `tax_rate`. Negative inflation and tax rates above 100% pass through to the engine.

**Integration point:** `SettingsInput` model validator in `forms.py`.

**Where validation belongs: Pydantic validators, not the form layer.** The existing pattern validates return rate inside `SettingsInput.validate_return_rate()`. Inflation and tax rate validation follows the same pattern.

**Why Pydantic, not a separate form-layer check:**
- `SettingsInput` already has a `model_validator` for return rate
- The Pydantic error pipeline (`pydantic_errors_to_dict`) already maps validator errors to template-compatible error keys
- Adding more validators to the same model is consistent and testable
- The validation fires on both form submission AND JSON import (via `FormInput.model_validate`)

**Concrete change -- add validators to `SettingsInput`:**

```python
@model_validator(mode="after")
def validate_inflation_rate(self) -> Self:
    """Validate inflation rate is within reasonable bounds."""
    if not self.inflation_enabled:
        return self
    val = _try_decimal(self.inflation_rate)
    if val is not None and (val < 0 or val > 20):
        msg = "inflation_rate:Inflation rate must be between 0% and 20%."
        raise ValueError(msg)
    return self

@model_validator(mode="after")
def validate_tax_rate(self) -> Self:
    """Validate tax rate is within reasonable bounds."""
    if not self.tax_enabled:
        return self
    val = _try_decimal(self.tax_rate)
    if val is not None and (val < 0 or val > 60):
        msg = "tax_rate:Tax rate must be between 0% and 60%."
        raise ValueError(msg)
    return self
```

**Design note on bounds:**
- Inflation: 0-20%. US historical max was ~14% (1980). 20% provides headroom.
- Tax: 0-60%. US top marginal rate is 37% federal. State taxes can add ~13%. 60% covers all realistic combinations with margin.

**Validation-only-when-enabled:** Only validate when the toggle is on. When inflation/tax is disabled, the rate value is irrelevant (engine skips the calculation), so rejecting it would be confusing UX.

**Template hint update:** Add `min`/`max` attributes to the HTML input elements in `partials/global_settings.html` for client-side guidance (not enforcement -- server validation is authoritative).

**Files modified:** `forms.py` (add validators), `partials/global_settings.html` (add min/max hints).
**Files for tests:** `tests/test_forms.py` -- negative values, over-max values, blank-when-enabled, disabled-with-invalid-value.

---

### Fix 3: Line Chart Metric Correction (charts.py, engine.py)

**The bug:** `_collect_option_points()` in `charts.py` line 185 reads `dp.cumulative_cost` from `MonthlyDataPoint`. In the engine builders, `cumulative_cost` accumulates only payments (the raw `cumulative = down + sum(payments)` running total). It does not include opportunity cost, tax savings, or inflation -- so the line chart diverges from the true total cost metric.

**Meanwhile:** `results.py:_monthly_data_to_rows()` correctly computes `cumulative_true_total_cost` as a running sum of `payment + opportunity_cost - tax_savings + inflation_adjustment` per period. The detailed breakdown table uses this correct metric.

**Two possible fix approaches:**

**Approach A -- Fix at the engine level (modify MonthlyDataPoint.cumulative_cost):**
Change the engine builders to populate `cumulative_cost` with the true cumulative cost (payments + opp cost - tax + inflation). This fixes the data at the source.
- **Pro:** Single source of truth; charts and any future consumer get the right number.
- **Con:** Changes the semantic meaning of an existing field. Any existing test that asserts `cumulative_cost` values would need updating.

**Approach B -- Fix at the chart level (derive from per-period factors):**
Change `_collect_option_points()` to compute cumulative true cost from per-period factors, matching what `_monthly_data_to_rows()` does.
- **Pro:** No change to engine or MonthlyDataPoint semantics. Charts get the right number without disturbing existing data.
- **Con:** Two places (charts.py and results.py) compute the same derived metric.

**Recommendation: Approach B.** The `cumulative_cost` field on `MonthlyDataPoint` is established as "cumulative payments" and tests depend on it. Changing its meaning is a larger, riskier refactor. Instead, the chart code should derive cumulative true cost the same way `_monthly_data_to_rows()` does.

**Concrete change in `charts.py:_collect_option_points()`:**

Replace line 185:
```python
points = [(dp.month, _to_float(dp.cumulative_cost)) for dp in monthly_data]
```

With:
```python
# Derive cumulative true cost from per-period factors
# (matches results.py:_monthly_data_to_rows logic)
cumulative = 0.0
points = []
for dp in monthly_data:
    net = _to_float(
        dp.payment + dp.opportunity_cost - dp.tax_savings + dp.inflation_adjustment
    )
    cumulative += net
    points.append((dp.month, cumulative))
```

**Edge case -- cash options with sparse data (len(monthly_data) <= 1):** The existing fallback at line 181-183 uses `option_result.true_total_cost` for a flat line. This is already the correct metric (true total cost), so no change needed for this path.

**Files modified:** `charts.py` (`_collect_option_points` method).
**Files for tests:** `tests/test_charts.py` -- assert line chart endpoint values match `true_total_cost`, not `total_payments`.

---

### Fix 4: HTMX Endpoint Guards (routes.py)

**The bug:** `add_option()` and `remove_option()` in `routes.py` do not enforce the 2-4 option contract. Adding a 5th option succeeds; removing down to 1 option succeeds.

**Integration point:** `routes.py` add/remove handlers. These are HTMX partial endpoints that return re-rendered option list HTML.

**Guard pattern -- early return with unchanged state:**

```python
MIN_OPTIONS = 2
MAX_OPTIONS = 4

@bp.route("/partials/option/add", methods=["POST"])
def add_option() -> str:
    parsed = extract_form_data(request.form)

    # Guard: do not exceed maximum
    if len(parsed["options"]) >= MAX_OPTIONS:
        # Return current state unchanged
        options = _rebuild_option_list(parsed)
        return render_template(
            "partials/option_list.html",
            options=options,
            option_types=_build_option_types(),
            errors={},
        )

    # ... existing add logic ...

@bp.route("/partials/option/<int:idx>/remove", methods=["POST"])
def remove_option(idx: int) -> str:
    parsed = extract_form_data(request.form)

    # Guard: do not go below minimum
    if len(parsed["options"]) <= MIN_OPTIONS:
        options = _rebuild_option_list(parsed)
        return render_template(
            "partials/option_list.html",
            options=options,
            option_types=_build_option_types(),
            errors={},
        )

    # ... existing remove logic ...
```

**Why return 200 with unchanged state (not 422 or error):** HTMX expects HTML to swap into the target. Returning an error status would trigger `hx-swap-oob` error handling in the browser. Returning the current option list unchanged is the cleanest UX -- the button simply does nothing when at a boundary.

**UI-side complement:** The add/remove buttons should also be disabled at boundaries via template conditionals. This provides immediate visual feedback. But the server guard is the authoritative enforcement.

**Extract shared helper:** Both handlers duplicate the option-list-building loop. Extract `_rebuild_option_list(parsed)` as a helper in `routes.py` to DRY up the shared template-context construction.

**Files modified:** `routes.py` (add guards + extract helper).
**Files for tests:** `tests/test_routes.py` -- POST add at 4 options returns 200 with 4 options; POST remove at 2 options returns 200 with 2 options.

---

### Fix 5: Custom Option Validation + custom_label Wiring (forms.py, models.py, results.py)

**Two sub-issues that should be fixed together:**

**5a. Upfront cash validation for custom options:**

The custom option template shows "Upfront Cash Required" as a field, but `OptionInput.validate_by_type()` does not require `down_payment` for custom options.

**Decision: Make it optional with clear UI copy.** Custom options are intentionally flexible (the whole point is "configure whatever you want"). Requiring `down_payment` would reduce that flexibility. Instead, update the template label to "Upfront Cash (optional)" and add a `0` default for display.

**File modified:** `src/fathom/templates/partials/option_fields/custom.html` (label text change).

**5b. Wire custom_label into results display:**

`custom_label` is parsed in `forms.py` (`OptionInput.custom_label`) but never flows into `FinancingOption` or display output.

**Integration path:**

1. **`models.py`:** Add `custom_label: str | None = None` to `FinancingOption`.
2. **`forms.py:build_domain_objects()`:** Pass `opt.custom_label` to `FinancingOption` constructor when type is CUSTOM and label is non-empty.
3. **`forms.py:build_domain_objects()`:** Use `custom_label` as the `label` for the option when provided (falling back to `"custom"` otherwise). This is actually the simplest approach -- no model change needed. Just set `label = opt.custom_label or "Custom"` when `option_type == OptionType.CUSTOM`.

**Recommendation: Use approach (3) -- just use custom_label as the label.** This avoids adding a new field to `FinancingOption` and flows naturally through the existing display pipeline, which already uses `option.label` everywhere.

```python
# In build_domain_objects, inside the option loop:
if option_type == OptionType.CUSTOM and opt.custom_label and opt.custom_label.strip():
    label = opt.custom_label.strip()
else:
    label = opt.label or option_type.value
```

**Files modified:** `forms.py` (label logic in `build_domain_objects`), `templates/partials/option_fields/custom.html` (label text).
**Files for tests:** `tests/test_forms.py` -- custom option with custom_label produces FinancingOption with that label.

---

### Fix 6: Toggle Visibility for Inflation/Tax Fields (templates, CSS or HTMX)

**The bug:** Inflation Rate and Tax Rate input fields are always visible in `partials/global_settings.html`, regardless of whether their enable checkboxes are checked.

**Two implementation options:**

**Option A: CSS-only (checkbox + sibling combinator):**
```html
<input type="checkbox" id="inflation_enabled" name="inflation_enabled">
<label for="inflation_enabled">Include Inflation</label>
<div class="toggle-target">
    <label for="inflation_rate">Inflation Rate (%)</label>
    <input type="text" id="inflation_rate" name="inflation_rate" ...>
</div>
```
```css
input[name="inflation_enabled"]:not(:checked) ~ .toggle-target { display: none; }
```

- **Pro:** Zero JS, instant, accessible.
- **Con:** Requires the checkbox to be a sibling of (not nested inside a different parent from) the target. May need minor HTML restructuring.

**Option B: HTMX swap (server renders conditional HTML):**
- **Con:** Unnecessary round-trip for pure UI state. Over-engineered for show/hide.

**Recommendation: Option A (CSS-only).** The existing codebase already uses CSS-only column toggles for the detailed breakdown table (checkbox `:not(:checked)` + sibling combinator). This is the same pattern.

**HTML restructuring needed:** The current `global_settings.html` likely wraps checkboxes and rate inputs in separate containers. The CSS sibling combinator requires the checkbox and the target div to share the same parent. Minor restructuring of the template HTML to ensure this relationship.

**Accessibility:** When the field is `display: none`, it is removed from the tab order and screen reader tree. The server still receives the value (hidden fields retain their value), but since `inflation_enabled` won't be in form data when unchecked, the engine correctly skips the calculation.

**Files modified:** `partials/global_settings.html` (restructure), `static/style.css` (toggle rules).
**Files for tests:** Playwright -- check toggle, verify field appears; uncheck, verify field hidden.

---

### Fix 7: Centralize Monetary Rounding (new module)

**The bug:** `quantize_money()` and `CENTS = Decimal("0.01")` are copy-pasted across 5 modules: `amortization.py`, `opportunity.py`, `inflation.py`, `tax.py`, `caveats.py`.

**Integration approach -- new shared utility module:**

Create `src/fathom/money.py`:

```python
"""Shared monetary arithmetic utilities."""

from decimal import Decimal

CENTS = Decimal("0.01")

def quantize_money(value: Decimal) -> Decimal:
    """Round a Decimal value to the nearest cent (two decimal places)."""
    return value.quantize(CENTS)
```

Then update all 5 modules to import from `fathom.money` instead of defining locally:

```python
# In amortization.py, opportunity.py, inflation.py, tax.py, caveats.py:
from fathom.money import quantize_money
# Remove local CENTS and quantize_money definitions
```

**Also update `engine.py`:** Currently imports `quantize_money` from `fathom.amortization`. Change to import from `fathom.money`.

**Why `money.py` and not `utils.py`:** The module name describes the domain concept. `utils.py` is a code smell that accumulates unrelated functions. `money.py` is cohesive -- it holds monetary arithmetic helpers, and future additions (e.g., `format_currency()`) have a clear home.

**Note on `formatting.py`:** The existing `formatting.py` handles display formatting (comma formatting for templates). `money.py` handles arithmetic operations (rounding for calculations). These are distinct concerns and should remain separate modules.

**Files created:** `src/fathom/money.py`.
**Files modified:** `amortization.py`, `opportunity.py`, `inflation.py`, `tax.py`, `caveats.py`, `engine.py` (import changes + remove local definitions).
**Files for tests:** Existing tests continue to pass (behavior unchanged). Add `tests/test_money.py` with basic rounding tests.

---

### Fix 8: Live Result Updates (OUT OF SCOPE)

The code review finding #7 noted the absence of live-as-you-type result updates. **The PROJECT.md explicitly marks this as out of scope:**

> "Live result updates as user types -- submit-driven HTMX is the design (PRD updated v1.2)"

No architecture work needed. The submit-driven HTMX pattern is the intentional design.

---

### Fix 9: Promo Ranking (OUT OF SCOPE)

The code review finding #9 (ranking on optimistic path) is flagged as a design question, not a defect. **The PROJECT.md explicitly marks this as out of scope:**

> "Risk-weighted promo ranking -- optimistic paid-on-time ranking is intentional; caveat handles risk"

No architecture work needed. The current behavior is product-intent.

---

## Data Flow Changes

### Before (v1.1)

```
MonthlyDataPoint.cumulative_cost = running sum of payments only

Line chart: reads cumulative_cost directly -> plots payments, not true cost
Detailed table: _monthly_data_to_rows() computes cumulative_true_total_cost -> correct metric
Promo penalty: same FinancingOption regardless of deferred_interest flags
Validation: return_rate bounded, inflation/tax unbounded
```

### After (v1.2)

```
MonthlyDataPoint.cumulative_cost = unchanged (still payments only -- no model change)

Line chart: _collect_option_points() derives cumulative true cost from per-period factors
           -> matches detailed table metric
Detailed table: _monthly_data_to_rows() unchanged -> still correct
Promo penalty: retroactive path uses full principal; forward path uses estimated remaining
Validation: return_rate, inflation_rate, and tax_rate all bounded
Rounding: all modules import from fathom.money (single definition)
```

---

## New vs Modified Components

### New Components

| Component | Type | Purpose |
|-----------|------|---------|
| `src/fathom/money.py` | Python module | Centralized `quantize_money()` and `CENTS` |
| `tests/test_money.py` | Test module | Unit tests for monetary rounding |

### Modified Components

| Component | Change Type | What Changes |
|-----------|-------------|--------------|
| `engine.py` | Logic fix | `_build_promo_result()` -- two distinct penalty paths |
| `forms.py` | Additive | `SettingsInput` -- inflation/tax rate validators |
| `forms.py` | Logic fix | `build_domain_objects()` -- custom_label as label |
| `charts.py` | Logic fix | `_collect_option_points()` -- derive cumulative true cost |
| `routes.py` | Additive | add/remove guards + `_rebuild_option_list()` helper |
| `amortization.py` | Import change | Import `quantize_money` from `fathom.money` |
| `opportunity.py` | Import change | Import `quantize_money` from `fathom.money` |
| `inflation.py` | Import change | Import `quantize_money` from `fathom.money` |
| `tax.py` | Import change | Import `quantize_money` from `fathom.money` |
| `caveats.py` | Import change | Import `quantize_money` from `fathom.money` |
| `global_settings.html` | Template | Toggle visibility + min/max hints |
| `custom.html` | Template | Label text clarification |
| `style.css` | Additive | Toggle visibility CSS rules |
| `tests/test_engine.py` | Additive | Promo deferred-interest differentiation tests |
| `tests/test_forms.py` | Additive | Inflation/tax bounds tests, custom_label tests |
| `tests/test_routes.py` | Additive | Add-at-max, remove-at-min boundary tests |
| `tests/test_charts.py` | Additive | Line chart metric correctness tests |

---

## Recommended Build Order

Dependencies drive this order. Each phase is independently testable.

### Phase 1: Centralize Monetary Rounding
**Why first:** Zero-risk refactor. No behavior change. Creates clean foundation. All existing tests must still pass after this change (same function, different import location). Getting this out of the way means all subsequent fixes import from the canonical location.

**Scope:** Create `money.py`, update imports in 6 files, add `test_money.py`.

### Phase 2: Promo Penalty Modeling Fix
**Why second:** Highest-severity defect. Self-contained in `engine.py`. No dependencies on other fixes.

**Scope:** Rework `_build_promo_result()`, add engine tests.

### Phase 3: Validation Bounds
**Why third:** High severity, simple change, forms.py only. Independent of engine fix.

**Scope:** Add validators to `SettingsInput`, update template hints, add form tests.

### Phase 4: Line Chart Metric Correction
**Why fourth:** High severity but requires understanding the per-period factor structure. Reading the engine fix (Phase 2) provides context for how per-period factors flow.

**Scope:** Modify `_collect_option_points()`, add chart tests.

### Phase 5: HTMX Endpoint Guards
**Why fifth:** Medium severity, self-contained in routes.py. No dependency on calculation fixes.

**Scope:** Add guards, extract helper, add route tests.

### Phase 6: Custom Option Cleanup
**Why sixth:** Low severity. Two small changes (label wiring + template text).

**Scope:** Modify `build_domain_objects()` label logic, update template, add tests.

### Phase 7: Toggle Visibility
**Why seventh:** Low severity, template/CSS only. No Python logic changes.

**Scope:** Restructure `global_settings.html`, add CSS rules, Playwright tests.

### Phase 8: Test Backfill
**Why last:** All fixes are in place. This phase adds additional test coverage for edge cases and regression scenarios that span multiple fix areas.

**Scope:** Integration tests, browser automation tests for toggle behavior and chart correctness.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Changing MonthlyDataPoint.cumulative_cost Semantics

**What:** Redefining `cumulative_cost` to mean "cumulative true total cost" instead of "cumulative payments."
**Why bad:** Existing tests assert specific `cumulative_cost` values based on the current meaning. The detailed breakdown table in `results.py` already correctly derives cumulative true total cost separately. Changing the field meaning creates a cascade of test updates and risks subtle bugs in any code that relied on the old meaning.
**Instead:** Derive the correct metric at the consumption point (charts.py), matching what results.py already does.

### Anti-Pattern 2: Adding Validation in build_domain_objects()

**What:** Putting inflation/tax bounds checks in the domain object construction step.
**Why bad:** `build_domain_objects()` receives already-validated `FormInput`. Adding validation there creates a second validation layer that can diverge from the Pydantic layer. Error messages from `build_domain_objects()` don't flow through `pydantic_errors_to_dict()` and won't render properly in templates.
**Instead:** All validation in Pydantic models (`SettingsInput`), where the error pipeline is established.

### Anti-Pattern 3: HTTP Error Codes for HTMX Boundary Guards

**What:** Returning 422 or 400 when add/remove hits the boundary.
**Why bad:** HTMX's default behavior on non-2xx responses is to not swap content, leaving the UI in a stale state. Custom error handling requires `htmx:responseError` event listeners -- unnecessary complexity.
**Instead:** Return 200 with the current (unchanged) option list. The button simply has no effect at the boundary.

### Anti-Pattern 4: Separate quantize_money Variants

**What:** Creating `quantize_money_half_up()`, `quantize_money_half_even()`, etc. in the shared module.
**Why bad:** The codebase uses a single rounding mode (default `ROUND_HALF_EVEN` from Decimal). Exposing multiple rounding modes invites inconsistency.
**Instead:** One function, one rounding behavior, one import.

---

## Sources

- Fathom source code: direct inspection of `engine.py`, `forms.py`, `routes.py`, `results.py`, `charts.py`, `models.py`, all 5 calculation modules (HIGH confidence, primary source)
- Code review findings: `docs/code-review-2026-03-15.md` (HIGH confidence, primary source)
- PROJECT.md: scope decisions on live updates and promo ranking (HIGH confidence, primary source)
- Python `decimal.Decimal.quantize` behavior: standard library, no external verification needed (HIGH confidence)

---

*Architecture research for: Fathom v1.2 -- code review fix integration*
*Researched: 2026-03-15*
