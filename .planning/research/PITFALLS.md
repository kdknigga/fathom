# Domain Pitfalls

**Domain:** Fixing calculation bugs, tightening validation, changing chart metrics, and refactoring utilities in an existing SSR financial app (Flask/HTMX/Pydantic/Decimal)
**Researched:** 2026-03-15
**Confidence:** HIGH (derived from direct code inspection of the existing codebase, code review findings, and established patterns in the Flask/Pydantic/HTMX ecosystem)

---

## Context: Previous Pitfalls

The v1.0 (2026-03-10) and v1.1 (2026-03-13) PITFALLS documents covered foundational risks: float arithmetic, HTMX partial swap gotchas, CSS-only tooltip accessibility, dark mode FOUC, comma input parsing, JSON import safety, and SVG chart dark mode colors. Those are resolved. This document covers only the new risk surface introduced by fixing code review defects in an existing, tested, working system.

---

## Critical Pitfalls

### Pitfall 1: Reworking Promo Penalty Math Without a Behavioral Specification

**What goes wrong:**
The code review found that `_build_promo_result()` constructs identical `not_paid_option` objects in both the `deferred_interest=True` and `deferred_interest=False` branches. The fix requires making these branches produce materially different financial outcomes. But the current codebase has no written specification for what "retroactive interest" means numerically (full principal at post-promo APR from month 1? Accrued interest on original principal added to remaining balance? Penalty APR applied to outstanding balance only?). The inline comment says "assume half the balance remains" but the code does not implement that either.

**Why it happens:**
Developers fixing a "both branches are identical" bug naturally focus on making them different. Without a locked-down business rule, they will invent plausible-sounding math that passes tests but does not match any real-world deferred-interest product. The result is a fix that is technically non-identical but financially incorrect in a different way.

**Consequences:**
- The app presents a specific dollar amount as the penalty cost for not paying on time -- users may make real financial decisions based on this number
- If the model is wrong, the recommendation may flip (promo wins when it should not, or vice versa)
- Tests written against the invented model will pass permanently, hiding the incorrectness

**Prevention:**
Before writing any code, write down the two business rules as plain-English sentences with a worked example:

1. **Forward-only interest (deferred_interest=False or retroactive_interest=False):** "After the promo term, the remaining balance accrues interest at post_promo_apr. Only the outstanding balance (not the original principal) is subject to interest." Worked example: $10,000 purchase, 12-month promo, $5,000 remaining at month 12, 24.99% APR on $5,000 for 12 months.

2. **Retroactive interest (deferred_interest=True AND retroactive_interest=True):** "All interest that would have accrued during the promo period at post_promo_apr is added to the balance retroactively. The full original principal accrues interest from month 1." Worked example: $10,000 at 24.99% for 12 months = ~$2,774 retroactive interest added to remaining balance.

Lock these in a code comment before implementing. Write the test expectations from the worked examples, not from whatever the code produces.

**Detection:**
- The two branches produce different `not_paid_on_time.true_total_cost` values
- Retroactive case costs more than forward-only case for same inputs
- Both cases cost more than the paid_on_time case

---

### Pitfall 2: Changing `cumulative_cost` Semantics Breaks Chart Tests That Assert on Raw Values

**What goes wrong:**
The line chart currently reads `MonthlyDataPoint.cumulative_cost`, which is populated as cumulative payments only. The fix changes it to include opportunity cost, tax savings, and inflation. But `test_charts.py` constructs `MonthlyDataPoint` objects with hand-picked `cumulative_cost` values and asserts that line chart endpoints match those values. Changing what `cumulative_cost` means without updating these test fixtures causes either: (a) tests fail and the developer weakens assertions to make them pass, or (b) the developer updates fixture values to match the new semantics but picks arbitrary numbers that do not validate the financial correctness.

**Why it happens:**
The chart tests were written to verify SVG rendering (paths, coordinates, scaling), not financial accuracy. They use synthetic data unconnected to the engine. When the metric changes, there is no single source of truth to derive the new expected values from.

**Consequences:**
- Chart tests pass with values that are internally consistent but financially meaningless
- The actual metric correctness is never tested end-to-end (engine produces data, chart renders it, assertion verifies the number matches the financial definition)
- A future regression in the engine's per-period calculation silently corrupts the chart

