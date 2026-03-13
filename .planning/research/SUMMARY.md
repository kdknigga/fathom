# Project Research Summary

**Project:** Fathom — Financing Options Analyzer (v1.1)
**Domain:** SSR financial calculator — enhancement milestone
**Researched:** 2026-03-13
**Confidence:** HIGH

## Executive Summary

Fathom v1.1 adds seven UX enhancements to an already-shipping v1.0 Flask/HTMX/Pico CSS app: input and output tooltips, comma-normalized number inputs, dark mode, JSON export/import, US tax rate guidance, and a detailed period-by-period cost breakdown table. The research is unusually concrete because the v1.0 codebase exists and every integration point has been verified against actual source files. The recommended approach is additive — no new Python dependencies, no new JS libraries, no new CSS frameworks. All seven features are implementable with the existing stack plus two small vanilla JS files (~50 lines each) and targeted CSS additions (~2 KB).

The recommended build order is driven by two hard dependencies: comma-stripping must land before any feature that exposes formatted number inputs (otherwise `_try_decimal()` silently produces `None`), and the detailed breakdown table should come last because it is the most complex feature and benefits from having tooltips and export/import already in place for testing. Dark mode is the fastest and lowest risk (done first to establish Playwright screenshot test infrastructure), tooltips are low-risk foundational work (done second, establishing the accessibility pattern for all subsequent tooltip additions), comma inputs are medium complexity with an important server-side prerequisite, export/import is a clean new route pair, and the period table is the largest structural addition.

The primary risk area is the combination of HTMX, file downloads, and partial-page state. Specifically: HTMX will intercept the JSON export request if not explicitly excluded (export form must have no `hx-*` attributes), HTMX file upload requires `hx-encoding="multipart/form-data"` or the upload is silently lost, and HTMX partial swaps will reset dark mode theme state on `<html>` if not defended with an `htmx:afterSwap` listener. These are well-understood pitfalls with documented one-line fixes; they must be written into the design from the start rather than discovered during QA.

## Key Findings

### Recommended Stack

The v1.0 stack (Flask 3.1.3, Jinja2 3.1.6, HTMX 2.0.8, Pico CSS 2.1.1, pygal 3.1.0, WTForms 3.2.1, Pydantic 2.12.5) requires zero additions for v1.1. Every feature maps to either a native browser API (HTML Popover API, `prefers-color-scheme` CSS, `Intl.NumberFormat`), an existing Python stdlib capability (json, decimal), or standard Flask patterns (file download response, multipart file upload). The tempting library additions — Cleave.js for number formatting, Van11y for tabs, AutoNumeric — add 20–40 KB each for behavior achievable in 8–50 lines of vanilla code.

**Core technologies:**
- **Flask 3.1.3:** SSR routing and new export/import endpoints — best Python SSR framework for HTMX-based apps
- **Pico CSS 2.1.1:** Dark mode via `prefers-color-scheme` is already built in; requires only removing `data-theme="light"` from `<html>`
- **HTML Popover API (native, no library):** Tooltips — Baseline Widely Available since April 2025; provides WCAG-compliant dismiss, keyboard access, top-layer rendering with zero JS
- **Pydantic 2.12.5:** JSON export serialization via `model_dump()` and import validation — same models as form pipeline
- **`decimal` stdlib:** Comma stripping must happen at the `Decimal()` call boundary in `forms.py` — server-authoritative parse location

**What NOT to add:**
- Cleave.js / IMask / AutoNumeric — 8 lines of `Intl.NumberFormat` covers comma formatting
- Van11y / Tabby — 50 lines of vanilla JS covers the W3C tab pattern
- Any second CSS framework — variable conflicts with Pico CSS
- `interestfor` attribute (hover tooltips) — not Baseline; missing Firefox/Safari support (March 2026)
- CSS Anchor Positioning — 82% global support, Firefox 147+ required, not Baseline Widely Available

### Expected Features

**Must have (table stakes):**
- Input tooltips (`?` popovers on form fields) — financial jargon (APR, opportunity cost, marginal rate) requires inline explanation; users abandon unfamiliar forms
- Output tooltips (result term explanations) — "True Total Cost" and "Opportunity Cost" are novel terms; without explanation users distrust the numbers
- Comma-normalized number inputs — entering `25000` when the amount is `$25,000` is error-prone; users expect formatted numeric entry
- US tax rate guidance — marginal tax rate is the single most confusing input; inline bracket reference converts an opaque field into a self-service lookup

