# Fathom Code Review Findings

Date: 2026-03-15
Reviewer: GitHub Copilot (GPT-5.4)
Scope: Backend logic, validation, routes, results rendering, charting, UI contract alignment, and test coverage.

Audit status: This document captures all confirmed findings from the completed review passes. A full end-to-end WCAG/browser audit was not completed in this pass, so absence of accessibility findings here should not be interpreted as a clean accessibility bill of health.

## Review Standard

This review was done as a production-readiness review, not a style pass. Findings are prioritized toward:

- Incorrect financial modeling
- Product-contract mismatches
- User-visible behavioral defects
- Validation gaps that can distort recommendations
- Test coverage gaps that allow defects to ship undetected

## Baseline Verified

The current baseline is clean on static quality gates:

- `uv run ruff check .` passed
- `uv run ruff format --check .` passed
- `uv run ty check` passed
- `uv run pyrefly check` passed
- `uv run pytest tests/test_engine.py tests/test_edge_cases.py tests/test_routes.py -q` passed (`71 passed`)

This matters because the findings below are not lint or typing cleanup. They are logic, behavior, product-fit, and test-coverage issues.

## Confirmed Findings

### 1. Promo penalty modeling ignores deferred-interest settings

Severity: High

Files:

- `src/fathom/engine.py`

What is wrong:

- `_build_promo_result()` builds the same `not_paid_on_time` fallback loan whether `deferred_interest` and `retroactive_interest` are enabled or not.
- The code branches on those flags, but both branches construct the same `FinancingOption`.

Why it matters:

- The PRD distinguishes standard `0% promotional financing` from cases with a deferred-interest clause.
- Right now the warning state can change while the modeled penalty cost does not change.
- That means the app can present materially different legal/financial scenarios as if they cost the same.

Evidence:

- Code inspection of `_build_promo_result()` shows both branches create the same `not_paid_option`.
- Direct runtime reproduction:

```text
paid_on_time_equal True
not_paid_on_time_equal True
not_paid_a 14106.15
not_paid_b 14106.15
```

The above compared two otherwise identical promo options with opposite deferred-interest settings.

Additional concern:

- The inline comment says the model assumes half the balance remains after the promo term, but the implementation does not do that. The code/comment mismatch makes the intended model unclear.

Recommended fix direction:

- Rework `_build_promo_result()` so deferred-interest and forward-interest scenarios are actually modeled differently.
- Align the implementation and comments with one explicit business rule.
- Add tests that prove the flags change the resulting penalty path.

### 2. Global inflation and tax settings accept impossible values

Severity: High

Files:

- `src/fathom/forms.py`
- `src/fathom/models.py`

What is wrong:

- `SettingsInput` validates only the return rate.
- `inflation_rate` and `tax_rate` are accepted without meaningful bounds.
- `build_domain_objects()` converts them directly into `GlobalSettings`.

Why it matters:

- These settings directly affect recommendation outputs.
- Negative inflation and tax rates above `100%` can generate mathematically valid but product-invalid outputs.
- That can make the recommendation engine look credible while using impossible assumptions.

Evidence:

Direct runtime reproduction:

```text
inflation_rate -0.05
tax_rate 1.5
```

This was produced from form input of `-5%` inflation and `150%` tax rate.

Recommended fix direction:

- Validate inflation and tax rates in `SettingsInput`.
- Define product-appropriate bounds and reflect them in both server validation and UI hints.
- Add tests for negative values, blank-enabled states, and rates above maximum.

### 3. HTMX add/remove endpoints violate the 2-4 option contract server-side

Severity: Medium

Files:

- `src/fathom/routes.py`

What is wrong:

- `/partials/option/add` will render a fifth option if called while four options already exist.
- `/partials/option/<idx>/remove` will render a one-option form if called while only two exist.

Why it matters:

- The PRD and form validation both define comparison as `2-4` options.
- The dynamic UI layer can enter invalid intermediate states before final submission.
- That makes the app inconsistent and creates confusing UX around why the final compare may fail.

Evidence:

Direct runtime reproduction:

```text
add_status 200
contains_option_4 True
remove_status 200
contains_option_0 True
contains_option_1 False
```

Recommended fix direction:

- Enforce the same option-count boundaries inside the HTMX add/remove endpoints.
- Return the unchanged form state or a validation message when a boundary action is invalid.
- Add route tests for add-at-max and remove-at-min server-side behavior.