**Prevention:**
Two-layer testing strategy:

1. **Keep existing chart tests as rendering tests:** They verify SVG structure, path syntax, scaling, and edge cases (empty data, single option). These should use synthetic data and are not affected by the metric change. Do not change them.

2. **Add new integration tests that verify metric correctness:** Use the engine to produce a real `ComparisonResult`, extract the line chart data, and assert that the final data point equals `true_total_cost` (not `total_payments`). This is a 5-line test that catches the exact defect the code review found:
   ```python
   # The line chart endpoint value must equal true_total_cost, not total_payments
   assert chart_endpoint == option_result.true_total_cost
   ```

Do not modify `MonthlyDataPoint.cumulative_cost` semantics in-place. Instead, either add a new field (`cumulative_true_cost`) or compute the cumulative true cost in the chart data preparation layer (which already has access to all per-period factors). This avoids breaking any code that currently reads `cumulative_cost` expecting cumulative payments.

**Detection:**
- Line chart endpoint values differ from `true_total_cost` by more than rounding tolerance
- `cumulative_cost` in `MonthlyDataPoint` does not match cumulative payments (breaks detailed breakdown if that code path also reads it)

---

### Pitfall 3: Adding Validation Bounds That Reject Previously Accepted Input

**What goes wrong:**
The code review says inflation and tax rates need bounds. A developer adds `if val < 0 or val > 50` for inflation and `if val < 0 or val > 100` for tax. But the current default tax rate is `"22"` (as a string representing a percentage), and the form sends percentages as whole numbers (e.g., `"22"` for 22%). If the developer accidentally interprets the form value as a decimal rate (0.22) and sets bounds accordingly, or sets overly narrow bounds (e.g., inflation max 10%), users with previously working JSON exports cannot import them.

**Why it happens:**
The validation layer works with raw string percentages ("22" means 22%), but the domain layer converts to decimal rates (22/100 = 0.22). Bounds must be expressed in the same unit as the form input. The existing `validate_return_rate` validates against 0-30 (treating the custom input as a percentage), so inflation/tax bounds must follow the same convention. But this is not documented -- it is only visible by reading the existing code.

**Consequences:**
- Saved JSON exports with inflation_rate: "5" suddenly fail validation on import if bounds are wrong
- Users who had tax_rate: "37" (a valid US marginal rate) are rejected if max is set to 35
- The toggle-disable feature (inflation_enabled=False) still sends the field value -- validation must not reject disabled fields

**Prevention:**
- Copy the pattern from `validate_return_rate`: bounds expressed as percentage values matching what the form sends
- Inflation: 0-20% (covers any realistic scenario; US has never exceeded ~15% since 1980)
- Tax: 0-60% (covers the highest US marginal rate of 37% plus state taxes; international users may have higher)
- Test that disabled fields (inflation_enabled=False with inflation_rate="5") pass validation -- the toggle controls whether the value is used, not whether it is valid
- Test JSON import with edge-case values at the boundaries

**Detection:**
- Previously valid form submissions return validation errors
- JSON import of previously exported files fails
- Setting inflation_enabled=False still triggers inflation_rate validation errors

---

## Moderate Pitfalls

### Pitfall 4: HTMX Add/Remove Boundary Enforcement Returning Wrong HTTP Status

**What goes wrong:**
The code review says add-at-4 and remove-at-2 should be rejected. A common fix is to return HTTP 400 or 422 when the boundary is hit. But HTMX by default does not swap content from non-200 responses -- it fires `htmx:responseError` instead. The user clicks "Add Option" at 4 options and nothing happens. No error message, no feedback, no UI change. The button appears broken.

**Why it happens:**
Server-side developers think in terms of HTTP semantics (400 = bad request). HTMX thinks in terms of DOM swaps (200 = swap the content, anything else = error event). These two mental models collide at boundary enforcement.

**Consequences:**
- Buttons silently stop working at boundaries
- Users think the app is broken
- No visual feedback explaining why the action was not performed

