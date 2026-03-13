# Feature Research

**Domain:** Financing comparison calculator — v1.1 enhancements (tooltips, cost breakdown tables, JSON export/import, number formatting, tax guidance, dark mode)
**Researched:** 2026-03-13
**Confidence:** HIGH (native browser APIs, well-established patterns, Pico CSS dark mode confirmed via official docs)

## Context

This is a subsequent milestone research file. v1.0 already ships: single-page input form, 6 option types, True Total Cost engine, summary recommendation, cost breakdown table, SVG charts, HTMX live updates, WCAG 2.1 AA, responsive layout.

The seven v1.1 features are not "should we build these" questions — they are scoped and committed in PROJECT.md. This file answers: **what does each feature expect, what is table stakes vs differentiator, how complex, and what depends on what.**

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features that users of financial tools assume exist. Missing these makes v1.1 feel incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Input tooltips (`?` icon popovers) | Any financial form with jargon (APR, opportunity cost, marginal rate) must explain its terms inline. Users abandon forms when confused by unfamiliar fields. Intuit, Bankrate, and SmartAsset all do this. | LOW | Static content, no server round-trip needed. Pico CSS + native Popover API (Baseline Widely Available since April 2025). One `?` button per field, `popover` attribute on `<div>`. Pure HTML/CSS, no JS required. |
| Output tooltips (result term explanations) | "Opportunity cost" and "True Total Cost" are novel terms. Without inline explanations, users distrust the numbers. The recommendation card and breakdown table are meaningless if terms are opaque. | LOW | Same mechanism as input tooltips. Each row label in the breakdown table and each metric in the summary card gets a `?` trigger. Static content, inline in Jinja templates. |
| Comma-normalized number inputs | Entering "18000" instead of "18,000" is error-prone at amounts like $18,000 or $245,000. Users expect to type or paste formatted numbers. Type `<input type="number">` rejects commas — must use `type="text"` with stripping before submission. | MEDIUM | `type="text"` with `inputmode="numeric"` and `pattern`. Format on blur via minimal JS. Strip commas server-side in Pydantic validators before parsing to Decimal. Active area of form UX concern (see sources). |
| Dark mode (`prefers-color-scheme`) | Dark mode is now a baseline user expectation (2025+ web). Using a system that doesn't respect OS dark mode preference feels dated. Pico CSS ships with built-in dark mode support out of the box — this is essentially free. | LOW | Pico CSS auto-activates dark mode via `prefers-color-scheme: dark` with no JS required. Custom CSS vars declared twice (media query + `[data-theme="dark"]`). SVG chart colors need explicit dark-mode overrides. No manual toggle required for v1.1 — OS preference is sufficient. |

### Differentiators (Competitive Advantage)