**Should have (differentiators):**
- Detailed period-by-period breakdown table — no mainstream consumer financing calculator shows period-level True Total Cost decomposition with cost-factor columns; uniquely transparent
- JSON export/import — no competitor supports this; critical for "what if I renegotiated to 3.9%?" scenario iteration
- Dark mode (`prefers-color-scheme`) — baseline user expectation in 2025+; essentially free via Pico CSS once `data-theme="light"` hardcode is removed

**Defer to v2+:**
- Manual dark/light toggle button — OS preference is sufficient for v1.1; toggle adds localStorage state management with FOUC risk
- Real-time comma formatting while typing — cursor position bugs and mobile keyboard conflicts; format-on-blur is the right pattern
- CSV/Excel amortization export — the period breakdown table and JSON export together satisfy the underlying need
- Tax bracket auto-calculation from income — auto-computed marginal rate creates false confidence; user-selects from reference table

### Architecture Approach

All seven features integrate additively into the existing Flask/HTMX SSR architecture with no structural changes to the calculation engine. The data flow is unchanged: `forms.py` parses and validates, `engine.py` calculates, `results.py` and `charts.py` prepare display data, templates render. v1.1 touches `forms.py` (comma stripping), `results.py` (adds `period_table` key), `routes.py` (two new routes), `base.html` (remove one attribute), and adds two new template partials plus tooltip markup across existing templates. The key architectural decision is that tab state in the breakdown table is managed in minimal vanilla JS, not via HTMX round-trips — all period data is already in the DOM at render time, so HTMX tab switching would add latency with zero benefit.

**Major components (v1.1 additions):**
1. `forms.py::_try_decimal()` / `_to_money()` — add `.replace(",", "")` before `Decimal()` (MODIFY: one-line change, server-authoritative)
2. `results.py::build_period_table_data()` — reshapes `OptionResult.monthly_data` into template-ready period rows per option (NEW function, no engine changes)
3. `routes.export_config()` / `routes.import_config()` — JSON download response and multipart upload parse (NEW routes, plain Flask patterns)
4. `partials/results/period_table.html` + tab JS (~30 lines) — tabbed period breakdown with CSS column toggles (NEW template)
5. Tooltip `?` buttons across all option field templates, global settings, and results partials (ADDITIVE, HTML Popover API, ~6 templates modified)
6. `base.html` dark mode — remove `data-theme="light"` and add dark overrides for hardcoded caveat CSS variables (MODIFY)

### Critical Pitfalls

1. **Comma input breaks `_try_decimal()` silently** — `Decimal("1,500")` raises `InvalidOperation`, is caught and returns `None`, silently treating the field as empty with no user-visible error. Fix: add `.replace(",", "")` in `_try_decimal()` and `_to_money()` before any comma-display feature ships. Verify with an explicit test: POST `"1,500"` → `Decimal("1500")`.

2. **HTMX intercepts JSON export request** — HTMX will intercept a POST to `/export` and attempt to swap JSON into the DOM instead of triggering a file download. Fix: export form must use no `hx-*` attributes (plain `<form method="post" action="/export">`); the `Content-Disposition: attachment` response then triggers browser download correctly.

3. **SVG chart text invisible in dark mode** — `charts.py` uses hardcoded hex for axis labels and grid lines (`fill="#333"`). These do not inherit `prefers-color-scheme` and become invisible on dark backgrounds. Fix: replace text/axis/grid hardcoded colors with `fill="currentColor"` in SVG Jinja templates. Data series colors (blue/red/green/amber) can remain hardcoded — saturated enough for both modes.

4. **Tooltip WCAG 1.4.13 failure if CSS-only** — CSS `:hover` tooltips fail three WCAG 2.1 AA requirements: not dismissable (no Escape key), not hoverable (disappears when pointer moves to tooltip), not keyboard accessible. Fix: use the HTML Popover API exclusively. The `popovertarget` click-toggle pattern satisfies all three requirements and is Baseline Widely Available. The first tooltip sets the canonical pattern; all others follow.

5. **HTMX table swap fails with bare `<tr>`/`<td>` fragments** — HTMX parses partial HTML responses via `innerHTML`; browsers enforce table structure rules and discard or misplace bare row/cell fragments. Fix: never use a `<tbody>` or `<tr>` as an HTMX swap target. Wrap the entire `<table>` in a `<div>` and target the `<div>` for any HTMX swaps. (For this feature, tab switching uses vanilla JS visibility toggling — not HTMX — which avoids this pitfall entirely.)

## Implications for Roadmap

Based on research, the build order is dependency-driven with each phase independently testable and verifiable via Playwright.

