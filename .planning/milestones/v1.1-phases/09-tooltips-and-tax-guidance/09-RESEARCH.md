# Phase 9: Tooltips and Tax Guidance - Research

**Researched:** 2026-03-13
**Domain:** HTML Popover API, CSS Anchor Positioning, WCAG 1.4.13 compliance, IRS tax bracket data
**Confidence:** HIGH

## Summary

Phase 9 adds explanatory tooltips to all form fields and result metrics, plus a tax bracket reference widget. The locked decision uses the native HTML `popover` attribute with `popover="auto"` for tooltip content, triggered by `<button>` elements with `popovertarget`. CSS Anchor Positioning places popovers near their triggers with a fallback to fixed viewport centering for older browsers. The tax bracket widget uses the existing `<details>` pattern with a table of 2025 IRS brackets that auto-fills the tax rate input on row click.

All core APIs (Popover API and CSS Anchor Positioning) are now Baseline Widely Available as of early 2025, with support across Chrome 125+, Firefox 148+, Safari 26+, and Edge 125+. The implementation requires zero JavaScript for basic popover behavior -- only the tax bracket row-click interaction needs a small JS handler (or could use HTMX). The existing CSS custom property system and dark mode pattern (`@media (prefers-color-scheme: dark) { :root:not([data-theme]) }`) extend naturally to popover styling.

**Primary recommendation:** Use pure HTML `popover`/`popovertarget` attributes with CSS Anchor Positioning via `@supports` progressive enhancement. Define tax bracket data as a Python list-of-dicts constant, render via Jinja, and wire row clicks with minimal delegated JS on `#comparison-form`.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Native HTML `popover` attribute + `popovertarget` for show/hide -- zero custom JS for core behavior
- `popover="auto"` (default) -- browser auto-closes other popovers, only one open at a time
- Click/tap only to open -- no hover behavior. Consistent across mouse, keyboard, and touch
- CSS Anchor Positioning API for popover placement near trigger -- graceful fallback to top-center viewport for older browsers
- Escape to dismiss, click-outside to dismiss -- all handled natively by popover API
- Short paragraph + concrete example for every tooltip (2-3 sentences: definition + why it matters + example)
- Same style for both form field tooltips and result metric tooltips -- consistent experience
- Claude drafts all tooltip copy during implementation, based on the calculation engine's actual logic
- Every form field gets a tooltip -- including self-explanatory ones like Purchase Price
- Styled `<button class="tip">?</button>` -- small circle, muted color, ~16px, vertically centered with label
- Dark mode variant via CSS variables
- Placed after the label text, before the input field: "Annual Interest Rate (APR) ?"
- ? icon after each row label in the breakdown table
- ? icon next to "True Total Cost" in the recommendation card
- Chart titles do NOT get tooltips
- Expandable HTML `<details>` element below the tax rate field -- "What's my bracket?"
- Shows 2025 IRS brackets for Single and Married Filing Jointly side-by-side in one table
- All 7 federal rates (10%--37%) with income ranges
- Bracket data defined in Python (list of dicts), rendered via Jinja template
- Clicking a bracket row auto-fills the tax rate input with that rate
- Uses existing `|comma` Jinja filter for income range formatting
- All tooltips keyboard-focusable via the `<button>` trigger
- Content persistent until explicitly dismissed (click-only, no auto-timeout)
- Tax bracket table rows keyboard-activatable (Enter/Space to select rate)