Features that make v1.1 more useful than generic calculators.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Detailed cost breakdown table (period-by-period, tabs, column toggles, compare view) | No mainstream consumer financing calculator shows period-by-period True Total Cost decomposition across multiple options. This is uniquely transparent — "show your work" for complex financial comparisons. The existing v1.0 summary table is one row per cost factor; this is one row per period. | HIGH | Per-period rows: each month/year shows payments, opportunity cost, running total, inflation adjustment, tax savings. Tabs: per-option detail + side-by-side compare. Column toggles: show/hide individual cost factors. Server-rendered HTML table from Python. HTMX can lazy-load detailed table on demand. Must remain accessible (proper `<thead>`, `scope` attributes, `aria-label`). |
| JSON export/import | Lets users save and restore scenarios. Critical for "what if I renegotiated to 3.9%?" iteration. No competitor supports this. Supports self-hosted users who want auditability. | MEDIUM | Export: server endpoint returns JSON of current form state; browser downloads via `Content-Disposition: attachment`. Import: `<input type="file" accept=".json">`, POST to parse endpoint, server re-populates form via HTMX swap. Server validates uploaded JSON through same Pydantic models as form submission. No client-side state management needed. |
| US-centric tax rate guidance | Marginal tax rate is the single most confusing input for non-accountant users. Displaying the 2025 IRS brackets (10%, 12%, 22%, 24%, 32%, 35%, 37%) with income ranges inline turns an opaque field into a self-service lookup. SmartAsset and TurboTax do this as dedicated tools; embedding it inline is a UX win. | LOW-MEDIUM | Static data (2025 brackets from IRS). Expandable helper panel below the tax rate field, toggled by a "What's my bracket?" link/button. Shows filing status × income bracket table. No calculation — pure reference. Content lives in a Jinja partial, updated annually. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Manual dark/light mode toggle button | Users want explicit control; some prefer manual override over OS-level setting | Adds localStorage state, JavaScript toggle logic, and icon/button UI. For a utility tool used briefly, OS preference is sufficient. Toggle is deferred complexity for marginal UX gain. | Respect `prefers-color-scheme` only in v1.1. Add manual toggle in v1.2 if users request it. Use `[data-theme]` attribute pattern so toggle can be added without refactoring CSS. |
| Real-time comma formatting while typing | Feels polished; users see "18,000" as they type each digit | Reformatting on `keydown` creates cursor position bugs, breaks copy-paste, and breaks mobile numeric keyboards. Complex to implement correctly across browsers. | Format on `blur` only (when user leaves the field). This is the correct UX pattern — confirmed by form UX sources. Strip commas on server-side; display formatted value in repopulated form after HTMX swap. |
| Downloadable amortization schedule CSV/Excel | Power users ask for this; it's a feature every bank's loan page has | Out of scope per PROJECT.md. Full amortization schedule is "noise for a comparison tool." The period-by-period breakdown table in v1.1 covers the substantive need. CSV export adds format complexity. | The JSON export provides data portability. The detailed breakdown table provides period-level transparency. Both together satisfy the underlying need. |
| Client-side JSON parse/restore | Avoids server round-trip on import; feels more responsive | Creates two code paths for form validation (JS + Python). Violates Fathom's architecture constraint: all validation is server-side Python. State divergence bugs are worse than a small latency. | POST the uploaded JSON to a server endpoint, validate via Pydantic, return repopulated form HTML via HTMX swap. One code path. |
| Tax bracket auto-calculation from income | Users want to enter income and have the rate computed automatically | Tax calculation is complex (filing status, deductions, state taxes, AMT). Wrong auto-computed rate creates false confidence in results. IRS bracket tables change annually, requiring maintenance. | Show the bracket reference table and let the user pick their rate. One accurate manual selection beats one imprecise automatic calculation. |

---

## Feature Dependencies

```
[Comma-normalized inputs]
    └──requires──> [Pydantic validators strip commas before Decimal parse]
    └──enhances──> [All numeric inputs (purchase price, loan amount, rates)]

[Input tooltips]
    └──requires──> [Native Popover API] (Baseline Widely Available April 2025, no polyfill needed)
    └──enhances──> [All form fields with jargon]

[Output tooltips]
    └──requires──> [Same Popover API mechanism as input tooltips]
    └──enhances──> [Summary recommendation card] (already built)
    └──enhances──> [Cost breakdown table v1.0] (already built)
    └──enhances──> [Detailed breakdown table v1.1]

[Detailed cost breakdown table]
    └──requires──> [True Total Cost calculation engine] (already built)
    └──requires──> [Per-period cash flow series] (amortization.py already exists)
    └──enhances──> [Output tooltips] (column header tooltips explain cost factors)
    └──conflicts──> [Must not duplicate v1.0 summary breakdown table — tabs separate them]

[JSON export]
    └──requires──> [Pydantic models serialize cleanly to JSON] (Pydantic v2 .model_dump() works)
    └──independent of──> [JSON import] (can ship export without import)

[JSON import]
    └──requires──> [JSON export] (same schema must round-trip)
    └──requires──> [Pydantic model validation] (uploaded JSON validated through same models as form POST)
    └──requires──> [HTMX form repopulation endpoint]

[US tax rate guidance]
    └──enhances──> [Tax rate input field] (already built in global settings)
    └──requires──> [Static 2025 IRS bracket data] (hardcoded in template or Python constant)
    └──independent of──> [Inflation guidance, investment return rate guidance]

[Dark mode]
    └──requires──> [Pico CSS CSS variables audit] (identify all custom color vars overriding Pico defaults)
    └──requires──> [SVG chart color overrides] (chart.py colors must be dark-mode-aware)
    └──independent of──> [All other v1.1 features]
```

### Dependency Notes