### Phase 1: Dark Mode
**Rationale:** Zero risk, zero dependencies, single-file change that does not touch the calculation path. Establishes Playwright dark-mode screenshot test infrastructure before it is needed for later phases.
**Delivers:** OS-preference dark mode across the entire app; dark overrides for caveat card CSS variables; baseline Playwright screenshot comparison in both themes
**Addresses:** Dark mode (differentiator)
**Avoids:** FOUC pitfall (CSS-only `prefers-color-scheme` does not FOUC), SVG chart text color issue (audit `currentColor` usage in SVG templates)

### Phase 2: Comma-Normalized Inputs
**Rationale:** Server-side comma stripping is a prerequisite for all subsequent manual testing. If testers type formatted numbers during later phases and the parser silently produces `None`, test results are invalid. Ship the server fix before any feature that increases formatted-number input likelihood.
**Delivers:** `_try_decimal()` and `_to_money()` accept comma-formatted strings; `type="text"` with `inputmode="numeric"` on monetary fields; cosmetic blur/focus JS formatting (~20 lines)
**Addresses:** Comma inputs (table stakes)
**Avoids:** Silent `Decimal()` failure pitfall (Pitfall 1), `type="number"` comma rejection pitfall (Pitfall 2)

### Phase 3: Tooltips (Input + Output + Tax Guidance)
**Rationale:** Input and output tooltips use the same Popover API mechanism. Implementing all tooltip work in one phase establishes the canonical pattern (HTML, CSS, ARIA, WCAG 1.4.13 compliance) once, then repeats it across ~20 locations. Tax guidance is a specialized tooltip variant using the same mechanism. Getting the accessibility pattern right on the first tooltip is cheaper than retrofitting all of them.
**Delivers:** `?` popover buttons on all option field labels, global settings, and result term labels; tax bracket reference table in a `<details>` toggle near the tax rate input; ~20 lines CSS for `.tooltip-trigger` and `.tooltip-popover`
**Addresses:** Input tooltips (table stakes), output tooltips (table stakes), tax rate guidance (differentiator)
**Avoids:** WCAG 1.4.13 failure pitfall (Pitfall 9), tooltip overflow/z-index clipping pitfall (Pitfall 10)

### Phase 4: JSON Export / Import
**Rationale:** Export is simpler than import (download response only). Import depends on Phase 2's comma stripping being in place so imported JSON with formatted number strings parses correctly. Both routes follow established Flask patterns. Round-trip testing (export then import) provides a clean integration verification.
**Delivers:** `POST /export` Flask route returning `Content-Disposition: attachment` JSON download; `POST /import` multipart upload route that validates and re-renders the pre-populated form; `partials/export_import.html` UI
**Addresses:** JSON export/import (differentiator)
**Avoids:** HTMX intercepting download (Pitfall 8), missing `hx-encoding` on file upload (integration gotcha), JSON import without size/schema validation (Pitfall 7), XSS via unescaped imported values (security)

### Phase 5: Detailed Period-by-Period Breakdown Table
**Rationale:** Most complex feature; benefits from all earlier phases being stable before adding this surface area. Period data already exists in `OptionResult.monthly_data` — no engine changes. Work is data reshaping in `results.py` and a new template with tab and column toggle UI. Placed last so any regressions are isolated to this feature.
**Delivers:** `build_period_table_data()` in `results.py`; `partials/results/period_table.html` with per-option tabs and side-by-side compare tab; CSS column toggles (checkbox + sibling combinator); ~30-line tab switching JS with W3C ARIA pattern (`htmx:afterSwap` re-initialization)
**Addresses:** Detailed breakdown table (differentiator)
**Avoids:** HTMX table swap with bare `<tr>` fragments (Pitfall 6 — tabs use JS, not HTMX), tab state lost after Calculate (Pitfall 11), column toggle unchecked-state inversion (Pitfall 12), display state added to domain models anti-pattern

### Phase Ordering Rationale

- Dark mode first: zero-risk, establishes Playwright screenshot comparison infrastructure for all subsequent visual validation
- Comma inputs second: server-side parse fix is a prerequisite that affects test validity for all later phases; must land before users can type formatted numbers
- Tooltips third: single mechanism repeated across ~20 locations; establishing the pattern once in Phase 3 costs less than touching templates multiple times
- Export/import fourth: clean bounded feature pair that depends only on Phase 2 comma stripping being stable
- Period table last: most complex feature; touches `results.py` return shape, adds new template structure, benefits from all earlier phases having been independently validated

### Research Flags