### Claude's Discretion
- Exact tooltip copy for all fields and metrics
- Popover arrow/caret styling (or no arrow)
- Popover max-width and padding
- Whether to add a small close button inside popovers or rely entirely on light-dismiss
- Dark mode color palette for popover background/border
- Tax bracket table styling details (borders, spacing, selected-row highlight color)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TIPS-01 | User can see a `?` icon next to each form field that has financial jargon, and clicking/hovering reveals an explanation | HTML popover API with `popovertarget` on `<button class="tip">` elements; per CONTEXT every field gets a tooltip (not just jargon) |
| TIPS-02 | User can see a `?` icon next to each result metric with an explanation | Same popover pattern applied to breakdown table row labels and recommendation card True Total Cost |
| TIPS-03 | Tooltips are accessible -- keyboard-focusable, dismissable with Escape, hoverable without disappearing (WCAG 1.4.13) | Native popover API provides Escape dismiss, light-dismiss, focus management; `<button>` triggers are inherently keyboard-focusable |
| TAX-01 | User can expand a "What's my bracket?" reference below the tax rate field showing 2025 IRS brackets by filing status | `<details>` element with bracket table; Python data constant passed to Jinja template |
| TAX-02 | Tax bracket table shows income ranges for Single and Married Filing Jointly at all 7 federal rates (10%--37%) | 2025 IRS bracket data verified from IRS.gov (see tax bracket data section below) |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| HTML Popover API | Baseline 2025 | Show/hide tooltip content | Native browser API, zero JS, built-in accessibility |
| CSS Anchor Positioning | Baseline 2025 | Position popovers near triggers | Native positioning relative to anchor elements |
| `<details>/<summary>` | HTML5 | Tax bracket expand/collapse | Already used in Global Settings, native toggle |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Jinja2 | (existing) | Render tooltip content and bracket table | All templates |
| Pico CSS | (existing) | Base styling foundation | Already the project CSS framework |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Native popover | Tippy.js / Floating UI | Decision locked: native popover, zero dependencies |
| CSS Anchor Positioning | JS-based positioning | Decision locked: CSS-first with fallback |

**Installation:**
No new dependencies required. All features use native browser APIs and existing stack.

## Architecture Patterns

### Integration Points in Existing Templates

The tooltip triggers (`<button class="tip">`) must be inserted into existing template files. Each template needs modifications:

**Form fields (6 option field templates + global settings + purchase price):**
- `src/fathom/templates/index.html` -- Purchase Price label
- `src/fathom/templates/partials/global_settings.html` -- Investment Return Rate, Inflation Rate, Marginal Tax Rate labels + tax bracket widget
- `src/fathom/templates/partials/option_fields/traditional.html` -- APR, Loan Term, Down Payment
- `src/fathom/templates/partials/option_fields/promo_zero.html` -- Promotional Term, Down Payment, Deferred Interest, Post-Promo APR
- `src/fathom/templates/partials/option_fields/promo_cashback.html` -- APR, Loan Term, Cash-Back Amount, Down Payment
- `src/fathom/templates/partials/option_fields/promo_price.html` -- Discounted Price, APR, Loan Term, Down Payment
- `src/fathom/templates/partials/option_fields/custom.html` -- Effective APR, Term, Upfront Cash
- `src/fathom/templates/partials/option_fields/cash.html` -- Brief note on cash purchase

**Result metrics (2 templates):**
- `src/fathom/templates/partials/results/recommendation.html` -- True Total Cost
- `src/fathom/templates/partials/results/breakdown_table.html` -- Each row label (Interest, Opportunity Cost, Inflation Adj, Tax Savings, True Total Cost)

### Pattern 1: Tooltip Trigger + Popover

**What:** A `<button>` with `popovertarget` paired with a `<div popover>` element.
**When to use:** Every form field label and result metric label.

```html
<!-- Source: MDN Popover API docs -->
<label for="option-0-apr">
  Annual Interest Rate (APR)
  <button type="button" class="tip" popovertarget="tip-apr-0" aria-label="What is APR?">?</button>
</label>
<div id="tip-apr-0" popover class="tooltip-content">
  <p><strong>Annual Percentage Rate (APR)</strong> is the yearly interest rate
  charged on your loan balance. For example, a $10,000 loan at 6% APR costs
  roughly $600 in interest the first year. Lower APR means less interest paid.</p>
</div>
```

Key details:
- `type="button"` prevents form submission
- Unique `id` per popover (use field name + option index for form fields)
- `aria-label` on the button for screen readers
- `popover` (no value) defaults to `popover="auto"`

### Pattern 2: CSS Anchor Positioning with Fallback

**What:** Position popover near its trigger button, fall back to viewport center.
**When to use:** All tooltip popovers.

