# Technology Stack

**Project:** Fathom -- Financing Options Analyzer
**Researched:** 2026-03-10 (v1.0) / 2026-03-13 (v1.1 additions) / 2026-03-15 (v1.2 code review fixes)
**Overall confidence:** HIGH

---

## v1.2 Code Review Fixes (NEW -- researched 2026-03-15)

This section documents stack implications for fixing all confirmed defects from the
2026-03-15 code review. The existing v1.0/v1.1 stack below is unchanged.

### Key Finding: No New Dependencies Required

All nine code review fixes are implementable with the existing stack. No new Python
packages, no new JS files, no new CSS frameworks. Every fix is a logic correction,
validation addition, refactoring, or test backfill using tools already in the project.

---

### Fix 1: Deferred-Interest Promo Penalty Modeling (Finding #1, HIGH severity)

**Decision: Pure Python logic fix in `engine.py`. No new dependencies.**

The bug: both branches of the `deferred_interest`/`retroactive_interest` conditional
in `_build_promo_result()` construct identical `FinancingOption` objects, producing
identical penalty costs regardless of the flags.

The fix requires two distinct penalty calculation paths:

| Scenario | What should happen | Current behavior |
|----------|-------------------|------------------|
| Retroactive interest (`deferred_interest=True`, `retroactive_interest=True`) | Interest accrues on full original principal from month 1 at `post_promo_apr`. Total penalty includes back-interest for the entire promo period. | Same as forward-only |
| Forward-only interest (`deferred_interest=True`, `retroactive_interest=False`) | Only the remaining unpaid balance (after promo minimum payments) is amortized at `post_promo_apr`. No back-interest. | Same as retroactive |
| No deferred interest (`deferred_interest=False`) | Remaining balance amortized at `post_promo_apr` with no special penalty. | Identical to both above |

Implementation approach:
1. Calculate the actual remaining balance after promo-period minimum payments (use existing `amortization.py` functions at 0% APR over the promo term).
2. **Retroactive path:** Compute back-interest on full principal for the promo term months at `post_promo_apr`, then amortize the full remaining balance at `post_promo_apr`.
3. **Forward-only path:** Amortize only the remaining balance at `post_promo_apr` (no back-interest component).
4. Fix the misleading comment about "half the balance" -- the model should use the calculated remaining balance.

**Stack needed:** `Decimal` arithmetic + `amortization.py` (both already available).

**Confidence:** HIGH -- verified by code inspection of `_build_promo_result()` lines 279-357 in `engine.py`.

---

### Fix 2: Server-Side Validation Bounds for Inflation/Tax (Finding #2, HIGH severity)

**Decision: Add Pydantic validators to existing `SettingsInput` model. No new dependencies.**

The existing `SettingsInput.validate_return_rate` model validator already establishes
the validation pattern (0-30% bounds with `field_name:` prefixed error messages). Apply
the identical pattern for inflation and tax rates.

Recommended bounds:

| Field | Min | Max | Rationale |
|-------|-----|-----|-----------|
| `inflation_rate` | 0% | 20% | US CPI has never exceeded ~15% (1980 peak ~14.8%). 20% is generous. Negative inflation (deflation) is product-invalid -- it would make financing look artificially cheaper. |
| `tax_rate` | 0% | 50% | Top US federal marginal rate is 37%. Combined state+federal+local can reach ~50% in high-tax jurisdictions (CA, NYC). |

Implementation: extend the existing `validate_return_rate` model validator (or add a
second `model_validator`) to check `inflation_rate` and `tax_rate` when their
corresponding `_enabled` flags are true.

Important Pydantic pattern to follow (already established in codebase):
- Use `model_validator(mode="after")` with `Self` return type
- Prefix error messages with `field_name:` so `pydantic_errors_to_dict()` remaps correctly
- Keep raw string inputs; validate via `_try_decimal()` before bounds check

**Stack needed:** Pydantic 2.12.5 `model_validator` (already used). No new libraries.

**Confidence:** HIGH -- verified by code inspection of existing validation patterns in `forms.py`.

---

### Fix 3: Cumulative True Cost Line Chart (Finding #6, HIGH severity)

**Decision: Fix metric derivation in engine builders. No new dependencies.**

The `MonthlyDataPoint.cumulative_cost` field is populated with cumulative payments only.
The line chart (`charts.py:prepare_line_chart()`) reads this field directly at line 185.
Meanwhile, `results.py:_monthly_data_to_rows()` correctly computes cumulative true cost
by including opportunity cost, tax savings, and inflation adjustment.