- **Comma inputs require server-side stripping:** `type="text"` inputs with commas will break existing Pydantic `Decimal` field parsing. The comma-stripping must land before any feature that increases the chance of users pasting formatted numbers.
- **Detailed breakdown table requires per-period data:** `amortization.py` already calculates monthly cash flows (used for line chart). The per-period breakdown table reuses this data — it is not new calculation logic, just new rendering.
- **JSON import requires HTMX repopulation endpoint:** A new route is needed that accepts JSON, validates it, and returns the populated form HTML. This is a new server endpoint but follows the existing pattern.
- **Dark mode requires SVG color review:** The existing `charts.py` uses hardcoded hex colors. These need to either use CSS variables (if SVG supports them — they do for `fill` and `stroke`) or emit different colors when dark mode is detected server-side via `Sec-CH-Prefers-Color-Scheme` header (not universally supported). The safest approach is CSS variables in SVG `fill`/`stroke` attributes.
- **Output tooltips enhance, not replace:** The existing summary card and v1.0 breakdown table gain tooltip triggers. This is additive — no existing rendering logic changes.

---

## v1.1 Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority | Phase Suggestion |
|---------|------------|---------------------|----------|-----------------|
| Input tooltips | HIGH | LOW | P1 | Phase 1 — pure HTML/CSS, no risk |
| Output tooltips | HIGH | LOW | P1 | Phase 1 — same mechanism |
| Comma-normalized inputs | MEDIUM | MEDIUM | P1 | Phase 1 — unblocks accurate input for all users |
| US tax rate guidance | MEDIUM | LOW | P1 | Phase 1 — static content, simple toggle |
| Dark mode | MEDIUM | LOW-MEDIUM | P2 | Phase 2 — CSS audit required, SVG colors tricky |
| JSON export | MEDIUM | MEDIUM | P2 | Phase 2 — new endpoint, clean Pydantic serialization |
| JSON import | MEDIUM | MEDIUM | P2 | Phase 2 — depends on export schema being stable |
| Detailed breakdown table | HIGH | HIGH | P2 | Phase 3 — most complex, depends on data model clarity |

**Priority key:**
- P1: Must have for v1.1 launch — directly improves existing usability friction
- P2: Should have — adds new capability with moderate complexity

---

## Expected Behavior Detail

### Tooltips (Input + Output)

- Trigger: `?` icon button adjacent to field label or metric label
- Mechanism: HTML Popover API (`popover` attribute on `<div>`, `popovertarget` on `<button>`)
- Content: 1-3 sentences maximum. Explains the concept, not just restates the label.
- Positioning: Auto-positioned by browser; `popover` elements use the top layer
- Accessibility: `aria-label="Help for [field name]"` on trigger button; popover has `role` managed by Popover API
- Mobile: Tap to open, tap anywhere else to close (native Popover API behavior)
- No JS required for basic functionality; CSS-only show/hide via `:popover-open` pseudo-class
- Content lives in Jinja templates — easy to update without touching Python

### Comma-Normalized Inputs

- Input type: `type="text"` with `inputmode="numeric"` (shows numeric keyboard on mobile)
- Display: Show formatted value with commas (e.g., "18,000") after server repopulation
- On blur: JS formats display value with commas (minimal JS, ~10 lines)
- On server receipt: Pydantic pre-validator strips commas and non-numeric chars before Decimal parse
- Pattern attribute: `pattern="[\d,]*\.?\d*"` for browser-level hint
- What not to do: Do not use `type="number"` — browsers reject comma-formatted values

### Detailed Cost Breakdown Table

- Structure: Rows = periods (monthly or annually, user-selectable); Columns = cost factors per option
- Default view: Annual summary rows (less overwhelming than 60 monthly rows for a 5-year loan)
- Tab 1: Per-option detail (one table per option, with all cost factors as columns)
- Tab 2: Side-by-side compare (one column per option, rows = key cost factors summed by period)
- Column toggles: Checkboxes to show/hide individual cost factors (opportunity cost, inflation, tax savings, etc.)
- Row expansion: Click a year to expand to monthly detail (progressive disclosure)
- Server-rendered: Python generates HTML table; HTMX can lazy-load when user clicks "Detailed View" tab
- Accessibility: `<thead>` with `scope="col"`, row headers with `scope="row"`, `aria-label` on the section

### JSON Export

- Trigger: "Export JSON" button in form area
- Mechanism: GET or POST to `/export` endpoint; server serializes current form state via Pydantic `.model_dump()`; returns `Content-Disposition: attachment; filename="fathom-scenario.json"` with `application/json`
- Schema: Same Pydantic models used for form validation — no separate serialization format
- File name: `fathom-<timestamp>.json` for uniqueness