```css
/* Anchor positioning for modern browsers */
@supports (anchor-name: --tip) {
  .tip {
    anchor-name: --tip;
  }

  .tooltip-content {
    position: absolute;
    position-anchor: --tip;
    position-area: top center;
    position-try-fallbacks: bottom center, right center, left center;
    margin: 0;
    inset: auto;
  }
}

/* Fallback for browsers without anchor positioning */
@supports not (anchor-name: --tip) {
  .tooltip-content {
    position: fixed;
    top: 2rem;
    left: 50%;
    transform: translateX(-50%);
    margin: 0;
    inset: auto;
  }
}
```

**Important caveat:** Each popover trigger needs a unique anchor name if multiple could be visible simultaneously. Since `popover="auto"` ensures only one is open at a time, a single shared anchor name does NOT work -- the browser associates anchor names at parse time, not at show time. Two approaches:

1. **Unique anchor names per trigger** via inline style: `style="anchor-name: --tip-apr-0"` and matching `style="position-anchor: --tip-apr-0"` on the popover. This is verbose but correct.
2. **Use the implicit popover/invoker anchor relationship**: When a button has `popovertarget`, the popover can reference its invoker implicitly. Per MDN: "Popovers and invokers have an implicit anchor reference when `popovertarget` is used." This means:

```css
.tooltip-content {
  position: absolute;
  position-area: top center;
  position-try-fallbacks: bottom center, right center, left center;
  margin: 0;
  inset: auto;
}
```

The implicit anchor relationship is the cleanest approach. However, this is a newer part of the spec. If it does not work in testing, fall back to explicit anchor names via Jinja template variables.

### Pattern 3: Tax Bracket Widget

**What:** `<details>` with bracket table, click-to-fill behavior.
**When to use:** Below the Marginal Tax Rate field in global settings.

```html
<details class="tax-bracket-ref">
  <summary>What's my bracket?</summary>
  <table class="bracket-table">
    <thead>
      <tr>
        <th scope="col">Rate</th>
        <th scope="col">Single</th>
        <th scope="col">Married Filing Jointly</th>
      </tr>
    </thead>
    <tbody>
      {% for bracket in tax_brackets %}
      <tr class="bracket-row" data-rate="{{ bracket.rate }}" tabindex="0"
          role="button" aria-label="Select {{ bracket.rate }}% tax rate">
        <td>{{ bracket.rate }}%</td>
        <td>${{ bracket.single_range }}</td>
        <td>${{ bracket.mfj_range }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  <small>Click a row to use that rate. Source: IRS Rev. Proc. 2024-40</small>
</details>
```

### Pattern 4: Tax Bracket Row Click Handler

**What:** Delegated event listener that fills the tax rate input when a bracket row is clicked or activated via keyboard.

```javascript
// Delegated on #comparison-form (same pattern as formatting.js)
form.addEventListener("click", function (e) {
  var row = e.target.closest(".bracket-row");
  if (!row) return;
  var rate = row.getAttribute("data-rate");
  var taxInput = document.getElementById("tax-rate");
  if (taxInput && rate) {
    taxInput.value = rate;
    // Also check the "Include tax implications" checkbox
    var taxCheckbox = document.querySelector('[name="tax_enabled"]');
    if (taxCheckbox && !taxCheckbox.checked) {
      taxCheckbox.checked = true;
    }
  }
});

// Keyboard activation for bracket rows
form.addEventListener("keydown", function (e) {
  if (e.key !== "Enter" && e.key !== " ") return;
  var row = e.target.closest(".bracket-row");
  if (!row) return;
  e.preventDefault();
  row.click();
});
```