Recommended approach: **Compute cumulative true cost in `charts.py`** from the per-period
fields already available on `MonthlyDataPoint`:

```
cumulative_true_cost[month] = cumulative_cost[month]
    + sum(opportunity_cost[1..month])
    - sum(tax_savings[1..month])
    + sum(inflation_adjustment[1..month])
```

Why compute in `charts.py` rather than changing `cumulative_cost` semantics:
- `cumulative_cost` may be consumed by other display code expecting cumulative payments
- Changing its meaning risks breaking the detailed breakdown table
- Computing the derived metric at the chart boundary is safer and more explicit

**Stack needed:** `Decimal` arithmetic (stdlib). No new libraries.

**Confidence:** HIGH -- verified by code inspection of `charts.py` line 185 and `MonthlyDataPoint` fields.

---

### Fix 4: HTMX Add/Remove Boundary Enforcement (Finding #3, MEDIUM severity)

**Decision: Add guard clauses in `routes.py`. No new dependencies.**

The `add_option()` and `remove_option()` route handlers need boundary checks:

```python
# In add_option(): reject if at max
if len(parsed["options"]) >= 4:
    # Return current state unchanged -- HTMX swaps identical content (no-op)
    return render_template("partials/option_list.html", ...)

# In remove_option(): reject if at min
if len(parsed["options"]) <= 2:
    return render_template("partials/option_list.html", ...)
```

HTMX pattern: return 200 with unchanged HTML. HTMX swaps the response into the target,
which is a visual no-op. Do not return 4xx -- HTMX treats non-2xx as errors and may
trigger `htmx:responseError`, which would require custom error handling JS.

Additionally, the add/remove buttons should be conditionally disabled in the template
based on current option count. This is a defense-in-depth measure (server enforces
boundaries; UI communicates them).

**Stack needed:** Flask route handlers (already available). No new libraries.

**Confidence:** HIGH -- verified by code inspection of `routes.py` lines 210-312.

---

### Fix 5: Toggle-Controlled Inflation/Tax Field Visibility (Finding #8, LOW severity)

**Decision: Pure CSS with `:has()` selector. No new dependencies, no new HTMX endpoints.**

The inflation rate and tax rate input fields should be visible only when their
corresponding toggle checkboxes are checked.

Implementation using CSS `:has()`:

```css
fieldset:has(input[name="inflation_enabled"]:not(:checked)) .inflation-fields {
    display: none;
}
fieldset:has(input[name="tax_enabled"]:not(:checked)) .tax-fields {
    display: none;
}
```

Requires wrapping the rate input + label in a container element with the appropriate
class (`.inflation-fields`, `.tax-fields`).

CSS `:has()` browser support: Baseline Widely Available since Dec 2023. Chrome 105+,
Firefox 121+, Safari 15.4+. This covers all browsers that Pico CSS 2.1.1 supports.

Add a `@supports` fallback that keeps fields always visible for any browser lacking
`:has()` -- graceful degradation rather than broken state.

**Why not HTMX:** A server round-trip to show/hide a field is wasteful (adds latency,
server load, and endpoint complexity for a pure presentation concern).

**Why not Alpine.js/Stimulus:** Adding a JS framework for a 3-line CSS feature
contradicts the "minimal client-side JS" principle.

**Stack needed:** CSS (already available). No new libraries.

**Confidence:** HIGH -- CSS `:has()` support verified via caniuse.com baseline data.

---

### Fix 6: Centralize Monetary Rounding (Finding #10, LOW severity)

**Decision: Extract `quantize_money` to `src/fathom/money.py`. No new dependencies.**

Five modules define identical `quantize_money()` functions:

| Module | Lines |
|--------|-------|
| `amortization.py` | `CENTS = Decimal("0.01")` + 2-line function |
| `opportunity.py` | identical copy |
| `inflation.py` | identical copy |
| `tax.py` | identical copy |
| `caveats.py` | identical copy |

Create `src/fathom/money.py` containing:

```python
from decimal import Decimal

CENTS = Decimal("0.01")

def quantize_money(value: Decimal) -> Decimal:
    """Round a Decimal value to the nearest cent (two decimal places)."""
    return value.quantize(CENTS)
```

Update all five modules to `from fathom.money import quantize_money`. Remove the
local definitions and `CENTS` constants.

This follows the existing module-per-concern pattern (`amortization.py`, `opportunity.py`,
`inflation.py`, `tax.py`). A shared monetary utility module is the natural home.

**Stack needed:** Decimal (stdlib). No new libraries.

**Confidence:** HIGH -- verified by grep showing 5 identical definitions.

