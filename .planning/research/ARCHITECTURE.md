# Architecture Research

**Domain:** v1.1 feature integration — existing Flask/HTMX/Pico CSS SSR app
**Researched:** 2026-03-13
**Confidence:** HIGH

---

## Existing Architecture (Baseline)

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser (Client)                          │
│  HTML form + HTMX attributes + two inline <script> blocks       │
│  Pico CSS: data-theme="light" hardcoded on <html>               │
├──────────────────────────────────────────────────────────────────┤
│  POST /compare    GET /partials/*    (HTMX requests)            │
├──────────────────────────────────────────────────────────────────┤
│                        Flask routes.py                           │
│  Blueprint: index / compare_options / option_fields /            │
│             add_option / remove_option                           │
├──────────────────────────────────────────────────────────────────┤
│                        Python Layer                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │
│  │ forms.py │  │ engine.py│  │results.py│  │  charts.py   │    │
│  │ parse →  │  │ compare()│  │ analyze_ │  │ prepare_     │    │
│  │ validate │  │          │  │ results()│  │ charts()     │    │
│  │ → build  │  │          │  │          │  │              │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                       │
│  │models.py │  │amort.py  │  │ tax.py   │  (+ inflation.py,     │
│  │ Pydantic │  │ Decimal  │  │opportunity│    caveats.py)        │
│  └──────────┘  └──────────┘  └──────────┘                       │
├──────────────────────────────────────────────────────────────────┤
│                        Jinja2 Templates                          │
│  base.html → index.html → partials/                             │
│    results.html                                                  │
│      results/recommendation.html                                 │
│      results/breakdown_table.html                               │
│      results/bar_chart.html + line_chart.html                   │
│    option_card.html → option_fields/{type}.html (×6)            │
│    global_settings.html                                         │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities (Current)

| Component | Responsibility | v1.1 Impact |
|-----------|----------------|-------------|
| `routes.py` | Request routing, template context assembly | NEW routes for export/import |
| `forms.py` | parse → validate → build pipeline | MODIFY: strip commas before Decimal parse |
| `engine.py` | All financial calculations | NO CHANGE |
| `results.py` | Build display-ready data from ComparisonResult | MODIFY: expose monthly_data for period table |
| `charts.py` | SVG coordinate computation | NO CHANGE |
| `models.py` | Pydantic domain models | NO CHANGE |
| `base.html` | HTML shell, CSS/JS assets | MODIFY: remove `data-theme="light"` |
| `index.html` | Main page layout, form + results grid | MODIFY: add export/import partial |
| `partials/results.html` | Results section orchestrator | MODIFY: add period-table section |
| `static/style.css` | Custom overrides on Pico CSS | ADD: tooltip, tab, period-table styles |

---

## v1.1 Revised System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser                                   │
│  Pico CSS auto dark mode (prefers-color-scheme)                 │
│  Popover API tooltips (HTML native, no JS needed)               │
│  Comma formatting JS (~20 lines, cosmetic only)                 │
│  Tab switching JS (~30 lines, UI state only)                    │
│  CSS column toggles (checkbox + sibling combinator)             │
├──────────────────────────────────────────────────────────────────┤
│  Existing routes  +  POST /export  +  POST /import              │
├──────────────────────────────────────────────────────────────────┤
│                        Python Layer                              │
│  forms.py:     _try_decimal() strips commas (MODIFY)            │
│  results.py:   build_period_table_data() (NEW function)         │
│                analyze_results() adds period_table key (MODIFY) │
│  routes.py:    export_config() + import_config() (NEW routes)   │
├──────────────────────────────────────────────────────────────────┤
│                        Templates                                 │
│  base.html:                remove data-theme="light" (MODIFY)   │
│  index.html:               add export/import partial (MODIFY)   │
│  partials/results.html:    add period_table section (MODIFY)    │
│  NEW: partials/export_import.html                               │
│  NEW: partials/results/period_table.html                        │
│  MODIFY: partials/results/breakdown_table.html (tooltip ?s)     │
│  MODIFY: partials/results/recommendation.html (tooltip ?s)      │
│  MODIFY: partials/global_settings.html (tooltip ?s, tax guide)  │
│  MODIFY: partials/option_fields/*.html ×6 (tooltip ?s)          │
│  MODIFY: static/style.css (tooltip, tab, period table styles)   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Feature Integration Patterns

### Feature 1: Dark Mode

**What:** `prefers-color-scheme` auto-detection — browser picks light or dark without user action.

**Integration point:** `base.html` only.

**Mechanism:** Pico CSS v2 includes built-in `@media (prefers-color-scheme: dark)` rules that activate dark styles automatically when no explicit `data-theme` attribute is present on `<html>`. The current `data-theme="light"` hardcode blocks this. Removing it is the entire change.

**SVG chart concern:** Server-rendered SVGs in `charts.py` use hardcoded hex colors (`#2563eb`, `#dc2626`, `#059669`, `#d97706`) as inline `fill`/`stroke` attributes. These do not inherit CSS variables and will not change in dark mode.

**SVG fix decision:** Accept chart colors as static for v1.1. The chosen palette (blue/red/green/amber) provides readable contrast on both light and dark backgrounds. Switching to CSS custom property inheritance would require structural changes to chart templates and `charts.py` that are out of scope. Document as known limitation.

**New component:** None.
**Modified:** `base.html` (one attribute deletion on `<html>`).

---

### Feature 2: Input and Output Tooltips

**What:** `?` icon buttons next to form field labels and result term labels, showing explanatory popover text.

**Mechanism:** HTML Popover API — `popover` attribute on a `<div>` + `popovertarget` on a `<button>`. Browser provides: open/close toggle, Escape key dismiss, `aria-expanded` updates, focus management. Chrome 114+, Edge 114+, Safari 17+. No JS required for basic operation.

**Pattern per tooltip (repeated across templates):**
```html
<label for="field-id">
  Annual Interest Rate (APR)
  <button type="button"
          popovertarget="tip-apr-{{ opt.idx }}"
          class="tooltip-trigger"
          aria-label="What is APR?">?</button>
</label>
<div id="tip-apr-{{ opt.idx }}"
     popover
     class="tooltip-popover">
  The annual percentage rate represents the yearly cost of the loan
  as a percentage of the principal. Lower APR means less interest paid.
</div>
```

**Tooltip content:** Static strings in templates. No server-side data needed.

**CSS:** `.tooltip-trigger` (small inline `?` button, sized to not disrupt label line height) and `.tooltip-popover` (card with max-width, some padding, border). CSS Anchor Positioning for precise placement has incomplete browser support; use `position: fixed` with a reasonable offset as the positioning strategy for v1.1.

**Where to add input tooltips:**
- `partials/option_fields/*.html` — each field label (APR, term, down payment, etc.)
- `partials/global_settings.html` — return rate, inflation rate, tax rate

**Where to add output tooltips:**
- `partials/results/breakdown_table.html` — row labels: "Opportunity Cost", "Inflation Adjustment", "Tax Savings", "True Total Cost"
- `partials/results/recommendation.html` — any technical terms in explanatory text

**New component:** None (uses native browser API). Add CSS rules to `style.css`.
**Modified:** All `option_fields/*.html` (6 files), `global_settings.html`, `results/breakdown_table.html`, `results/recommendation.html`, `style.css`.

---

### Feature 3: Comma-Normalized Number Inputs

**What:** Display monetary inputs with thousand-separator commas (e.g., `25,000`) for readability; strip commas server-side before Decimal parsing.

**Two-part implementation:**

**Part A — Server-side stripping in `forms.py` (required, handles JS-disabled case):**

The `_try_decimal()` function currently does:
```python
return Decimal(value.strip())
```

Change to:
```python
return Decimal(value.strip().replace(",", ""))
```

Apply the same `.replace(",", "")` in `_to_money()` and anywhere raw strings are passed to `Decimal()` in `build_domain_objects`. This makes the server accept comma-formatted values regardless of whether JS is present.

**Part B — Client-side cosmetic formatting (small JS, UX improvement):**

~20 lines that:
- On `blur`: format the value with `Number.toLocaleString('en-US')` for display
- On `focus`: strip commas so cursor position and editing work correctly

Attach via a `data-money-input` attribute on target inputs. Zero interaction with financial logic — purely cosmetic.

**Repopulation after form errors:** `extract_form_data` returns raw strings as-is (including commas if user typed them). Server-side stripping at parse time handles this correctly — no template change needed.

**Affected inputs:** `purchase_price`, `down_payment`, `cash_back_amount`, `discounted_price` across all option field templates.

**New component:** `static/js/comma-format.js` or small inline `<script>` in `base.html`.
**Modified:** `forms.py` (`_try_decimal`, `_to_money`), `index.html` (purchase_price input), option field templates with monetary inputs.

---

### Feature 4: US Tax Rate Guidance

**What:** Help users select their marginal tax rate when enabling the tax implication setting.

**Integration point:** `partials/global_settings.html` only, near the existing tax rate input.

**Recommended pattern:** A `?` tooltip (same Popover API mechanism as Feature 2) that contains a compact reference table of approximate current US marginal federal income tax brackets (single filer / married filing jointly). The user reads it, picks their bracket, and types the rate manually.

A full interactive selector (user selects income range, bracket auto-fills) requires JS and is out of scope for v1.1. Static reference content is sufficient.

**New component:** None.
**Modified:** `partials/global_settings.html` (add tooltip near tax rate field with bracket reference table inside popover content).

---

### Feature 5: JSON Export / Import

**What:** Export current form inputs as a downloadable JSON file; import a previously saved JSON to restore the form state.

**Architecture decision:** Both operations are Flask routes. Export: server serializes form data and returns a download response. Import: server parses uploaded file and re-renders the index page with pre-populated values. This is consistent with the SSR approach — no client-side JSON manipulation.

#### Export Flow

```
User clicks Export button
    ↓
POST /export (plain form submit, no hx-* attributes)
    ↓
routes.export_config():
    extract_form_data(request.form)  →  dict
    json.dumps(dict, default=str)    →  JSON string
    make_response(json_str)
    set Content-Type: application/json
    set Content-Disposition: attachment; filename=fathom-config.json
    ↓
Browser triggers file download
```

**Critical constraint:** HTMX intercepts POST requests and expects an HTML response. An HTMX request to `/export` would silently discard the JSON download. The export button must be a plain `<form method="post" action="/export">` with no `hx-*` attributes. A standard form submit navigates the browser to the response, which triggers a file download rather than a page change when `Content-Disposition: attachment` is set.

**New route:**
```python
@bp.route("/export", methods=["POST"])
def export_config() -> Response:
    parsed = extract_form_data(request.form)
    json_str = json.dumps(parsed, default=str, indent=2)
    response = make_response(json_str)
    response.headers["Content-Type"] = "application/json"
    response.headers["Content-Disposition"] = (
        "attachment; filename=fathom-config.json"
    )
    return response
```

#### Import Flow

```
User selects JSON file via <input type="file">
    ↓
POST /import (multipart/form-data)
    ↓
routes.import_config():
    read uploaded file
    json.loads(content)            →  dict
    validate structure             →  option count 2-4, known types
    build template context         →  same shape as index route
    render_template("index.html", **ctx)
    ↓
Full page render with form pre-populated from imported data
(if malformed: render index.html with import_error in context)
```

**Validation on import:** Check for required top-level keys (`purchase_price`, `options`, `settings`), option count 2-4, known `type` values in each option. Do NOT run financial validation at import time — submit validation fires naturally when the user clicks Compare.

**JSON schema** (same structure as `extract_form_data` output):
```json
{
  "purchase_price": "25000",
  "options": [
    {"type": "cash", "label": "Pay in Full"},
    {"type": "traditional_loan", "label": "Loan", "apr": "5.99", "term_months": "60"}
  ],
  "settings": {
    "return_preset": "0.07",
    "return_rate_custom": "",
    "inflation_enabled": false,
    "inflation_rate": "3",
    "tax_enabled": false,
    "tax_rate": "22"
  }
}
```

**New components:** Routes `export_config()` and `import_config()` in `routes.py`, new partial `partials/export_import.html` containing the export button form and import file input form.
**Modified:** `routes.py` (two new routes), `index.html` (include export_import partial).

---

### Feature 6: Detailed Per-Option Period-by-Period Cost Breakdown Table

**What:** Per-option month-by-month view of payment, interest, principal, balance, and cumulative cost — with tab switching between options, column toggles, and a side-by-side compare tab.

**This is the most architecturally significant feature.** All data is already computed. The work is data reshaping and template implementation.

#### Data Available (No Engine Changes Needed)

`OptionResult.monthly_data` is a `list[MonthlyDataPoint]` with: `month`, `payment`, `interest_portion`, `principal_portion`, `remaining_balance`, `cumulative_cost`. This is fully populated by the engine for all option types.

For promo options, `PromoResult` contains both `paid_on_time.monthly_data` and `not_paid_on_time.monthly_data`.

`investment_balance` is always `Decimal(0)` (opportunity cost is computed as a total, not tracked monthly). This field is not worth showing in the period table.

#### New Data Preparation in `results.py`

Add `build_period_table_data(options_data)` and call it from `analyze_results()`:

```python
def build_period_table_data(options_data: list[dict]) -> dict:
    """Reshape monthly_data into template-ready period rows per option."""
    period_data: dict[str, list[dict]] = {}
    for opt in options_data:
        name = opt["name"]
        result = opt["result"]  # primary OptionResult
        period_data[name] = [
            {
                "month": dp.month,
                "payment": dp.payment,
                "interest": dp.interest_portion,
                "principal": dp.principal_portion,
                "balance": dp.remaining_balance,
                "cumulative": dp.cumulative_cost,
            }
            for dp in result.monthly_data
        ]
        if opt.get("is_promo") and "not_paid_result" in opt:
            not_paid_name = f"{name} (if not paid on time)"
            period_data[not_paid_name] = [
                {
                    "month": dp.month,
                    "payment": dp.payment,
                    "interest": dp.interest_portion,
                    "principal": dp.principal_portion,
                    "balance": dp.remaining_balance,
                    "cumulative": dp.cumulative_cost,
                }
                for dp in opt["not_paid_result"].monthly_data
            ]
    return period_data
```

Add `"period_table": build_period_table_data(options_data)` to the dict returned by `analyze_results()`. This flows through `ctx["display"]["period_table"]` with no route changes needed.

#### Tab Interactivity Decision

**Option A: Pure CSS tabs** — `:checked` + sibling combinator. Zero JS.
- Works for simple tabs; becomes fragile with column toggles layered on top.

**Option B: HTMX HATEOAS tabs** — tab click fetches server endpoint returning full updated tab set.
- Unnecessary network round-trips; all data is already rendered. Adds routing complexity for no benefit.

**Option C: Minimal inline JS tab switching** — ~30 lines toggling CSS classes on tab buttons and `tabpanel` divs.
- Instant switching, clean ARIA management, consistent with how index.html already uses inline `<script>`.
- The "no client-side logic" constraint covers financial calculations, not UI presentation state. Tab visibility is UI state.

**Recommendation: Option C for tabs + CSS-only column toggles.**

#### Column Toggle Mechanism

Hidden `<input type="checkbox">` controls above the table + CSS sibling combinator:

```html
<div class="col-toggles">
  <input type="checkbox" id="show-interest" class="col-toggle" checked>
  <label for="show-interest">Interest</label>
  <input type="checkbox" id="show-principal" class="col-toggle" checked>
  <label for="show-principal">Principal</label>
  ...
</div>

<!-- Each .period-table is a sibling of the toggles -->
<table class="period-table">
  <thead>
    <tr>
      <th>Month</th>
      <th class="col-interest">Interest</th>
      <th class="col-principal">Principal</th>
      ...
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1</td>
      <td class="col-interest">...</td>
      <td class="col-principal">...</td>
      ...
    </tr>
  </tbody>
</table>
```

CSS rule:
```css
#show-interest:not(:checked) ~ .tab-panels .col-interest { display: none; }
```

This is CSS-only, no JS, fully accessible, degrades gracefully.

#### New Template: `partials/results/period_table.html`

Structural skeleton:

```html
<section class="period-breakdown" aria-label="Detailed Period Breakdown">
  <!-- Column toggles (CSS-driven, outside tab panels) -->
  <div class="col-toggles" role="group" aria-label="Show/hide columns">
    <input type="checkbox" id="show-col-interest" checked>
    <label for="show-col-interest">Interest</label>
    ...
  </div>

  <!-- Tab buttons (JS manages active state + aria-selected) -->
  <div role="tablist" class="period-tabs">
    {% for opt in display.options_data %}
    <button role="tab"
            aria-selected="{{ 'true' if loop.first else 'false' }}"
            aria-controls="period-panel-{{ loop.index0 }}"
            class="tab-btn {{ 'active' if loop.first }}"
            data-tab="period-panel-{{ loop.index0 }}">
      {{ opt.name }}
    </button>
    {% endfor %}
    <button role="tab" aria-selected="false"
            aria-controls="period-panel-compare"
            class="tab-btn" data-tab="period-panel-compare">
      Compare All
    </button>
  </div>

  <!-- Per-option panels -->
  {% for opt in display.options_data %}
  <div role="tabpanel"
       id="period-panel-{{ loop.index0 }}"
       class="tab-panel {{ '' if loop.first else 'hidden' }}">
    <table class="period-table">
      <caption class="visually-hidden">
        Period-by-period breakdown for {{ opt.name }}
      </caption>
      <thead>
        <tr>
          <th>Month</th>
          <th class="col-payment">Payment</th>
          <th class="col-interest">Interest</th>
          <th class="col-principal">Principal</th>
          <th class="col-balance">Balance</th>
          <th>Cumulative</th>
        </tr>
      </thead>
      <tbody>
        {% for row in display.period_table[opt.name] %}
        <tr>
          <td>{{ row.month }}</td>
          <td class="col-payment">${{ "{:,.2f}".format(row.payment) }}</td>
          <td class="col-interest">${{ "{:,.2f}".format(row.interest) }}</td>
          <td class="col-principal">${{ "{:,.2f}".format(row.principal) }}</td>
          <td class="col-balance">${{ "{:,.2f}".format(row.balance) }}</td>
          <td>${{ "{:,.2f}".format(row.cumulative) }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% endfor %}

  <!-- Compare panel: month vs cumulative cost per option -->
  <div role="tabpanel" id="period-panel-compare" class="tab-panel hidden">
    <table class="period-table period-compare">
      <caption class="visually-hidden">Side-by-side cumulative cost comparison</caption>
      <thead>
        <tr>
          <th>Month</th>
          {% for opt in display.options_data %}
          <th>{{ opt.name }}</th>
          {% endfor %}
        </tr>
      </thead>
      <tbody>
        {% for i in range(display.comparison_period_months) %}
        <tr>
          <td>{{ i + 1 }}</td>
          {% for opt in display.options_data %}
          <td>${{ "{:,.2f}".format(display.period_table[opt.name][i].cumulative) }}</td>
          {% endfor %}
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</section>
```

**Integration in `partials/results.html`:** Add after the existing breakdown table section:

```html
{% if display.period_table is defined %}
<section class="period-breakdown-section" aria-label="Period-by-Period Breakdown">
  <h2>Period-by-Period Breakdown</h2>
  {% include "partials/results/period_table.html" %}
</section>
{% endif %}
```

**Performance note:** Comparison periods up to 360 months (30-year loan) = up to ~1,440 table rows across 4 options. This is a large DOM but renders in well under 100ms server-side. Client-side the DOM size is notable but acceptable for a desktop-class tool. If performance is a concern, consider lazy-rendering the period table only when the tab is activated (requires JS) — that's a v1.2 optimization.

**New components:** `partials/results/period_table.html`, `build_period_table_data()` in `results.py`, tab switching JS (~30 lines in `base.html` or `static/js/tabs.js`).
**Modified:** `results.py` (`analyze_results` return dict), `partials/results.html`.

---

## Data Flow Summary

### Unchanged Calculation Flow

```
POST /compare
  → parse_form_data(request.form)       → FormInput  [commas stripped v1.1]
  → build_domain_objects(form_input)    → [FinancingOption], GlobalSettings
  → compare(options, settings)          → ComparisonResult  [unchanged]
  → analyze_results(comparison, opts)   → display dict  [+period_table key v1.1]
  → prepare_charts(comparison, ...)     → charts dict  [unchanged]
  → render_template(...)                [period_table.html included v1.1]
```

### New Export Flow

```
POST /export  (plain form, no hx-*)
  → extract_form_data(request.form)     → dict (no validation)
  → json.dumps(dict, default=str)       → JSON string
  → make_response + Content-Disposition: attachment
  → browser file download
```

### New Import Flow

```
POST /import  (multipart/form-data)
  → request.files["config"].read()
  → json.loads(content)                 → dict
  → validate structure                  → error if malformed
  → build ctx (same shape as index())   → template context
  → render_template("index.html", **ctx)
```

---

## New vs Modified Component Summary

### New Components

| Component | Type | Description |
|-----------|------|-------------|
| `routes.export_config()` | Python | POST /export — JSON download response |
| `routes.import_config()` | Python | POST /import — parse JSON, render pre-populated form |
| `results.build_period_table_data()` | Python | Extract monthly_data into template rows |
| `partials/export_import.html` | Jinja2 | Export button + import file input |
| `partials/results/period_table.html` | Jinja2 | Tabbed period-by-period breakdown table |
| Tooltip CSS (in `style.css`) | CSS | `.tooltip-trigger`, `.tooltip-popover` |
| Tab switching JS | JS (~30 lines) | ARIA-aware tab show/hide |
| Comma formatting JS | JS (~20 lines) | Input blur/focus display formatting |

### Modified Components

| Component | Change | Details |
|-----------|--------|---------|
| `base.html` | Remove attribute | Delete `data-theme="light"` from `<html>` |
| `forms.py` | Logic change | `_try_decimal` + `_to_money` strip commas |
| `results.py` | Additive | `analyze_results` adds `period_table` key |
| `routes.py` | Additive | Two new routes + `json`/`make_response` imports |
| `index.html` | Additive | Include `partials/export_import.html` |
| `partials/results.html` | Additive | Include period_table section |
| `partials/results/breakdown_table.html` | Additive | `?` tooltip buttons on row labels |
| `partials/results/recommendation.html` | Additive | `?` tooltip buttons on key terms |
| `partials/global_settings.html` | Additive | Tooltip buttons + tax bracket reference |
| `partials/option_fields/*.html` ×6 | Additive | Tooltip `?` buttons per field |
| `static/style.css` | Additive | Tooltip, tab, period table, column toggle CSS |

---

## Recommended Build Order

Dependencies drive this order. Each phase is testable in isolation.

**Phase 1: Dark Mode** (~30 min, zero risk)
Delete `data-theme="light"` from `base.html`. Verify in Playwright with `prefers-color-scheme: dark` media emulation. No other files change. No possible regressions.

**Phase 2: Comma-Normalized Inputs** (~2 hours, low risk)
Modify `_try_decimal` and `_to_money` in `forms.py` first (server-side; all tests pass with existing values, new tests verify comma-formatted strings also parse). Add cosmetic JS second. This unblocks cleaner input UX for all subsequent manual testing.

**Phase 3: Input Tooltips** (~3 hours, no deps)
Add `?` tooltip buttons to all `option_fields/*.html` and `global_settings.html` including tax bracket guidance. Add Popover API CSS to `style.css`. Playwright verifies popovers open/close and are keyboard-accessible.

**Phase 4: Output Tooltips** (~2 hours, depends on Phase 3 CSS)
Add `?` buttons to `breakdown_table.html` and `recommendation.html` reusing CSS from Phase 3.

**Phase 5: JSON Export / Import** (~4 hours, depends on Phase 2)
Export first (simpler — no UI rendering). Import second — depends on comma stripping being in place so imported values with commas are handled correctly at parse time. Playwright tests verify round-trip: fill form, export, import, verify pre-populated values match.

**Phase 6: Period-by-Period Table** (~5 hours, no hard deps but most complex)
Add `build_period_table_data()` to `results.py`, update `analyze_results()`, create `period_table.html`, add tab JS. Do last so any regressions are isolated to this feature. Playwright tests verify tab switching, column toggles, and accessible ARIA attributes.

---

## Constraints Verification

| Constraint | Status | Preserved By |
|------------|--------|--------------|
| All financial math server-side | Intact | No calculation logic in JS; JS handles only display cosmetics and tab visibility |
| Stateless / no persistent storage | Intact | Export/import is file-in/file-out; no session state |
| Single-process deployment | Intact | No new external services or processes |
| WCAG 2.1 AA | Intact | Popover API provides native keyboard/ARIA; tabs use `role="tab"` + `role="tabpanel"` + `aria-selected`; period table has `<caption>` |
| 300ms render target | Intact | No new calculations; `build_period_table_data` is O(n × months) data reshape only, ~1ms |

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Duplicating Decimal Parsing in JS

**What people do:** Format numbers client-side and submit the formatted string, trusting JS to get precision right.
**Why it's wrong:** JS uses IEEE 754 floats. Any financial logic in JS becomes a second source of truth that can diverge from server-side Decimal.
**Do this instead:** Strip commas server-side in `_try_decimal`/`_to_money`. JS handles only cosmetic display.

### Anti-Pattern 2: HTMX-driven Tab Switching for Period Table

**What people do:** Use `hx-get` so each tab switch fetches the server.
**Why it's wrong:** Period table data is already in the DOM at render time. Round-trips add latency with no benefit. HTMX is right for operations that need server calculation; tab visibility does not.
**Do this instead:** Inline JS tab toggling. All panels rendered on initial response; JS shows/hides them.

### Anti-Pattern 3: Adding Display State to Domain Models

**What people do:** Add formatted strings or CSS class names to `MonthlyDataPoint` for template convenience.
**Why it's wrong:** `MonthlyDataPoint` is consumed by the calculation engine. Adding display concerns couples presentation to domain logic.
**Do this instead:** `build_period_table_data()` in `results.py` reshapes domain data into a separate display dict.

### Anti-Pattern 4: Client-Side JSON Export (Blob API)

**What people do:** Serialize form data in JS to a Blob and trigger a download without involving the server.
**Why it's wrong:** Requires serializing form state in JS, which duplicates form parsing logic and can diverge from server-side parsing. Also bypasses validation/normalization.
**Do this instead:** POST to `/export` endpoint. Flask serializes via `extract_form_data` (same code path as all other form handling) and returns a `Content-Disposition: attachment` response.

### Anti-Pattern 5: Server-Side Tax Bracket Data

**What people do:** Add a `/tax-brackets` endpoint returning current year bracket data.
**Why it's wrong:** Tax law changes annually. Server maintenance burden for reference-only data. Tempts coupling calculation logic to bracket lookup.
**Do this instead:** Static HTML table of approximate current brackets embedded in a tooltip popover. The user enters their own rate — the table is reference, not input.

---

## Sources

- [Pico CSS Color Schemes documentation](https://picocss.com/docs/color-schemes) — `data-theme` behavior, auto dark mode (HIGH confidence, official docs)
- [HTMX HATEOAS tab example](https://htmx.org/examples/tabs-hateoas/) — server-rendered tab pattern (HIGH confidence, official docs)
- [MDN Popover API](https://developer.mozilla.org/en-US/docs/Web/API/Popover_API/Using) — browser support and accessible pattern (HIGH confidence, official docs)
- [Frontend Masters: Popover API for tooltips](https://frontendmasters.com/blog/using-the-popover-api-for-html-tooltips/) — tooltip implementation pattern (MEDIUM confidence, community source)
- Flask `make_response` + `Content-Disposition` — standard Flask pattern, confirmed via Flask documentation search (HIGH confidence)
- Fathom v1.0 source code — all integration points verified by reading actual source (`routes.py`, `forms.py`, `results.py`, `engine.py`, `models.py`, all templates) (HIGH confidence, primary source)

---

*Architecture research for: Fathom v1.1 — tooltips, period table, export/import, comma inputs, dark mode*
*Researched: 2026-03-13*