### 4. Custom-option validation does not match the UI contract for upfront cash

Severity: Medium

Files:

- `src/fathom/forms.py`
- `src/fathom/templates/partials/option_fields/custom.html`

What is wrong:

- The custom-option template presents `Upfront Cash Required` as a first-class field.
- Validation does not require it for custom options.

Why it matters:

- The UI tells users this field matters for the financing arrangement.
- The engine will accept a custom option without it, which means the product contract is ambiguous and the UI is misleading.

Evidence:

Direct runtime reproduction:

```text
parsed_ok True
down_payment_raw ''
```

This was for a custom option with APR and term but no upfront-cash value.

Recommended fix direction:

- Decide whether custom options require upfront cash.
- If yes, enforce it in validation.
- If no, change the UI copy so it is clearly optional.

### 5. The optional custom description field is collected but never used

Severity: Low

Files:

- `src/fathom/templates/partials/option_fields/custom.html`
- `src/fathom/forms.py`
- `src/fathom/routes.py`

What is wrong:

- `custom_label` is rendered and parsed.
- It is not carried into `FinancingOption` or used in results rendering.

Why it matters:

- This is dead product surface area.
- Users can enter information that appears meaningful but has no effect anywhere.

Evidence:

- Search shows `custom_label` only in parsing/template plumbing, not in domain output or display logic.

Recommended fix direction:

- Either wire `custom_label` into display/output semantics or remove the field.

### 6. The line chart plots cumulative payments, not cumulative true cost

Severity: High

Files:

- `src/fathom/engine.py`
- `src/fathom/charts.py`
- `src/fathom/results.py`

What is wrong:

- `prepare_line_chart()` uses `MonthlyDataPoint.cumulative_cost`.
- In the engine builders, `cumulative_cost` is populated as cumulative payments only.
- It does not include opportunity cost, tax savings, or inflation adjustment.
- Meanwhile `results.py` separately computes `cumulative_true_total_cost` correctly for detailed breakdown tables.

Why it matters:

- The PRD defines the line chart as `Cumulative Cost Over Time` and explicitly ties it to breakeven insight.
- If the chart omits opportunity cost, tax, and inflation effects, it is not charting the same metric users are told they are comparing.
- This is a user-visible data integrity issue, not just a labeling issue.

Evidence:

Direct runtime reproduction:

```text
Loan true_total_cost 29733.98 chart_end 26,904 monthly_cumulative 26903.82
Cash true_total_cost 30885.48 chart_end 25,000 monthly_cumulative 25000
```

The chart endpoint values line up with payment accumulation rather than `true_total_cost`.

Recommended fix direction:

- Define the chart metric explicitly.
- If the intended metric is cumulative true cost, derive the line series from the same per-period net calculation used by `_monthly_data_to_rows()`.
- Add tests that compare line-chart endpoints to the intended metric.

### 7. The UI does not implement live result updates as described in the PRD

Severity: Medium

Files:

- `src/fathom/templates/index.html`
- `src/fathom/templates/partials/option_card.html`

What is wrong:

- The compare form uses `hx-post="/compare"`, but no `hx-trigger` is attached for input-driven recalculation.
- The page updates when the form is submitted, not as the user types.

Why it matters:

- The PRD says results update live as the user types, with a visible Calculate button as a fallback.
- The current implementation provides the fallback button but not the live-update behavior.

Evidence:

- No `hx-trigger` or equivalent input-driven update mechanism exists in the form templates.
- The current behavior is submit-driven HTMX replacement.

Recommended fix direction:

- Add debounced live-update triggers for relevant input changes while preserving the submit button fallback.
- Cover live-update behavior with browser automation.

### 8. Inflation and tax fields are always visible instead of being toggle-controlled

Severity: Low

Files:

- `src/fathom/templates/partials/global_settings.html`

What is wrong:

- `Inflation Rate` and `Marginal Tax Rate` inputs are always rendered.
- The PRD says they should be shown only when their corresponding toggles are enabled.

Why it matters:

- This is a product-contract mismatch.
- It adds visual complexity and weakens the intended progressive disclosure of optional assumptions.

Evidence:

- The template unconditionally renders both inputs with no conditional display logic tied to the checkboxes.

Recommended fix direction:

- Hide and show these controls based on their toggles.
- Add browser tests for toggle behavior.

## Design And Maintainability Risks

These are not all confirmed end-user bugs yet, but they are concrete risks that should be addressed or at least reviewed carefully.

### 9. Winner ranking for promo options always uses the optimistic paid-on-time path

Severity: Medium

Files:

- `src/fathom/results.py`

What is happening:

- `_get_effective_cost()` always ranks `PromoResult` using `paid_on_time.true_total_cost`.

Why this is risky:

- A risky promo can win the headline recommendation based only on the disciplined scenario.
- The caveat is shown, but the ranking itself does not reflect any risk weighting or alternate recommendation mode.

Why it should be reviewed:

- This may be product-intent, but if so it should be explicit.
- If not explicit, the UI may over-recommend risky promotions.

Recommended review question:

- Should promo options be ranked on optimistic cost only, or should the UI communicate both the winner and the conditionality more aggressively?

### 10. Core monetary rounding helpers are duplicated across modules

Severity: Low

Files:

- `src/fathom/amortization.py`
- `src/fathom/opportunity.py`
- `src/fathom/inflation.py`
- `src/fathom/tax.py`
- `src/fathom/caveats.py`

What is happening:

- Each module defines its own `quantize_money()` helper.

Why this is risky:

- If rounding rules ever need to change, these helpers can drift.
- Shared finance rules should usually live in one place.

Recommended fix direction:

- Centralize shared monetary rounding utilities.

## Test Coverage Findings

### 11. Existing tests do not detect the promo-modeling defect

Severity: High

Files:

- `tests/test_engine.py`

What is missing:

- Tests assert that promo results exist and contain positive values.
- They do not assert that deferred-interest-related flags materially affect `not_paid_on_time` results.

Impact:

- A major modeling defect passed the current engine suite.

### 12. Existing chart tests verify SVG structure, not metric correctness

Severity: High

Files:

- `tests/test_charts.py`
- `tests/test_results_display.py`

What is missing:

- The tests supply arbitrary `cumulative_cost` values and verify that lines render.
- They do not assert that chart data corresponds to the intended financial metric.

Impact:

- A user-visible data-integrity defect in the line chart can pass all current chart tests.

### 13. HTMX boundary behavior is not tested at the actual min/max constraints

Severity: Medium

Files:

- `tests/test_routes.py`

What is missing:

- There is no assertion that add-at-4 is rejected or that remove-at-2 is rejected.

Impact:

- Server-side route behavior can violate the product constraints even while route tests stay green.

### 14. Global settings validation tests focus on return rate only

Severity: Medium

Files:

- `tests/test_forms.py`

What is missing:

- No negative inflation tests.
- No excessively large tax-rate tests.
- No explicit bounds tests for those settings.

Impact:

- The engine can be fed impossible settings without any test failure.

### 15. Browser verification exists but is not part of the automated test suite

Severity: Low

Files:

- `tests/playwright_verify.py`

What is happening:

- The file explicitly states it is not a pytest test and runs standalone.

Why this matters:

- Important browser checks may be skipped in normal CI or developer workflows.
- That weakens confidence in HTMX, responsive, and accessibility behaviors.

Recommended fix direction:

- Either integrate these checks into automated test workflows or clearly define when they must be run.

## Summary For The Junior Developer

The highest-priority work is:

1. Fix promo penalty modeling so deferred-interest settings actually change the calculation path.
2. Add server-side validation bounds for inflation and tax rates.
3. Correct the line chart so it plots the intended metric.
4. Enforce the 2-4 option contract in the HTMX add/remove endpoints.
5. Reconcile custom-option UI requirements with actual validation and output behavior.

After that, clean up the product-contract mismatches around live updates and toggle-controlled settings visibility, then backfill the missing tests so these regressions cannot pass quietly again.

## Suggested Implementation Order

1. `src/fathom/engine.py`
2. `src/fathom/forms.py`
3. `src/fathom/charts.py` and related metric plumbing
4. `src/fathom/routes.py`
5. `src/fathom/templates/partials/option_fields/custom.html`
6. `src/fathom/templates/index.html`
7. `src/fathom/templates/partials/global_settings.html`
8. Test backfill in `tests/test_engine.py`, `tests/test_forms.py`, `tests/test_routes.py`, `tests/test_charts.py`, and browser coverage