---

### Fix 7: Custom Option Validation + custom_label Wiring (Findings #4 + #5)

**Decision: Pydantic model update + template changes. No new dependencies.**

Two changes:

1. **Add `custom_label` to `FinancingOption` domain model** as `custom_label: str | None = None`.
   Wire through `build_domain_objects()` in `forms.py`. Use in results templates where
   the option label is displayed (fall back to `label` if `custom_label` is empty).

2. **Custom option `down_payment` validation.** The UI presents "Upfront Cash Required"
   as a field but validation does not require it. Recommendation: keep it optional with
   default 0 (matching behavior of other non-cash types like `TRADITIONAL_LOAN`). The
   field is already handled by `_validate_down_payment()` when provided. No validation
   change needed -- just ensure the template copy says "optional" or "(if any)".

**Stack needed:** Pydantic BaseModel (already available). No new libraries.

**Confidence:** HIGH -- verified by code inspection.

---

### Fix 8: Test Coverage Backfill (Findings #11-15)

**Decision: pytest test cases using existing patterns. No new dependencies.**

Tests to add, organized by file:

| Test File | Tests Needed | Pattern Source |
|-----------|-------------|----------------|
| `test_engine.py` | Promo with `deferred_interest=True/False` produces different `not_paid_on_time` costs | Existing promo tests in same file |
| `test_forms.py` | Negative inflation, inflation >20%, tax >50%, tax=0% | Existing `validate_return_rate` tests |
| `test_routes.py` | `add_option` at 4 returns unchanged 4 options; `remove_option` at 2 returns unchanged 2 options | Existing add/remove route tests |
| `test_charts.py` | Line chart endpoint values match cumulative true cost, not cumulative payments | Existing chart structure tests |

The existing test infrastructure (pytest + Flask test client + conftest fixtures) is
sufficient. No new test libraries needed.

**Stack needed:** pytest 9.0.2 (already available). No new libraries.

**Confidence:** HIGH -- verified by reviewing existing test patterns.

---

### v1.2 Summary: Zero Dependency Changes

| Fix | New Python Deps | New JS | New CSS | New Files |
|-----|----------------|--------|---------|-----------|
| Promo penalty modeling | None | None | None | None |
| Validation bounds | None | None | None | None |
| Line chart metric | None | None | None | None |
| HTMX boundary enforcement | None | None | None | None |
| Toggle visibility | None | None | ~6 lines | None |
| Centralize rounding | None | None | None | `src/fathom/money.py` |
| Custom option wiring | None | None | None | None |
| Test backfill | None | None | None | None |

No changes to `pyproject.toml`. No `uv add` commands needed.

---

### v1.2 Alternatives Rejected

| Need | Considered | Why Rejected |
|------|-----------|--------------|
| Deferred-interest modeling | numpy-financial | Overkill; existing `amortization.py` handles all needed loan math in Decimal |
| Validation bounds | cerberus, marshmallow | Pydantic already handles validation with established patterns |
| Toggle visibility | Alpine.js, Stimulus | CSS `:has()` solves this in 3 lines; no JS framework needed |
| Toggle visibility | New HTMX endpoint | Server round-trip for show/hide is wasteful |
| Rounding centralization | py-moneyed | Would require rewriting all Decimal arithmetic; massive scope creep |
| Test coverage | pytest-cov | Coverage reporting is useful but orthogonal to writing the actual tests |
| Financial modeling | QuantLib Python | Nuclear option for simple amortization + interest accrual |

### v1.2 What NOT to Add

| Avoid | Why |
|-------|-----|
| Any new Python dependency | Every fix uses existing stdlib + installed packages |
| Alpine.js or any JS framework | CSS handles toggle visibility; no interactive JS needed |
| numpy-financial | Simple Decimal amortization math is already implemented |
| New HTMX endpoints for visibility | Pure presentation concern; CSS is faster and simpler |
| pytest-cov | Out of scope for defect fixes; add separately if desired |

---

## v1.1 Feature Additions (researched 2026-03-13)

This section documents only what is NEW for v1.1. The existing v1.0 stack below
is unchanged and already validated.

### Key Finding: No New Dependencies Required

All seven v1.1 features are implementable with the existing stack. No new Python
packages, no new vendored JS files, no new CSS frameworks.

---

### Feature: Dark Mode (`prefers-color-scheme`)

**Decision: Remove `data-theme="light"` from `<html>` -- zero new dependencies.**