### JSON Import

- Trigger: File input `<input type="file" accept=".json">` + "Import" button
- Mechanism: POST to `/import` endpoint with multipart form; server reads file, validates JSON through Pydantic models, returns repopulated form HTML via HTMX `hx-swap="outerHTML"` on the form
- Error handling: Invalid JSON or schema mismatch returns inline error message (no page reload)
- Security: Validate file size limit (e.g., 64KB max); reject non-JSON MIME types

### US Tax Rate Guidance

- Trigger: "What's my bracket?" link/button below the marginal tax rate input
- Mechanism: Toggles a hidden `<details>`/`<summary>` or Popover containing the bracket table
- Content: 2025 IRS brackets table (10%–37%) for single and married filing jointly
- Interaction: User reads table, manually enters their rate — no auto-population
- Updates: Static data in a Jinja partial; update annually with new IRS brackets
- No external API, no dynamic calculation

### Dark Mode

- Mechanism: `@media (prefers-color-scheme: dark)` — OS preference only for v1.1
- Pico CSS: Auto-activates dark theme with built-in variables. Custom overrides follow Pico's `[data-theme="dark"]` pattern declared inside media query
- SVG charts: Use CSS custom properties (`--chart-color-1`, etc.) in `fill`/`stroke` attributes; define light and dark values in CSS
- Testing: Playwright MCP can emulate `prefers-color-scheme: dark` via `page.emulate_media()`

---

## Competitor Feature Analysis (v1.1 Scope)

| Feature | Bankrate/NerdWallet | TurboTax Tax Bracket Calc | Fathom v1.1 Approach |
|---------|---------------------|--------------------------|----------------------|
| Field tooltips | Yes — on most fields | Yes — inline help text | Yes — Popover API, static content in templates |
| Number formatting | Yes — commas displayed | Yes | Yes — text input + blur formatting + server stripping |
| Dark mode | Bankrate: No. NerdWallet: Yes | Yes | Yes — `prefers-color-scheme` via Pico CSS |
| JSON export/import | No | No | Yes — unique to Fathom |
| Tax bracket lookup | No (separate tools) | Yes — dedicated calculator | Yes — inline reference table (lighter than TurboTax) |
| Detailed amortization | Yes — full schedule per option | N/A | Yes — per-period breakdown with cost factor decomposition (unique: includes opportunity cost + inflation) |

---

## Sources

- [Tooltip and popover guidelines — Balsamiq](https://balsamiq.com/learn/ui-control-guidelines/tooltips-popovers/)
- [Tooltips — Intuit Content Design](https://contentdesign.intuit.com/product-and-ui/tooltips/)
- [Using the Popover API for HTML Tooltips — Frontend Masters](https://frontendmasters.com/blog/using-the-popover-api-for-html-tooltips/)
- [prefers-color-scheme — MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-color-scheme)
- [Color schemes — Pico CSS official docs](https://picocss.com/docs/color-schemes)
- [CSS variables — Pico CSS official docs](https://picocss.com/docs/css-variables)
- [Dark Mode best practices 2025 — Medium/Bootcamp](https://medium.com/design-bootcamp/the-ultimate-guide-to-implementing-dark-mode-in-2025-bbf2938d2526)
- [Thousands separator UX — crio.do](https://www.crio.do/blog/format-numbers-with-commas-as-thousands-separators-2025-javascript-criodo/)
- [HTML5 number input localization — ctrl.blog](https://www.ctrl.blog/entry/html5-input-number-localization.html)
- [Data Table UX patterns — Pencil & Paper](https://www.pencilandpaper.io/articles/ux-pattern-analysis-enterprise-data-tables)
- [2025 Federal Tax Brackets — IRS](https://www.irs.gov/filing/federal-income-tax-rates-and-brackets)
- [Tax Bracket Calculator 2025-2026 — TurboTax](https://turbotax.intuit.com/tax-tools/calculators/tax-bracket/)
- [Fintech UX Best Practices 2026 — Eleken](https://www.eleken.co/blog-posts/fintech-ux-best-practices)

---
*Feature research for: Fathom v1.1 — financing analyzer enhancements*
*Researched: 2026-03-13*