### Anti-Patterns to Avoid
- **Hover-only tooltips:** Decision explicitly locks click-only. No `title` attributes, no CSS `:hover` popovers.
- **Custom popover JS:** Do not write show/hide/dismiss logic -- the native API handles everything.
- **Duplicate tooltip IDs:** Each popover needs a unique `id`. With dynamic option indices, use Jinja variables: `tip-apr-{{ opt.idx }}`.
- **Forgetting `type="button"`:** Without it, clicking the `?` button submits the form.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tooltip show/hide | Custom JS event handlers | `popover` + `popovertarget` | Native API handles dismiss, stacking, focus |
| Tooltip positioning | Absolute positioning with JS calculations | CSS Anchor Positioning | Handles viewport edges, flip behavior natively |
| Expand/collapse widget | Custom JS accordion | `<details>/<summary>` | Already used in project, zero JS |
| Keyboard focus management | Custom focus trap | Native popover focus behavior | API manages focus return automatically |

**Key insight:** The HTML Popover API eliminates the category of bugs that made tooltips historically difficult -- stacking context, focus management, dismiss-on-click-outside, escape handling, and z-index wars are all handled by the browser's top layer.

## Common Pitfalls

### Pitfall 1: Popover IDs Must Be Globally Unique
**What goes wrong:** Duplicate `id` values when multiple financing options share the same field names (e.g., two options both have APR).
**Why it happens:** Template loops create multiple options with the same field names.
**How to avoid:** Include the option index in every popover `id`: `tip-apr-{{ opt.idx }}` and matching `popovertarget="tip-apr-{{ opt.idx }}"`.
**Warning signs:** Only the first tooltip works; others silently fail.

### Pitfall 2: Button Inside Label Accessibility
**What goes wrong:** Placing a `<button>` inside a `<label>` can cause the button click to also trigger the label's `for` input.
**Why it happens:** Labels forward clicks to their associated input.
**How to avoid:** Place the button AFTER the `<label>` tag, not inside it. Or use a `<span>` wrapper that separates the label text from the button:
```html
<div class="label-with-tip">
  <label for="option-0-apr">Annual Interest Rate (APR)</label>
  <button type="button" class="tip" popovertarget="tip-apr-0">?</button>
</div>
```
**Warning signs:** Clicking `?` focuses the input instead of (or in addition to) opening the popover.

### Pitfall 3: Popover Content Swallowed by HTMX
**What goes wrong:** Popovers placed inside HTMX-swapped containers lose their content or stop working after a swap.
**Why it happens:** HTMX replaces innerHTML, removing popover elements from the DOM.
**How to avoid:** For form field tooltips, this is fine -- they live in the form which is not swapped. For result metric tooltips, they are inside `#results` which IS swapped by HTMX -- but this is also fine because the results HTML is re-rendered each time with fresh popover elements.
**Warning signs:** Tooltips work on initial load but not after recalculation.

### Pitfall 4: CSS Anchor Positioning Scope
**What goes wrong:** Anchor names can collide across different tooltip triggers, causing popovers to position relative to the wrong element.
**Why it happens:** `anchor-name` is a global namespace within the document.
**How to avoid:** Use the implicit invoker-anchor relationship (popover + popovertarget), or assign unique anchor names per trigger via inline styles.

### Pitfall 5: Forgetting type="button" on Tip Buttons
**What goes wrong:** Clicking `?` submits the form.
**Why it happens:** Default button type in a form is `submit`.
**How to avoid:** Always include `type="button"` on tip buttons.

## Code Examples

### Complete Tooltip Markup (Form Field)
```html
<!-- In option field template -->
<div class="label-with-tip">
  <label for="option-{{ opt.idx }}-apr">Annual Interest Rate (APR)</label>
  <button type="button" class="tip"
          popovertarget="tip-apr-{{ opt.idx }}"
          aria-label="What is APR?">?</button>
</div>
<div id="tip-apr-{{ opt.idx }}" popover class="tooltip-content">
  <p><strong>Annual Percentage Rate (APR)</strong> is the yearly interest rate
  on your outstanding loan balance. A $10,000 loan at 6% APR costs about
  $600 in interest the first year, decreasing as you pay down the balance.</p>
</div>
<fieldset role="group">
  <input type="text" inputmode="decimal" id="option-{{ opt.idx }}-apr" ...>
  <span class="suffix">%</span>
</fieldset>
```