Pico CSS 2.1.1 already implements dark mode via the selector
`:root:not([data-theme])` inside `@media (prefers-color-scheme: dark)`. The
current `base.html` hardcodes `data-theme="light"`, which suppresses this
built-in behavior entirely. Removing that single attribute enables automatic
dark mode with no JS, no new library, no build step.

Work required:
1. Remove `data-theme="light"` from `<html>` in `base.html`.
2. Audit and fix hardcoded hex colors in `style.css` that bypass Pico's CSS
   variable system. The caveats section uses light-mode-only hex values that
   must get `@media (prefers-color-scheme: dark)` overrides:

| Selector | Hardcoded Value | Fix |
|----------|-----------------|-----|
| `.caveat-warning` background | `#fef3c7` | Add dark override: `#451a03` |
| `.caveat-warning` color | `#92400e` | Add dark override: `#fde68a` |
| `.caveat-critical` background | `#fee2e2` | Add dark override: `#450a0a` |
| `.caveat-critical` color | `#991b1b` | Add dark override: `#fecaca` |
| `.caveat-info` background | `#dbeafe` | Add dark override: `#1e3a5f` |
| `.caveat-info` color | `#1e40af` | Add dark override: `#bfdbfe` |

3. The `winner-col` background (`rgba(59,130,246,0.06)`) is low-opacity enough
   to work in both modes -- no change needed.

**No JS toggle needed.** A manual theme toggle button is a separate UX feature.
`prefers-color-scheme` CSS support is the stated v1.1 requirement.