**Prevention:**
Return HTTP 200 with the unchanged option list (do not add the 5th option, do not remove below 2). Optionally include a toast or inline message in the response HTML explaining the limit. The HTMX swap succeeds, the DOM updates (to the same content), and the user sees the limit message.

Alternatively, use `htmx:responseError` JavaScript to show a message, but this requires client-side JS that does not exist in the current codebase and is harder to test.

The simplest, most SSR-idiomatic approach: return the current option list unchanged with the button disabled or hidden when at the boundary. The server controls the button state -- if there are already 4 options, render the "Add" button as `disabled` or omit it entirely in the response.

**Detection:**
- Playwright test: click "Add" at 4 options, verify the button is disabled or a limit message appears
- Playwright test: click "Remove" at 2 options, verify the button is disabled or a limit message appears

---

### Pitfall 5: Centralizing `quantize_money` Breaks Import Paths Across 5+ Modules

**What goes wrong:**
Five modules each define their own `quantize_money(value: Decimal) -> Decimal` that rounds to 2 decimal places: `amortization.py`, `opportunity.py`, `inflation.py`, `tax.py`, `caveats.py`. The engine imports it from `amortization`. Moving all definitions to a shared `utils.py` or `money.py` module requires updating imports in every module, every test file that imports from these modules, and any test that mocks `quantize_money`.

**Why it happens:**
"Just move the function" seems trivial, but in Python, import paths are part of the public API surface. Test files may import `from fathom.amortization import quantize_money` directly. Any test that patches `fathom.opportunity.quantize_money` (using unittest.mock) will silently stop patching the actual function after the move, because the patch target string no longer matches the import path.

**Consequences:**
- Tests pass but are no longer patching the right function (mock is applied to a module that no longer defines the function)
- Circular imports if the new shared module imports from any of the modules that used to contain `quantize_money`
- `ty` and `pyrefly` may flag unused imports if old import paths are left as re-exports without explicit `__all__`

**Prevention:**
1. **Search first:** Before moving anything, `grep -r "quantize_money" tests/` and `grep -r "quantize_money" src/` to find every import path and every mock target
2. **Create the shared module with no dependencies:** The new `money.py` (or similar) must not import from `amortization`, `opportunity`, `inflation`, `tax`, or `caveats` -- it should only depend on `decimal.Decimal`
3. **Update all imports in one commit:** Do not leave any module importing its own local copy. Every `from fathom.X import quantize_money` becomes `from fathom.money import quantize_money`
4. **Verify no mocks target the old path:** Search for `patch("fathom.amortization.quantize_money")` or equivalent -- these must be updated to the new path
5. **Run all quality gates:** `ruff check`, `ty check`, `pyrefly check`, and the full test suite. Unused import violations will surface leftover references

**Detection:**
- `ruff check` flags unused imports in the old modules
- Tests that previously mocked `quantize_money` now pass but do not actually exercise the mock (coverage drop on the mocked code path)

---

### Pitfall 6: Toggle-Controlled Field Visibility Breaks HTMX Form Inclusion

**What goes wrong:**
The fix for toggle-controlled inflation/tax fields hides the input when the checkbox is unchecked. If the hiding is done with `display: none` or by not rendering the input in the server response, the field value is not included in the next HTMX `hx-include` submission. The server receives no `inflation_rate` field, falls back to the default ("3"), and this default overwrites whatever the user had previously entered. When they re-enable the toggle, their custom value is gone.

**Why it happens:**
HTMX's `hx-include` and standard HTML form submission both exclude inputs that are not in the DOM or are inside a `display: none` container (for HTMX specifically, disabled inputs are excluded). The toggle creates an asymmetry: hiding the field removes it from the next submission, but the user expects their value to persist.

**Consequences:**
- User enters 5% inflation, disables it, runs a comparison, re-enables it, and sees 3% (the default) instead of 5%
- The inflation/tax rate "forgets" its value every time the toggle is cycled

**Prevention:**
Two options, both work:

1. **CSS visibility only:** Use `visibility: hidden; height: 0; overflow: hidden` instead of `display: none` or DOM removal. The input remains in the DOM and is included in form submissions. This is the simplest approach.

