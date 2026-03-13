# Technology Stack

**Project:** Fathom -- Financing Options Analyzer
**Researched:** 2026-03-10 (v1.0) / 2026-03-13 (v1.1 additions)
**Overall confidence:** HIGH

---

## v1.1 Feature Additions (NEW — researched 2026-03-13)

This section documents only what is NEW for v1.1. The existing v1.0 stack below
is unchanged and already validated.

### Key Finding: No New Dependencies Required

All seven v1.1 features are implementable with the existing stack. No new Python
packages, no new vendored JS files, no new CSS frameworks.

---

### Feature: Dark Mode (`prefers-color-scheme`)

**Decision: Remove `data-theme="light"` from `<html>` — zero new dependencies.**

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
   to work in both modes — no change needed.

**No JS toggle needed.** A manual theme toggle button is a separate UX feature.
`prefers-color-scheme` CSS support is the stated v1.1 requirement.

Source: [Pico CSS Color Schemes](https://picocss.com/docs/color-schemes) — HIGH confidence.

---

### Feature: Tooltips (`?` icon popovers)

**Decision: HTML `popover` attribute + `popovertarget` button — no JS, no library.**

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
`interestfor` attribute is not yet Baseline — it lacks Firefox/Safari production
support as of March 2026. The `popovertarget` click-toggle works everywhere.

**Do NOT use CSS-only `:hover` tooltips.** Pure CSS hover tooltips fail WCAG
1.4.13 (Content on Hover or Focus) — the content is not dismissible, hoverable,
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
- [Popover API — MDN](https://developer.mozilla.org/en-US/docs/Web/API/Popover_API) — HIGH confidence
- [Popover Baseline announcement](https://web.dev/blog/popover-baseline) — HIGH confidence
- [WCAG 1.4.13](https://www.w3.org/WAI/WCAG21/Understanding/content-on-hover-or-focus.html) — HIGH confidence
- [CSS Anchor Positioning support](https://caniuse.com/css-anchor-positioning) — 82%, not Baseline — HIGH confidence

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
(Flask route + Jinja2 template) triggered by HTMX — consistent with existing
results partials. Flask computes per-period data server-side; Jinja2 renders the
table HTML; HTMX swaps it into the results area. Tab switching is client-side
after swap.

The JS must re-initialize after HTMX partial injection:

```javascript
// static/tabs.js — W3C tab pattern, ~50 lines
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
- [W3C APG Tabs Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/) — HIGH confidence
- [ARIA tabpanel role — MDN](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Roles/tabpanel_role) — HIGH confidence

---

### Feature: JSON Export / Import

**Decision: Server-side Flask download route for export; HTMX file upload for import. No library.**

**Export flow:**
1. "Export JSON" is an `<a>` or form POST to `/export`.
2. Flask receives current form field values in the POST body.
3. Route validates through existing Pydantic models, calls `model_dump()`, then
   returns `flask.Response(json.dumps(data, indent=2), mimetype='application/json',
   headers={'Content-Disposition': 'attachment; filename="fathom-scenario.json"'})`.
4. Browser triggers file download — no client-side Blob/URL dance required.

This is preferable to a client-side Blob export because Pydantic validation
happens before export (exported data is always clean), and it requires zero JS.

**Import flow:**
1. `<input type="file" accept=".json">` with `hx-trigger="change"` and
   `hx-encoding="multipart/form-data"` on the enclosing form.
2. HTMX POSTs the file to `/import`.
3. Flask reads the uploaded JSON via `request.files`, validates with Pydantic,
   returns the form partial pre-populated with imported values.
4. HTMX swaps the form partial — same mechanism as existing live updates.

**No new Python library needed.** `json` (stdlib) + existing Pydantic models +
Flask's `request.files` covers everything.

Include a `version` field in the export payload for forward compatibility. Use
`pydantic_model.model_json_schema()` to document the schema alongside the code.

Sources:
- [Flask JSON/JS Patterns](https://flask.palletsprojects.com/en/stable/patterns/javascript/) — HIGH confidence

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

`Intl.NumberFormat` is a native browser API — Baseline Widely Available since
2018. Zero bytes added to the page.

Server-side: add `.replace(',', '')` before `Decimal()` conversion in the
existing form parser (`forms.py`). One-line change per numeric field. HTMX
POSTs the raw comma-formatted string; server strips commas transparently.

**Do NOT add Cleave.js, IMask, or AutoNumeric.** These libraries add 20-40 KB
for a feature solved in 8 lines of native JS.

Source: [Intl.NumberFormat — MDN](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat) — HIGH confidence.

---

### Feature: US Tax Rate Guidance

**Decision: Hardcode 2026 IRS brackets as a Python constant. Zero new dependencies.**

The feature helps users identify their marginal tax bracket to fill in the
"marginal tax rate" input. This is display/guidance only — not part of
calculations.

2026 federal marginal rates (confirmed by IRS, same 7 brackets since TCJA):
`10%, 12%, 22%, 24%, 32%, 35%, 37%`

Rates are identical for 2025 and 2026; only income thresholds adjust for
inflation annually. Thresholds differ by filing status (single, married filing
jointly, head of household).

Implementation: a Python dict constant in a `constants.py` or directly in the
relevant route context. Rendered server-side as a `<details>`/`<summary>`
disclosure widget alongside the tax rate input field — no JS needed.

**Do NOT fetch live IRS data.** The project is stateless with no external
dependencies. Brackets change once per year at most. Hardcode and add a comment
noting the source URL and tax year.

**Do NOT add a tax calculation library.** The guidance feature provides bracket
reference for the user, not a tax calculation. Existing `tax.py` handles the
financial math.

Sources:
- [IRS Federal Tax Rates and Brackets](https://www.irs.gov/filing/federal-income-tax-rates-and-brackets) — HIGH confidence
- [Tax Foundation 2026 Brackets](https://taxfoundation.org/data/all/federal/2026-tax-brackets/) — HIGH confidence

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
| Tooltip popovers | No HTMX involvement — pure HTML `popover` attribute behavior |
| Breakdown table tabs | JS re-initializes on `htmx:afterSwap` event |
| JSON import | Needs `hx-encoding="multipart/form-data"` on the file upload form |
| Comma inputs | HTMX POSTs comma-formatted strings; server strips them — no special handling |
| Dark mode | No HTMX involvement — pure CSS `@media` |
| Tax guidance | Static content in form template — no HTMX involvement |

---

### v1.1 Alternatives Rejected

| Recommended | Alternative | Why Rejected |
|-------------|-------------|--------------|
| Remove `data-theme="light"` | Add JS theme toggle | Requirement is CSS `prefers-color-scheme`; a toggle button is a separate UX feature |
| `popovertarget` click-toggle popover | `interestfor` + `popover=hint` hover | Not Baseline — missing Firefox/Safari production support (March 2026) |
| `popovertarget` click-toggle popover | CSS-only `:hover` tooltip | Fails WCAG 1.4.13 — not dismissible, not hoverable, not persistent |
| `position: fixed` popover placement | CSS Anchor Positioning | 82% global support; Firefox 147+ required; not Baseline Widely Available |
| Vanilla JS tab pattern (~50 lines) | Van11y / Tabby library | Adds vendor file for a feature simple enough to write inline |
| Vanilla JS tab pattern (~50 lines) | CSS radio-button hack | No `aria-selected`, no arrow-key navigation — fails WCAG |
| Flask download route for JSON export | Client-side Blob + `URL.createObjectURL` | Flask route runs Pydantic validation before export; no JS needed |
| `Intl.NumberFormat` (native) | Cleave.js / IMask / AutoNumeric | Libraries add 20-40 KB for an 8-line feature |
| Hardcoded tax bracket data | External IRS API | Project is stateless; brackets change once/year; no external dependency |

---

### v1.1 What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `interestfor` attribute | Not Baseline — missing Firefox/Safari support (March 2026) | `popovertarget` click-toggle |
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

## What NOT to Use (v1.0 + v1.1)

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
| `interestfor` attribute | Not Baseline — no Firefox/Safari production support (March 2026) |
| CSS Anchor Positioning | 82% global support, not Baseline Widely Available |
| Cleave.js / IMask / AutoNumeric | 8-line feature; no library needed |
| Any second CSS framework | Conflicts with Pico CSS variable system |

## Sources

### v1.1 Sources

- [Pico CSS Color Schemes](https://picocss.com/docs/color-schemes) — dark mode mechanism — HIGH confidence
- [Popover API — MDN](https://developer.mozilla.org/en-US/docs/Web/API/Popover_API) — `popovertarget` usage — HIGH confidence
- [Popover Baseline Widely Available](https://web.dev/blog/popover-baseline) — April 2025 — HIGH confidence
- [CSS Anchor Positioning — Can I Use](https://caniuse.com/css-anchor-positioning) — 82% support, not Baseline — HIGH confidence
- [WCAG 1.4.13 Content on Hover or Focus](https://www.w3.org/WAI/WCAG21/Understanding/content-on-hover-or-focus.html) — tooltip WCAG requirements — HIGH confidence
- [W3C APG Tabs Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/) — tab ARIA requirements — HIGH confidence
- [Intl.NumberFormat — MDN](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat) — comma formatting — HIGH confidence
- [Flask JSON/JS Patterns](https://flask.palletsprojects.com/en/stable/patterns/javascript/) — export route pattern — HIGH confidence
- [IRS Federal Tax Rates and Brackets](https://www.irs.gov/filing/federal-income-tax-rates-and-brackets) — 2026 rates — HIGH confidence
- [Tax Foundation 2026 Brackets](https://taxfoundation.org/data/all/federal/2026-tax-brackets/) — bracket data verification — HIGH confidence

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