Source: [Pico CSS Color Schemes](https://picocss.com/docs/color-schemes) -- HIGH confidence.

---

### Feature: Tooltips (`?` icon popovers)

**Decision: HTML `popover` attribute + `popovertarget` button -- no JS, no library.**

The HTML Popover API reached Baseline Widely Available in April 2025. Supported
in Chrome 114+, Firefox 125+, Safari 17+, Edge 114+. Global coverage ~95%+.

Tooltip HTML pattern:

```html
<button type="button"
        class="tooltip-trigger"
        popovertarget="tip-opportunity-cost"
        aria-label="What is opportunity cost?">?</button>

<div id="tip-opportunity-cost"
     popover
     role="tooltip">
  The return you forgo by paying cash instead of keeping money invested.
</div>
```

The `popover` attribute provides dismiss-on-Escape, correct focus management,
and top-layer rendering (no z-index wars) automatically. No JS required.

**Do NOT use `popover=hint` + `interestfor` (hover triggering).** The
`interestfor` attribute is not yet Baseline -- it lacks Firefox/Safari production
support as of March 2026. The `popovertarget` click-toggle works everywhere.

**Do NOT use CSS-only `:hover` tooltips.** Pure CSS hover tooltips fail WCAG
1.4.13 (Content on Hover or Focus) -- the content is not dismissible, hoverable,
or persistent as required. The Popover API satisfies all three requirements.

**Do NOT use CSS Anchor Positioning for tooltip placement.** At 82% global
support (Firefox 147+ required), it is not yet Baseline Widely Available. Use
`position: fixed` with `max-width` and centered placement. For a `?` icon
popover, content does not need to appear precisely adjacent to the trigger.

New CSS additions needed (approximately 20 lines):

```css
.tooltip-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 50%;
  font-size: 0.75rem;
  padding: 0;
  cursor: help;
  /* inherits Pico button variables for color */
}

[popover].tooltip-content {
  max-width: min(90vw, 24rem);
  padding: 0.75rem 1rem;
  border-radius: var(--pico-border-radius);
  border: 1px solid var(--pico-muted-border-color);
  background: var(--pico-card-background-color);
  color: var(--pico-color);
}
```

Sources:
- [Popover API -- MDN](https://developer.mozilla.org/en-US/docs/Web/API/Popover_API) -- HIGH confidence
- [Popover Baseline announcement](https://web.dev/blog/popover-baseline) -- HIGH confidence
- [WCAG 1.4.13](https://www.w3.org/WAI/WCAG21/Understanding/content-on-hover-or-focus.html) -- HIGH confidence
- [CSS Anchor Positioning support](https://caniuse.com/css-anchor-positioning) -- 82%, not Baseline -- HIGH confidence

---

### Feature: Detailed Cost Breakdown Table (tabs, column toggles, compare view)

**Decision: ~50 lines vanilla JS for tab widget + ARIA management. No library.**

**Why not CSS-only tabs?** The CSS checkbox/radio hack cannot implement proper
ARIA tab semantics. W3C APG requires `aria-selected`, `aria-controls`,
`tabindex="-1"` on inactive tabs, and arrow-key navigation between tabs. These
attributes must be toggled dynamically. CSS-only tab approaches consistently
fail accessibility audits for keyboard users and screen readers.

**Why not a library (Van11y, Tabby)?** The feature is a single tab widget.
Adding a vendored JS file for 40-60 lines of standard behavior creates a
maintenance dependency with no benefit. The W3C tab pattern is fully specified
and stable.

HTMX integration: The detailed breakdown table is a new server-rendered partial
(Flask route + Jinja2 template) triggered by HTMX -- consistent with existing
results partials. Flask computes per-period data server-side; Jinja2 renders the
table HTML; HTMX swaps it into the results area. Tab switching is client-side
after swap.

The JS must re-initialize after HTMX partial injection:

```javascript
// static/tabs.js -- W3C tab pattern, ~50 lines
function initTabs() {
  document.querySelectorAll('[role="tablist"]').forEach(tablist => {
    const tabs = [...tablist.querySelectorAll('[role="tab"]')];
    tabs.forEach((tab, i) => {
      tab.addEventListener('click', () => activate(tabs, tab));
      tab.addEventListener('keydown', e => {
        if (e.key === 'ArrowRight') activate(tabs, tabs[(i + 1) % tabs.length]);
        if (e.key === 'ArrowLeft') activate(tabs, tabs[(i - 1 + tabs.length) % tabs.length]);
        if (e.key === 'Home') activate(tabs, tabs[0]);
        if (e.key === 'End') activate(tabs, tabs[tabs.length - 1]);
      });
    });
  });
}
function activate(tabs, target) {
  tabs.forEach(t => {
    const on = t === target;
    t.setAttribute('aria-selected', on);
    t.tabIndex = on ? 0 : -1;
    document.getElementById(t.getAttribute('aria-controls'))
      ?.toggleAttribute('hidden', !on);
  });
  target.focus();
}
document.addEventListener('htmx:afterSwap', initTabs);
initTabs();
```

Delivered as `static/tabs.js`, loaded in `base.html` alongside `htmx.min.js`.

Sources:
- [W3C APG Tabs Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/) -- HIGH confidence
- [ARIA tabpanel role -- MDN](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Roles/tabpanel_role) -- HIGH confidence

---

### Feature: JSON Export / Import

**Decision: Server-side Flask download route for export; HTMX file upload for import. No library.**

**Export flow:**
1. "Export JSON" is an `<a>` or form POST to `/export`.
2. Flask receives current form field values in the POST body.
3. Route validates through existing Pydantic models, calls `model_dump()`, then
   returns `flask.Response(json.dumps(data, indent=2), mimetype='application/json',
   headers={'Content-Disposition': 'attachment; filename="fathom-scenario.json"'})`.
4. Browser triggers file download -- no client-side Blob/URL dance required.

This is preferable to a client-side Blob export because Pydantic validation
happens before export (exported data is always clean), and it requires zero JS.

**Import flow:**
1. `<input type="file" accept=".json">` with `hx-trigger="change"` and
   `hx-encoding="multipart/form-data"` on the enclosing form.
2. HTMX POSTs the file to `/import`.
3. Flask reads the uploaded JSON via `request.files`, validates with Pydantic,
   returns the form partial pre-populated with imported values.
4. HTMX swaps the form partial -- same mechanism as existing live updates.

**No new Python library needed.** `json` (stdlib) + existing Pydantic models +
Flask's `request.files` covers everything.

Include a `version` field in the export payload for forward compatibility. Use
`pydantic_model.model_json_schema()` to document the schema alongside the code.

Sources:
- [Flask JSON/JS Patterns](https://flask.palletsprojects.com/en/stable/patterns/javascript/) -- HIGH confidence

---

### Feature: Comma-Normalized Number Inputs

**Decision: `Intl.NumberFormat` (native browser API) for display; server-side
comma-stripping in existing form parser. No library.**

HTML `<input type="number">` rejects comma-formatted values. Switch numeric
fields to `<input type="text" inputmode="numeric">`.

Client-side behavior (8 lines, no library):

```javascript
// Inline in base.html or a small static/inputs.js
document.querySelectorAll('input[inputmode="numeric"]').forEach(input => {
  input.addEventListener('blur', () => {
    const raw = input.value.replace(/,/g, '');
    const n = parseFloat(raw);
    if (!isNaN(n)) input.value = new Intl.NumberFormat('en-US').format(n);
  });
  input.addEventListener('focus', () => {
    input.value = input.value.replace(/,/g, '');
  });
});
```

`Intl.NumberFormat` is a native browser API -- Baseline Widely Available since
2018. Zero bytes added to the page.

Server-side: add `.replace(',', '')` before `Decimal()` conversion in the
existing form parser (`forms.py`). One-line change per numeric field. HTMX
POSTs the raw comma-formatted string; server strips commas transparently.

**Do NOT add Cleave.js, IMask, or AutoNumeric.** These libraries add 20-40 KB
for a feature solved in 8 lines of native JS.

Source: [Intl.NumberFormat -- MDN](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat) -- HIGH confidence.

---

### Feature: US Tax Rate Guidance

**Decision: Hardcode 2026 IRS brackets as a Python constant. Zero new dependencies.**

The feature helps users identify their marginal tax bracket to fill in the
"marginal tax rate" input. This is display/guidance only -- not part of
calculations.

2026 federal marginal rates (confirmed by IRS, same 7 brackets since TCJA):
`10%, 12%, 22%, 24%, 32%, 35%, 37%`

Rates are identical for 2025 and 2026; only income thresholds adjust for
inflation annually. Thresholds differ by filing status (single, married filing
jointly, head of household).

Implementation: a Python dict constant in a `constants.py` or directly in the
relevant route context. Rendered server-side as a `<details>`/`<summary>`
disclosure widget alongside the tax rate input field -- no JS needed.

**Do NOT fetch live IRS data.** The project is stateless with no external
dependencies. Brackets change once per year at most. Hardcode and add a comment
noting the source URL and tax year.

**Do NOT add a tax calculation library.** The guidance feature provides bracket
reference for the user, not a tax calculation. Existing `tax.py` handles the
financial math.

Sources:
- [IRS Federal Tax Rates and Brackets](https://www.irs.gov/filing/federal-income-tax-rates-and-brackets) -- HIGH confidence
- [Tax Foundation 2026 Brackets](https://taxfoundation.org/data/all/federal/2026-tax-brackets/) -- HIGH confidence

---

### v1.1 New Static Assets Summary

| File | Estimated Size | Purpose |
|------|---------------|---------|
| `static/tabs.js` | ~1 KB | W3C tab pattern for detailed breakdown table |
| Additions to `static/style.css` | ~2 KB | Tooltip styles, dark mode caveat overrides, tab styles |

No new vendor files. No CDN dependencies. No Python packages added.

---

### v1.1 HTMX Integration Notes

| Feature | HTMX Consideration |
|---------|-------------------|
| Tooltip popovers | No HTMX involvement -- pure HTML `popover` attribute behavior |
| Breakdown table tabs | JS re-initializes on `htmx:afterSwap` event |
| JSON import | Needs `hx-encoding="multipart/form-data"` on the file upload form |
| Comma inputs | HTMX POSTs comma-formatted strings; server strips them -- no special handling |
| Dark mode | No HTMX involvement -- pure CSS `@media` |
| Tax guidance | Static content in form template -- no HTMX involvement |

---

### v1.1 Alternatives Rejected

| Recommended | Alternative | Why Rejected |
|-------------|-------------|--------------|
| Remove `data-theme="light"` | Add JS theme toggle | Requirement is CSS `prefers-color-scheme`; a toggle button is a separate UX feature |
| `popovertarget` click-toggle popover | `interestfor` + `popover=hint` hover | Not Baseline -- missing Firefox/Safari production support (March 2026) |
| `popovertarget` click-toggle popover | CSS-only `:hover` tooltip | Fails WCAG 1.4.13 -- not dismissible, not hoverable, not persistent |
| `position: fixed` popover placement | CSS Anchor Positioning | 82% global support; Firefox 147+ required; not Baseline Widely Available |
| Vanilla JS tab pattern (~50 lines) | Van11y / Tabby library | Adds vendor file for a feature simple enough to write inline |
| Vanilla JS tab pattern (~50 lines) | CSS radio-button hack | No `aria-selected`, no arrow-key navigation -- fails WCAG |
| Flask download route for JSON export | Client-side Blob + `URL.createObjectURL` | Flask route runs Pydantic validation before export; no JS needed |
| `Intl.NumberFormat` (native) | Cleave.js / IMask / AutoNumeric | Libraries add 20-40 KB for an 8-line feature |
| Hardcoded tax bracket data | External IRS API | Project is stateless; brackets change once/year; no external dependency |

---

### v1.1 What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `interestfor` attribute | Not Baseline -- missing Firefox/Safari support (March 2026) | `popovertarget` click-toggle |
| CSS Anchor Positioning | 82% support, Firefox 147+, not Baseline Widely Available | `position: fixed` centered popover |
| `<input type="number">` for formatted inputs | Rejects comma-formatted values, no comma display | `<input type="text" inputmode="numeric">` |
| Cleave.js / IMask / AutoNumeric | 20-40 KB for an 8-line feature | `Intl.NumberFormat` + server-side strip |
| Any tab UI library | New vendor file for a well-specified 50-line pattern | Vanilla JS W3C tab pattern |
| Any second CSS framework | Creates variable conflicts with Pico CSS | Stay with Pico CSS 2.1.1 |

---

## v1.0 Original Stack (unchanged)

*Original research: 2026-03-10*

### Core Framework

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Flask | 3.1.3 | Web framework, SSR, routing | Best Python framework for SSR + HTMX. Lightweight, Jinja2-native, massive ecosystem. FastAPI is API-first (wrong paradigm for SSR HTML). Django is overkill for a single-page stateless app with no database. Flask hits the sweet spot: template rendering is first-class, HTMX partial responses are trivial (just render a template fragment), and the learning curve is minimal. | HIGH |
| Jinja2 | 3.1.6 | HTML templating | Ships with Flask. Industry standard for Python SSR. Supports template inheritance, macros, and partial rendering -- all needed for HTMX fragment responses. No reason to consider alternatives. | HIGH |
| Gunicorn | 25.1.0 | Production WSGI server | Standard production server for Flask. Single-process constraint is fine -- Gunicorn with 1-4 workers in a single container. Uvicorn is ASGI (wrong protocol for Flask WSGI). | HIGH |

### Frontend (CDN / Static)

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| HTMX | 2.0.8 | Partial page updates | Mandated by PRD. 16KB, zero dependencies. Enables live result updates by swapping HTML fragments from the server. No build step needed -- serve from CDN or vendor locally. | HIGH |

### Charting

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| pygal | 3.1.0 | SVG chart generation | Purpose-built for server-side SVG chart rendering in Python. Supports bar charts (True Total Cost comparison) and line charts (cumulative cost over time) -- the two chart types the PRD requires. Outputs clean SVG that can be embedded directly in HTML. Actively maintained (latest release Dec 2025). Alternatives: matplotlib can output SVG but produces raster-style graphics with poor web integration; Chart.js requires client-side JS (acceptable fallback per PRD but not preferred). pygal's SVG output is WCAG-friendly: text is real text (not rasterized), and the library supports custom styling/colors. | HIGH |

### Form Handling and Validation

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| WTForms | 3.2.1 | Form definition and validation | Server-side form validation for financing option inputs. Handles type coercion (strings to Decimal), range validation, conditional required fields. Integrates natively with Flask via Flask-WTF. Pydantic is an alternative but is model-validation focused, not HTML-form focused -- WTForms generates HTML labels and error messages directly, which matters for WCAG compliance. | HIGH |
| Flask-WTF | 1.2.2 | Flask + WTForms integration | CSRF protection (needed even for HTMX POST requests), form rendering helpers, file upload handling (not needed but comes free). | HIGH |

### Data Modeling and Calculation

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python `decimal` | stdlib | Financial calculations | Mandated by financial accuracy requirements. IEEE 754 floats produce rounding errors in currency math. `decimal.Decimal` with explicit precision avoids this. Zero dependencies -- it is in the standard library. | HIGH |
| Pydantic | 2.12.5 | Internal data models | Type-safe data containers for calculation inputs/outputs. Validates and coerces data between form layer and calculation engine. Excellent type checker support (important for ty and pyrefly). Use for internal models only -- WTForms handles the HTTP form layer. | MEDIUM |

### Testing

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| pytest | 9.0.2 | Test runner | Standard Python test runner. Flask has built-in test client that works with pytest. | HIGH |
| pytest-cov | 7.0.0 | Coverage reporting | Standard coverage plugin for pytest. | HIGH |

### CSS / Styling

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Pico CSS | 2.1.1 | CSS framework | Classless semantic CSS with dark mode built in. No build step, no class names to memorize, excellent HTMX compatibility. | HIGH |

### Infrastructure

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Docker | N/A | Containerization | PRD mandates self-hosting with Dockerfile. Single-stage build: `python:3.14-slim` base, `uv sync`, `gunicorn` entrypoint. | HIGH |
| uv | latest | Package management | Mandated by PRD. Replaces pip, poetry, conda. Handles venv creation, dependency resolution, and script running. | HIGH |

## What NOT to Use (v1.0 + v1.1 + v1.2)

| Technology | Why Not |
|------------|---------|
| mypy / pyright | PRD mandates ty and pyrefly only |
| pip / poetry / conda | PRD mandates uv only |
| pre-commit | PRD mandates prek |
| SQLite / PostgreSQL / any DB | Stateless app, no persistence |
| Redis / Memcached | No caching layer needed for stateless calculator |
| Celery / task queues | Calculations complete in <300ms, no background jobs |
| React / Vue / Svelte | SSR with HTMX replaces SPA frameworks entirely |
| Node.js / npm | Pure Python stack, no JS toolchain |
| Docker Compose | Single process, no orchestration needed |
| `interestfor` attribute | Not Baseline -- no Firefox/Safari production support (March 2026) |
| CSS Anchor Positioning | 82% global support, not Baseline Widely Available |
| Cleave.js / IMask / AutoNumeric | 8-line feature; no library needed |
| Any second CSS framework | Conflicts with Pico CSS variable system |
| numpy-financial | Existing Decimal amortization code covers all needed loan math |
| Alpine.js / Stimulus | CSS `:has()` handles toggle visibility; no JS framework needed |
| py-moneyed | Would require rewriting all Decimal arithmetic |
| QuantLib | Nuclear option for simple amortization + interest accrual |

## Sources

### v1.2 Sources

- Code review findings: `docs/code-review-2026-03-15.md` -- HIGH confidence (primary source)
- Pydantic 2.12.5 runtime version -- verified via `python -c "import pydantic; print(pydantic.__version__)"` -- HIGH confidence
- Flask 3.1.3 runtime version -- verified via `python -c "import flask; print(flask.__version__)"` -- HIGH confidence
- `quantize_money` duplication -- verified via `grep -r "def quantize_money" src/` showing 5 identical definitions -- HIGH confidence
- CSS `:has()` browser support -- Baseline Widely Available Dec 2023 (Chrome 105+, Firefox 121+, Safari 15.4+) -- HIGH confidence
- `_build_promo_result()` bug -- verified via code inspection of `engine.py` lines 279-357 -- HIGH confidence

### v1.1 Sources

- [Pico CSS Color Schemes](https://picocss.com/docs/color-schemes) -- dark mode mechanism -- HIGH confidence
- [Popover API -- MDN](https://developer.mozilla.org/en-US/docs/Web/API/Popover_API) -- `popovertarget` usage -- HIGH confidence
- [Popover Baseline Widely Available](https://web.dev/blog/popover-baseline) -- April 2025 -- HIGH confidence
- [CSS Anchor Positioning -- Can I Use](https://caniuse.com/css-anchor-positioning) -- 82% support, not Baseline -- HIGH confidence
- [WCAG 1.4.13 Content on Hover or Focus](https://www.w3.org/WAI/WCAG21/Understanding/content-on-hover-or-focus.html) -- tooltip WCAG requirements -- HIGH confidence
- [W3C APG Tabs Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/) -- tab ARIA requirements -- HIGH confidence
- [Intl.NumberFormat -- MDN](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat) -- comma formatting -- HIGH confidence
- [Flask JSON/JS Patterns](https://flask.palletsprojects.com/en/stable/patterns/javascript/) -- export route pattern -- HIGH confidence
- [IRS Federal Tax Rates and Brackets](https://www.irs.gov/filing/federal-income-tax-rates-and-brackets) -- 2026 rates -- HIGH confidence
- [Tax Foundation 2026 Brackets](https://taxfoundation.org/data/all/federal/2026-tax-brackets/) -- bracket data verification -- HIGH confidence

### v1.0 Sources

- Flask 3.1.3: https://pypi.org/project/flask/ (verified 2026-03-10)
- Jinja2 3.1.6: https://pypi.org/project/jinja2/ (verified 2026-03-10)
- Gunicorn 25.1.0: https://pypi.org/project/gunicorn/ (verified 2026-03-10)
- HTMX 2.0.8: https://htmx.org (verified 2026-03-10)
- pygal 3.1.0: https://pypi.org/project/pygal/ (verified 2026-03-10)
- pygal chart types: https://www.pygal.org/en/stable/documentation/types/index.html
- WTForms 3.2.1: https://pypi.org/project/wtforms/ (verified 2026-03-10)
- Flask-WTF 1.2.2: https://pypi.org/project/flask-wtf/ (verified 2026-03-10)
- Pydantic 2.12.5: https://pypi.org/project/pydantic/ (verified 2026-03-10)
- pytest 9.0.2: https://pypi.org/project/pytest/ (verified 2026-03-10)
- pytest-cov 7.0.0: https://pypi.org/project/pytest-cov/ (verified 2026-03-10)