2. **Hidden input mirror:** When the toggle is unchecked, keep a `<input type="hidden" name="inflation_rate" value="...">` that preserves the last-entered value. The visible input can be removed from the DOM. This is more complex but semantically cleaner.

Do NOT use HTMX to dynamically add/remove the fields from the server (like the option type switching does) -- that would require a server round-trip on every toggle click, adding latency to a purely cosmetic change.

**Detection:**
- Playwright test: enter custom inflation rate, uncheck toggle, submit, re-check toggle, verify value is preserved
- Check that form submission with toggle unchecked still includes the field in POST data

---

### Pitfall 7: Wiring `custom_label` Into Display Without Handling Label Collisions

**What goes wrong:**
The code review says `custom_label` is parsed but never used in results display. The fix wires it into `FinancingOption.label`. But `ComparisonResult.results` is a `dict[str, OptionResult | PromoResult]` keyed by label. If two options have the same `custom_label` (or a `custom_label` that matches another option's default label like "Traditional Loan"), one result silently overwrites the other. The user sees 3 options in the form but only 2 in the results.

**Why it happens:**
The dict key is the option label. Labels are not validated for uniqueness. Default labels are predictable ("Pay in Full", "Traditional Loan"), and custom labels are user-controlled. The collision is silent because Python dicts overwrite on duplicate keys.

**Consequences:**
- One option's result disappears entirely from the comparison
- The recommendation may be based on incomplete data (comparing 2 options when 3 were submitted)
- No error message -- the results just look wrong

**Prevention:**
- Validate label uniqueness in `build_domain_objects()` or `FormInput` validation. If two options have the same effective label, append a disambiguator (e.g., "Custom (2)")
- When `custom_label` is empty or whitespace, fall back to "Custom" (or the OptionType label), not to an empty string
- Add a test that submits two custom options with the same `custom_label` and verifies both appear in results

**Detection:**
- Number of results in `ComparisonResult.results` is less than the number of submitted options
- Results page shows fewer options than the form had

---

### Pitfall 8: Changing `cumulative_cost` Field Semantics Breaks the Detailed Breakdown Table

**What goes wrong:**
`results.py::_monthly_data_to_rows()` computes `cumulative_true_total_cost` independently from `MonthlyDataPoint.cumulative_cost`. It uses a running sum of `payment + opportunity_cost - tax_savings + inflation_adjustment`. But the line chart currently reads `cumulative_cost` from MonthlyDataPoint directly. If the fix for the line chart changes `cumulative_cost` to mean "cumulative true cost" (by changing how the engine populates it), then `_monthly_data_to_rows()` is now computing the same metric from the same per-period factors -- and any rounding difference between the engine's running sum and the results module's running sum will cause the chart endpoint and the detailed breakdown final row to differ by a few cents.

**Why it happens:**
Two independent running sums over Decimal values with `quantize_money()` applied at different points in the computation will diverge due to rounding. `quantize_money` rounds each intermediate value to 2 decimal places. Rounding `A + B` is not the same as `round(A) + round(B)` over 36+ months.

**Consequences:**
- The line chart endpoint and the detailed breakdown table's final cumulative value differ by $0.01-$0.05
- This is cosmetically embarrassing but not financially material
- It may trigger test failures if assertions use exact equality

**Prevention:**
Do not change the semantics of `MonthlyDataPoint.cumulative_cost`. Instead, compute the cumulative true cost in the chart preparation layer:

```python
# In charts.py _collect_option_points(), replace:
points = [(dp.month, _to_float(dp.cumulative_cost)) for dp in monthly_data]
# With a running sum using the same formula as _monthly_data_to_rows():
cumulative = 0.0
points = []
for dp in monthly_data:
    net = float(dp.payment + dp.opportunity_cost - dp.tax_savings + dp.inflation_adjustment)
    cumulative += net
    points.append((dp.month, cumulative))
```

This ensures the chart and the detailed breakdown use the exact same computation, and `cumulative_cost` on MonthlyDataPoint remains "cumulative payments" for any other consumer.

Alternatively, add a `cumulative_true_cost` field to MonthlyDataPoint and populate it in the engine alongside `cumulative_cost`. This is the cleanest long-term solution but requires updating the frozen Pydantic model.

**Detection:**
- Chart endpoint value and detailed breakdown final cumulative value match to the cent
- `cumulative_cost` consumers outside of the chart (if any) are not broken

---

## Minor Pitfalls

### Pitfall 9: Custom Option Validation Decision Creates a UI/Server Divergence

**What goes wrong:**
The code review says the custom option template shows "Upfront Cash Required" as a first-class field, but validation does not require it. The fix requires a product decision: make it required or change the UI copy to say "optional." If the developer makes it required without also making the UI show a validation error next to the field, the user sees a generic error but does not know which field caused it.

**Prevention:**
- If making it required: add `down_payment` to the custom option's validation in `_validate_by_type()` and verify the error key maps to the correct field location in the template (`options.{idx}.down_payment`)
- If making it optional: change the template label from "Upfront Cash Required" to "Upfront Cash (optional)" and ensure the engine handles `down_payment=None` for custom options (it already does -- `_build_loan_result` defaults to `Decimal(0)`)

---

### Pitfall 10: Test Backfill That Only Asserts the Fix, Not the Invariant

**What goes wrong:**
When backfilling tests for fixed defects, developers write tests that verify "the new code does X" rather than "the system invariant is Y." For example, testing that deferred_interest=True produces a different `not_paid_on_time` result than deferred_interest=False. This test passes today but does not enforce that the deferred-interest result is more expensive than the forward-only result -- which is the actual business invariant.

**Prevention:**
For each fixed defect, write tests at two levels:

1. **Behavioral:** The flag changes the output (different values)
2. **Invariant:** The relationship between values is correct (retroactive > forward-only > paid_on_time)

Invariant tests survive future refactors. Behavioral tests only survive until the next time someone changes the numbers.

---

### Pitfall 11: Frozen Pydantic Models Resist Field Addition

**What goes wrong:**
`MonthlyDataPoint`, `OptionResult`, `PromoResult`, and `ComparisonResult` all use `model_config = ConfigDict(frozen=True)`. Adding a new field (like `cumulative_true_cost` or `custom_label` on the result) requires either making the field optional with a default or updating every constructor call site. Forgetting to add a default causes `ValidationError` at every existing construction point.

**Prevention:**
- Any new field on a frozen model must have a default value: `new_field: Decimal = Field(default_factory=lambda: Decimal(0))`
- Search for all construction sites before adding: `grep -r "MonthlyDataPoint(" src/ tests/` to find every place that creates the object
- Add the field with a default first, verify all tests pass, then populate it in the engine

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Promo penalty fix (engine.py) | Inventing financial math without a spec | Write the business rule and worked example before coding; test against the example |
| Validation bounds (forms.py) | Bounds expressed in wrong unit (decimal vs percentage) | Follow existing `validate_return_rate` pattern; bounds in percentage units matching form input |
| Validation bounds (forms.py) | Rejecting disabled fields | Test that `inflation_enabled=False` with any `inflation_rate` value passes validation |
| Line chart metric (charts.py) | Dual running-sum rounding divergence | Compute cumulative true cost in chart prep layer, not by changing MonthlyDataPoint.cumulative_cost |
| HTMX boundaries (routes.py) | Non-200 response status prevents HTMX swap | Return 200 with unchanged content and disabled button, not 4xx |
| Custom option validation (forms.py) | Required field without corresponding template error display | Verify error key mapping renders next to the field |
| custom_label wiring (forms.py, routes.py, results.py) | Label collision in results dict | Validate label uniqueness or auto-disambiguate |
| Toggle visibility (templates) | Hidden fields excluded from HTMX form submission | Use CSS visibility, not display:none or DOM removal |
| Centralize quantize_money | Circular imports or broken mock patches | New module depends only on Decimal; update all import paths and mock targets |
| Test backfill | Tests assert current behavior, not business invariants | Write invariant assertions (retroactive > forward > paid_on_time) |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Engine change + chart change | Changing `cumulative_cost` meaning in MonthlyDataPoint affects both chart and detailed breakdown | Keep `cumulative_cost` as cumulative payments; compute cumulative true cost separately in each consumer |
| Validation change + JSON import | New bounds reject previously valid exported JSON files | Test import of pre-v1.2 export files against new validation |
| HTMX boundary enforcement + button state | Returning error status that HTMX does not swap | Return 200 with the button state reflecting the boundary |
| Toggle visibility + form repopulation | Hidden field values lost across HTMX round-trips | CSS-only hiding preserves form values; DOM removal does not |
| Label wiring + results dict | User-controlled labels can collide with default labels | Enforce uniqueness before using as dict key |
| Utility centralization + mock patching | Mock targets `fathom.amortization.quantize_money` no longer exist | Search all test files for mock targets referencing the old paths |

---

## "Looks Done But Isn't" Checklist

- [ ] **Promo penalty:** deferred_interest=True AND retroactive_interest=True produces strictly higher `not_paid_on_time.true_total_cost` than deferred_interest=False
- [ ] **Promo penalty:** Both branches produce costs higher than `paid_on_time.true_total_cost`
- [ ] **Promo penalty:** Worked example with known dollar amounts matches hand-calculated expectation
- [ ] **Line chart metric:** Chart endpoint value for each option equals `true_total_cost` (not `total_payments`)
- [ ] **Line chart metric:** Detailed breakdown table final cumulative matches chart endpoint to the cent
- [ ] **Validation bounds:** Inflation rate of -1% rejected; inflation rate of 0% accepted; inflation rate of 20% accepted; inflation rate of 21% rejected (or whatever bound is chosen)
- [ ] **Validation bounds:** Tax rate of -1% rejected; tax rate of 0% accepted; tax rate of 60% accepted; tax rate of 61% rejected
- [ ] **Validation bounds:** `inflation_enabled=False` with `inflation_rate=-5` does NOT produce a validation error (toggle disabled = field unused)
- [ ] **HTMX add/remove:** Adding at 4 options returns 200 with 4 options (not 5) and "Add" button disabled or absent
- [ ] **HTMX add/remove:** Removing at 2 options returns 200 with 2 options (not 1) and "Remove" button disabled or absent
- [ ] **Custom label:** Two custom options with label "My Option" both appear in results (no collision)
- [ ] **Custom label:** Empty custom_label falls back to a sensible default, not empty string
- [ ] **Toggle visibility:** Enter 5% inflation, uncheck toggle, submit, re-check toggle -- field shows 5%, not 3%
- [ ] **quantize_money centralization:** `grep -r "def quantize_money" src/` returns exactly 1 result
- [ ] **quantize_money centralization:** `grep -r "quantize_money" tests/` shows all mock targets use the new path
- [ ] **All quality gates pass:** `ruff check .`, `ruff format --check .`, `ty check`, `pyrefly check`, full test suite

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Wrong promo penalty math | MEDIUM | Correct the business rule; update engine + tests; re-verify hand-calculated example |
| Chart/breakdown cumulative divergence | LOW | Move computation to chart layer; leave MonthlyDataPoint unchanged |
| Validation rejecting valid input | LOW | Widen bounds; add boundary tests; re-test JSON import |
| HTMX boundary returning 4xx | LOW | Change to 200 + disabled button; add Playwright test |
| Label collision | LOW | Add uniqueness check in build_domain_objects; disambiguate |
| Toggle losing field values | LOW | Switch from display:none to CSS visibility:hidden |
| Broken mock targets after centralization | LOW | Search-and-replace mock target strings; re-run tests |
| Frozen model field addition error | LOW | Add default value to new field; re-run all tests |

---

## Sources

- Direct code inspection of `/home/kris/git/fathom/src/fathom/engine.py`, `forms.py`, `charts.py`, `results.py`, `models.py`, `routes.py`
- Direct code inspection of `/home/kris/git/fathom/tests/test_engine.py`, `test_charts.py`
- Code review findings: `/home/kris/git/fathom/docs/code-review-2026-03-15.md`
- HTMX docs: Response handling for non-200 status codes (htmx.org/docs)
- Pydantic docs: frozen model behavior with ConfigDict
- Python decimal module: Rounding behavior of quantize operations
- Flask/Werkzeug: Form data handling for hidden vs display:none inputs

---
*Pitfalls research for: Fathom v1.2 -- code review defect fixes*
*Researched: 2026-03-15*