### Complete Tooltip Markup (Result Metric)
```html
<!-- In breakdown_table.html -->
<td class="row-label">
  {{ row.label }}
  <button type="button" class="tip"
          popovertarget="tip-metric-{{ loop.index0 }}"
          aria-label="What is {{ row.label }}?">?</button>
  <div id="tip-metric-{{ loop.index0 }}" popover class="tooltip-content">
    <p>{{ row.tooltip }}</p>
  </div>
</td>
```

### CSS Styling for Tip Button and Popover
```css
/* Tip button */
.tip {
  all: unset;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1rem;
  height: 1rem;
  font-size: 0.7rem;
  font-weight: 700;
  border-radius: 50%;
  border: 1.5px solid var(--tip-border);
  color: var(--tip-color);
  background: var(--tip-bg);
  cursor: pointer;
  vertical-align: middle;
  margin-left: 0.25rem;
}

.tip:focus-visible {
  outline: 2px solid var(--pico-primary);
  outline-offset: 2px;
}

/* Tooltip popover content */
.tooltip-content {
  max-width: 320px;
  padding: 0.75rem 1rem;
  border-radius: var(--pico-border-radius);
  border: 1px solid var(--tooltip-border);
  background: var(--tooltip-bg);
  color: var(--tooltip-text);
  font-size: 0.875rem;
  line-height: 1.5;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Label + tip button layout */
.label-with-tip {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
}

/* CSS custom properties for theming */
:root {
  --tip-border: var(--pico-muted-border-color);
  --tip-color: var(--pico-muted-color);
  --tip-bg: transparent;
  --tooltip-bg: #ffffff;
  --tooltip-border: var(--pico-muted-border-color);
  --tooltip-text: var(--pico-color);
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme]) {
    --tooltip-bg: #1e293b;
    --tooltip-border: #475569;
    --tooltip-text: #e2e8f0;
  }
}
```

### Tax Bracket Data (Python)
```python
# Source: IRS Rev. Proc. 2024-40 (for tax year 2025)
TAX_BRACKETS_2025: list[dict[str, object]] = [
    {"rate": 10, "single_min": 0,       "single_max": 11_925,
                 "mfj_min": 0,          "mfj_max": 23_850},
    {"rate": 12, "single_min": 11_926,  "single_max": 48_475,
                 "mfj_min": 23_851,     "mfj_max": 96_950},
    {"rate": 22, "single_min": 48_476,  "single_max": 103_350,
                 "mfj_min": 96_951,     "mfj_max": 206_700},
    {"rate": 24, "single_min": 103_351, "single_max": 197_300,
                 "mfj_min": 206_701,    "mfj_max": 394_600},
    {"rate": 32, "single_min": 197_301, "single_max": 250_525,
                 "mfj_min": 394_601,    "mfj_max": 501_050},
    {"rate": 35, "single_min": 250_526, "single_max": 626_350,
                 "mfj_min": 501_051,    "mfj_max": 751_600},
    {"rate": 37, "single_min": 626_351, "single_max": None,
                 "mfj_min": 751_601,    "mfj_max": None},
]
```

## 2025 IRS Tax Bracket Data (Verified)

Source: IRS.gov Federal Income Tax Rates and Brackets page + Tax Foundation verification.

| Rate | Single | Married Filing Jointly |
|------|--------|----------------------|
| 10% | $0 -- $11,925 | $0 -- $23,850 |
| 12% | $11,926 -- $48,475 | $23,851 -- $96,950 |
| 22% | $48,476 -- $103,350 | $96,951 -- $206,700 |
| 24% | $103,351 -- $197,300 | $206,701 -- $394,600 |
| 32% | $197,301 -- $250,525 | $394,601 -- $501,050 |
| 35% | $250,526 -- $626,350 | $501,051 -- $751,600 |
| 37% | $626,351+ | $751,601+ |

Confidence: HIGH -- verified against IRS.gov official data.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Custom JS tooltip libraries (Tippy.js, Popper.js) | Native HTML `popover` attribute | Baseline April 2025 | Zero dependencies, built-in a11y |
| JS-calculated positioning | CSS Anchor Positioning | Baseline early 2025 | Declarative, handles edge cases |
| `title` attribute for tooltips | `popover` with rich content | 2024+ | Styled, accessible, persistent content |
| Manual focus trap for modals/tooltips | Native popover focus management | 2024+ | Browser handles focus return |