Phases with standard patterns (no additional research needed during planning):
- **Phase 1 (Dark mode):** Single attribute deletion + 6 CSS overrides. Pico CSS docs are authoritative.
- **Phase 2 (Comma inputs):** One-line server fix + 20-line JS. MDN `Intl.NumberFormat` is definitive.
- **Phase 3 (Tooltips):** HTML Popover API is Baseline Widely Available with complete MDN documentation. W3C WCAG 1.4.13 is the spec.
- **Phase 4 (JSON export/import):** Standard Flask `make_response` + `Content-Disposition` pattern.

Phase that benefits from a brief research spike before implementation:
- **Phase 5 (Period breakdown table):** Tab state persistence mechanism has two viable approaches (server-echoes active tab as hidden input vs. `htmx:afterSwap` re-activation via JS). Confirm which approach to use before building the tab UI. Column toggle CSS specificity within Pico CSS may also require iteration.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All v1.0 packages production-verified. v1.1 adds zero new packages. All browser APIs confirmed Baseline Widely Available via Can I Use and web.dev. |
| Features | HIGH | Features are scoped in PROJECT.md, not speculative. Research confirmed implementation paths against well-documented browser APIs and IRS data. |
| Architecture | HIGH | All integration points verified against actual v1.0 source files (`routes.py`, `forms.py`, `results.py`, all templates). No guesses about existing code. |
| Pitfalls | HIGH | All pitfalls sourced from official documentation (HTMX issues tracker, MDN, W3C WCAG spec, Pico CSS GitHub). All have documented fixes with specific code examples. |

**Overall confidence:** HIGH

### Gaps to Address

- **SVG chart dark mode scope:** Research recommends `currentColor` for axis/text colors, but the actual SVG Jinja templates were not read during this research cycle. During Phase 1 implementation, audit `bar_chart.html` and `line_chart.html` for all hardcoded hex color attributes. Low risk — a Playwright screenshot in dark mode immediately catches any missed color.

- **Period table render performance:** Research estimates 60 months × 4 options × 8 cost columns = ~1,920 table cells is acceptable server-side, but this was not benchmarked. During Phase 5 planning, measure render time with maximum data before committing to always-rendering the full table. If render exceeds 100ms, consider lazy-loading the period table on tab activation.

- **Tab state persistence approach:** Two valid options exist (hidden input echoed by server vs. `htmx:afterSwap` JS re-activation). Architecture research recommends the server-echo approach as more reliable, but the implementation detail was not fully specified. Settle this before building the tab UI in Phase 5.

## Sources

### Primary (HIGH confidence)
- [Pico CSS Color Schemes](https://picocss.com/docs/color-schemes) — dark mode mechanism, `data-theme` attribute behavior
- [MDN Popover API](https://developer.mozilla.org/en-US/docs/Web/API/Popover_API) — browser support matrix, `popovertarget` usage, ARIA behavior
- [Popover Baseline Widely Available](https://web.dev/blog/popover-baseline) — April 2025 confirmation
- [W3C APG Tabs Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/) — `aria-selected`, arrow-key navigation requirements
- [WCAG SC 1.4.13 Content on Hover or Focus](https://www.w3.org/WAI/WCAG21/Understanding/content-on-hover-or-focus.html) — tooltip WCAG requirements
- [IRS Federal Tax Rates and Brackets](https://www.irs.gov/filing/federal-income-tax-rates-and-brackets) — 2026 bracket data
- [Flask JSON Patterns](https://flask.palletsprojects.com/en/stable/patterns/javascript/) — `Content-Disposition: attachment` download pattern
- [HTMX Documentation](https://htmx.org/attributes/hx-swap/) — `hx-encoding`, `hx-boost`, partial swap behavior
- [HTMX Troublesome Tables Issue #2654](https://github.com/bigskysoftware/htmx/issues/2654) — table fragment swap constraint
- [Pico CSS GitHub: FOUC fix](https://github.com/picocss/examples/issues/18) — inline head script pattern
- Fathom v1.0 source code — all integration points verified against actual source files

### Secondary (MEDIUM confidence)
- [Frontend Masters: Popover API for HTML Tooltips](https://frontendmasters.com/blog/using-the-popover-api-for-html-tooltips/) — tooltip implementation pattern
- [MDN Intl.NumberFormat](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat) — comma formatting API
- [CSS Anchor Positioning — Can I Use](https://caniuse.com/css-anchor-positioning) — 82% support, not Baseline Widely Available

### Tertiary (LOW confidence)
- Period table render performance estimate (1,920 cells acceptable) — not benchmarked; inferred from general DOM size guidelines

---
*Research completed: 2026-03-13*
*Ready for roadmap: yes*