## Open Questions

1. **Implicit invoker-anchor relationship scope**
   - What we know: MDN documents that `popovertarget` creates an implicit anchor reference
   - What's unclear: Whether this works reliably across all target browsers without explicit `anchor-name`/`position-anchor`
   - Recommendation: Start with implicit anchoring; if testing reveals issues, fall back to explicit `anchor-name` via inline styles

2. **Tooltip content for breakdown table rows**
   - What we know: Row labels come from `display.breakdown_rows` in template context
   - What's unclear: Whether tooltip text should be passed as part of `breakdown_rows` data or defined in the template
   - Recommendation: Add a `tooltip` field to each breakdown row dict in `results.py`, keeping content with data

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + Playwright (sync API) |
| Config file | `pyproject.toml` (pytest section) |
| Quick run command | `uv run pytest tests/ -x -q` |
| Full suite command | `uv run pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TIPS-01 | `?` button present next to each form field, popover opens on click | e2e (Playwright) | Playwright MCP: navigate, click `.tip`, assert `[popover]:popover-open` | No -- Wave 0 |
| TIPS-02 | `?` button present next to result metrics, popover opens on click | e2e (Playwright) | Playwright MCP: submit form, click `.tip` in results, assert popover | No -- Wave 0 |
| TIPS-03 | Keyboard focus, Escape dismiss, persistent content | e2e (Playwright) | Playwright MCP: Tab to `.tip`, Enter to open, Escape to close | No -- Wave 0 |
| TAX-01 | "What's my bracket?" details expands with bracket table | unit + e2e | `uv run pytest tests/test_routes.py -x -q` (bracket data in context) + Playwright | Partially (test_routes exists) |
| TAX-02 | Table shows all 7 rates for Single and MFJ with correct ranges | unit | `uv run pytest tests/test_tax_brackets.py -x -q` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/ -x -q`
- **Per wave merge:** `uv run pytest tests/ -v`
- **Phase gate:** Full suite green + Playwright verification before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_tax_brackets.py` -- verify bracket data constant has correct 2025 IRS values, all 7 rates, correct income ranges
- [ ] Playwright verification for TIPS-01, TIPS-02, TIPS-03 -- popover open/close, keyboard navigation, Escape dismiss
- [ ] `tests/test_routes.py` additions -- verify `tax_brackets` in template context for index route

## Sources

### Primary (HIGH confidence)
- [MDN Popover API](https://developer.mozilla.org/en-US/docs/Web/API/Popover_API/Using) -- full implementation guide, accessibility behavior, CSS styling
- [MDN CSS Anchor Positioning](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Anchor_positioning) -- anchor-name, position-area, fallbacks, @supports
- [IRS Federal Income Tax Rates and Brackets](https://www.irs.gov/filing/federal-income-tax-rates-and-brackets) -- 2025 bracket data
- [Can I Use: Popover API](https://caniuse.com/mdn-api_htmlelement_popover) -- browser support data
- [Can I Use: CSS Anchor Positioning](https://caniuse.com/css-anchor-positioning) -- browser support data

### Secondary (MEDIUM confidence)
- [Tax Foundation 2025 Brackets](https://taxfoundation.org/data/all/federal/2025-tax-brackets/) -- cross-verified bracket data
- [Chrome Developers: Popover API](https://developer.chrome.com/blog/introducing-popover-api) -- implementation details
- [Chrome Developers: Anchor Positioning](https://developer.chrome.com/docs/css-ui/anchor-positioning-api) -- detailed API guide

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- native browser APIs, well-documented, Baseline Widely Available
- Architecture: HIGH -- existing codebase patterns clearly support the integration
- Pitfalls: HIGH -- well-understood from MDN documentation and existing template structure
- Tax data: HIGH -- verified against IRS.gov official source

**Research date:** 2026-03-13
**Valid until:** 2026-04-13 (stable APIs, tax data valid for 2025 tax year)
