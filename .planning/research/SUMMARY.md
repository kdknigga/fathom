# Project Research Summary

**Project:** Fathom — Financing Options Analyzer
**Domain:** Consumer financial calculator (SSR web app, opportunity cost modeling)
**Researched:** 2026-03-10
**Confidence:** MEDIUM-HIGH

## Executive Summary

Fathom is a stateless, server-rendered Python web application that computes the "True Total Cost" of financing options by incorporating opportunity cost, inflation, and tax implications — concepts that no mainstream consumer calculator addresses. The architecture is a deliberate monolith: Flask + Jinja2 + HTMX for the web layer, a pure-Python calculation engine with `decimal.Decimal` arithmetic, and pygal for server-rendered SVG charts. There is no database, no client-side calculation logic, and no JavaScript build step. Every significant technology decision flows from two constraints: all math must live server-side in Python, and the app must deploy as a single process.

The recommended approach is to build the calculation engine first and treat it as the product. The core differentiator — True Total Cost with opportunity cost modeling and comparison period normalization — is architecturally central and cannot be retrofitted. All other components (web layer, charts, HTMX integration) depend on the calculation engine's output structures. The domain model must be defined in Phase 1, because the web layer and chart generator can be built in parallel once those types exist.

The primary risks are mathematical correctness and user trust. Using `float` instead of `decimal.Decimal`, mishandling comparison period normalization (ignoring post-payoff cash flows), or botching rate conversions (nominal vs. effective annual) would produce subtly wrong numbers that users cannot detect until they compare against a lender's amortization table. The second category of risk is UX trust: the True Total Cost metric is novel and non-intuitive; the recommendation card's plain-English explanation is not a nice-to-have — it is the mechanism by which users trust and act on the result.

## Key Findings

### Recommended Stack

The stack is Python-only with no JavaScript build step. Flask 3.1.3 is the correct framework choice — it is WSGI (matching the synchronous, CPU-bound calculation profile), Jinja2-native, and designed for HTML rendering rather than JSON APIs. FastAPI and Django were considered and rejected: FastAPI is API-first (wrong paradigm) and Django brings ORM/auth/admin overhead the project does not need. Gunicorn 25.1.0 is the production server; the stateless design means 1-4 workers covers any realistic load. HTMX 2.0.8 ships as a vendored static file — no CDN dependency, no build step. pygal 3.1.0 generates SVG charts as strings that are embedded inline in Jinja2 templates via the `| safe` filter, keeping all chart logic server-side. WTForms 3.2.1 + Flask-WTF 1.2.2 handle the HTTP form layer (CSRF, HTML label generation, field-level errors); Pydantic 2.12.5 validates the internal typed calculation models. All monetary math uses Python's stdlib `decimal.Decimal` — never `float`.

**Core technologies:**
- **Flask 3.1.3:** Web framework, SSR routing, Jinja2 template rendering — best fit for HTMX + SSR paradigm
- **Jinja2 3.1.6:** HTML templating — ships with Flask, supports template inheritance and partial fragment rendering
- **Gunicorn 25.1.0:** Production WSGI server — single-process deployment with multiple workers
- **HTMX 2.0.8:** Partial page updates — vendored, 16KB, zero dependencies
- **pygal 3.1.0:** Server-side SVG chart generation — inline SVG output, WCAG-friendly text elements
- **WTForms + Flask-WTF:** HTTP form validation, CSRF protection, HTML error rendering
- **Pydantic 2.12.5:** Internal typed domain models — validates data between form layer and calculation engine
- **`decimal.Decimal` (stdlib):** All monetary arithmetic — eliminates float rounding errors

### Expected Features

The product's table stakes are the financing inputs and outputs every calculator provides; the differentiators are what justify Fathom's existence.

**Must have (table stakes):**
- Loan amortization (principal + interest, exact to the cent)
- Side-by-side comparison of 2-4 financing options
- Support for cash, traditional loan, and 0% promotional financing types
- Monthly payment display and total interest paid
- Summary recommendation card ("Option B saves you $X")
- Responsive layout (mobile stacked, desktop two-column with sticky anchor)
- Server-side input validation with field-level error display
- WCAG 2.1 AA accessible form controls (visible labels, ARIA, focus management)
- Purchase price as global primary input
- Reset / Start Over action

**Should have (differentiators):**
- **Opportunity cost modeling** — the core thesis; configurable return rate with presets (4%/7%/10%)
- **True Total Cost metric** — synthesizes payments + opportunity cost - rebates - tax savings +/- inflation
- **Comparison period normalization** — models post-payoff cash flows as invested; critical for honest comparisons
- **Plain-English recommendation with caveats** — templated natural language; explains why, not just what
- **Cumulative cost over time chart** — breakeven visualization (line chart, server-rendered SVG)
- **True Total Cost bar chart** — at-a-glance comparison (bar chart, server-rendered SVG, accessible)
- **Cost breakdown table** — row-by-row decomposition building user trust
- **Deferred interest warning** — consumer advocacy for 0% promos with retroactive interest clauses
- **Live result updates via HTMX** — partial page swap on input change, with Calculate button as fallback
- **Inflation adjustment toggle** — optional, off by default, discounts future cash flows to present value
- **Tax implications toggle** — optional, off by default, marginal rate applied to deductible interest

**Defer to v2+:**
- Cash-back rebate and price reduction option types (lower frequency scenarios)
- Custom / Other option type (edge case escape hatch)
- PDF export or shareable links (significant complexity for unclear demand)
- Dark mode (CSS complexity, not a utility app blocker)
- Print-friendly CSS (nice to have, not launch-critical)
- Live interest rate feeds / bank API integration (external dependency risk, stale data worse than user-entered)

### Architecture Approach

Fathom is a server-rendered monolith with a strictly layered, unidirectional data flow: form submission from the browser, validation into typed domain objects, calculation in a pure-Python engine (no I/O, no Flask imports), SVG chart generation from calculation results, Jinja2 template rendering of the full response or HTMX fragment, and HTML returned to the browser for HTMX to swap into the DOM. The entire request lifecycle is "input in, result out" with no persistent state. HTMX uses the single expanded-target pattern: the entire results area (`#results`) is replaced as one unit; the form is never included in the swap target.

**Major components:**
1. **Web Layer** (`src/fathom/web/`) — thin Flask route handlers orchestrating validation, calculation, and rendering; checks `HX-Request` header to return fragment or full page
2. **Models** (`src/fathom/models/`) — `GlobalSettings`, `FinancingOption`, `CalculationResult`, `ComparisonResult` dataclasses; the contract between all other layers
3. **Calculation Engine** (`src/fathom/calc/`) — pure Python modules for amortization, opportunity cost, inflation, and tax savings; fully testable without HTTP
4. **Chart Generator** (`src/fathom/charts/`) — pygal functions that accept `ComparisonResult` and return SVG strings; decoupled from web layer
5. **Templates** (`src/fathom/templates/`) — base layout, full `index.html`, and `partials/results.html` HTMX fragment; progressive enhancement via standard form fallback

### Critical Pitfalls

1. **Float arithmetic in financial calculations** — Use `decimal.Decimal` with `prec=28` from day one for all monetary values. Never retrofit; the recovery cost is high (every calculation touched). Rate conversions (APR, investment returns) can remain `float` since they are percentages, not currency.

2. **Wrong comparison period normalization** — Model the full comparison window (longest term among active options) for every option. Post-payoff monthly payments must be modeled as invested at the user's return rate through the end of the window. Omitting this makes short-term options look artificially cheap and is architecturally central — cannot be bolted on later.

3. **Nominal vs. effective rate confusion** — Loan APR uses `monthly_rate = APR / 12` (regulatory convention). Investment returns use `monthly_rate = (1 + annual_rate)^(1/12) - 1` (effective annual to effective monthly). Using the same formula for both produces consistently wrong opportunity cost numbers. Verify with the standard $10,000 / 6% APR / 36 months = $304.22/month check.

4. **Opportunity cost double-counting** — For loan options, opportunity cost applies only to the down payment (monthly payments are obligatory, not discretionary). For cash purchase, opportunity cost applies to the full purchase price. Document this accounting model in code comments and tests before writing any calculations.

5. **HTMX form state loss** — Never set `hx-target` to an element that includes or overlaps the form. Always target only `#results`. Use `hx-include` to send all form inputs with every request. Test the "type in field A, change option type in field B, verify field A retained" scenario explicitly.

6. **SVG accessibility as afterthought** — Add `role="img"`, `aria-labelledby`, `<title>`, `<desc>`, and a visually-hidden companion data table to every chart from the first implementation. Use patterns/textures alongside color. Retrofitting costs MEDIUM effort; building it in from the start costs nothing.

## Implications for Roadmap

The architecture research prescribes a natural build order based on component dependencies. The calculation engine and models are the foundation; everything else flows from them. The web layer and chart generator can be developed in parallel once models are defined.

### Phase 1: Domain Models and Calculation Engine

**Rationale:** The calculation engine is the product. All other components depend on its output types. The highest-severity pitfalls (float arithmetic, comparison period normalization, rate conversions, opportunity cost accounting) all live here and cannot be fixed cheaply after the fact. Build and test exhaustively before touching the web layer.

**Delivers:** A fully tested, pure-Python library that accepts `GlobalSettings` and a list of `FinancingOption` objects and returns a `ComparisonResult`. No Flask dependency. Passes known amortization check values to the cent.

**Features addressed:** Amortization (all option types), True Total Cost calculation, opportunity cost, comparison period normalization, inflation adjustment, tax savings, deferred interest flag, plain-English recommendation text generation.

**Pitfalls to avoid:** All five critical pitfalls (float arithmetic, normalization, rate conversion, double-counting) must be addressed here. Write unit tests against known values before implementation; tests are the proof of correctness.

**Research flag:** LOW — financial math patterns are well-documented. Standard amortization and compound interest formulas are established. The novel element (opportunity cost + normalization) is explained thoroughly in ARCHITECTURE.md. No additional research phase needed.

### Phase 2: Web Layer and Form Handling

**Rationale:** Once the calculation engine exists and returns typed results, the web layer is a thin orchestration layer. Flask routing, WTForms validation, and HTMX integration follow well-established patterns. Building this after models are defined allows using stub results during development.

**Delivers:** Working single-page application: form with all input fields (conditional display by option type), server-side validation with field-level errors, `POST /calculate` route returning full page or HTMX fragment, progressive enhancement (works without JavaScript).

**Features addressed:** Input form for cash/loan/0% promo types, input validation, responsive layout, accessible form controls, Reset button, HTMX live updates.

**Pitfalls to avoid:** HTMX form state loss (target only `#results`, never the form itself), HTMX + validation (return error fragments with correct HTTP status codes), XSS via custom option labels (escape all user text before embedding in SVG or HTML).

**Research flag:** LOW — Flask + HTMX + WTForms integration follows well-documented patterns. ARCHITECTURE.md provides the exact route handler structure and template pattern.

### Phase 3: Results Display and Charts

**Rationale:** Results rendering depends on having real `ComparisonResult` objects from the calculation engine. The summary recommendation card, cost breakdown table, and both charts must be built together because they form one logical output unit (rendered as `partials/results.html`).

**Delivers:** Complete results view: summary recommendation card with plain-English text and caveats, cost breakdown table with one column per option, True Total Cost bar chart (SVG), cumulative cost over time line chart (SVG). Accessibility-compliant from the start.

**Features addressed:** Summary recommendation card, cost breakdown table, bar chart, cumulative cost line chart, deferred interest caveat display, inflation and tax toggle results.

**Pitfalls to avoid:** SVG accessibility (title, desc, aria-labelledby, companion data table, non-color-only differentiation from first implementation), SVG XSS (use pygal's template engine, never string concatenation), chart performance (polyline/path for line charts, not per-point elements).

**Research flag:** LOW for the table and recommendation card. MEDIUM for SVG accessibility specifics — the WCAG 2.1 AA requirements for SVG are well-defined but pygal's specific hook points for ARIA injection may need validation against the library's render() API.

### Phase 4: Polish, Edge Cases, and Additional Option Types

**Rationale:** With the core three option types (cash, loan, 0% promo) working end-to-end, this phase adds the remaining option types, hardens edge cases, and completes the UX polish pass. These were deferred because they add complexity without changing the architectural foundation.

**Delivers:** Cash-back rebate and price reduction option types, advanced input validation (reasonable ranges, helpful error messages), mobile layout refinement, HTMX debounce for live updates (prevent calculation spam), rate limiting middleware, print-friendly CSS, performance verification against 300ms target.

**Features addressed:** Cash-back and price reduction option types, HTMX keystroke debouncing, security hardening (rate limiting, input escaping audit), UX polish (plain language labels, monthly payment always visible, partial results with incomplete inputs).

**Pitfalls to avoid:** Keystroke-triggered calculation spam (add `hx-trigger="keyup changed delay:500ms"` or keep explicit Calculate button as primary), privacy (never log form inputs), display of opportunity cost as negative number (reframe as "investment earnings you would miss").

**Research flag:** LOW — these are refinements on established foundations. Custom/Other option type (v2) and PDF export (v2) are explicitly deferred.

### Phase Ordering Rationale

- **Models first:** Both the web layer and calculation engine depend on shared type definitions. Defining `FinancingOption`, `GlobalSettings`, and `ComparisonResult` first allows parallel development of the calculation engine and a stub web layer.
- **Calculation engine before web layer:** The web layer can use hardcoded mock `ComparisonResult` objects during development. The reverse is not true — the calculation engine has no web dependency.
- **Results display after calculation engine:** `partials/results.html` renders `ComparisonResult` objects; without real data, you cannot validate the rendering is correct.
- **Polish last:** Edge cases, additional option types, and UX refinements do not block the core user flow. Ship the core flow first; iterate.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (SVG accessibility):** pygal's specific API for injecting ARIA attributes (`<title>`, `<desc>`, `aria-labelledby`) into rendered SVG needs validation against the library's actual render() output structure. May require post-processing the SVG string if pygal does not expose these hooks.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Calculation Engine):** Financial math formulas are textbook. The architecture is clearly specified. Pydantic + Decimal patterns are well-documented.
- **Phase 2 (Web Layer):** Flask + HTMX + WTForms integration is well-documented in official sources and the ARCHITECTURE.md provides the exact route handler pattern.
- **Phase 4 (Polish):** All remaining work is refinement of established patterns.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Versions verified against PyPI (2026-03-10). Technology choices are well-reasoned with documented alternatives considered and rejected. |
| Features | MEDIUM | PRD analysis is thorough. Competitor analysis was limited — calculator UIs could not be fully scraped. Feature categorization relies on domain expertise. Core differentiators (opportunity cost, True Total Cost) are clearly novel; table stakes are well-established. |
| Architecture | HIGH | Official HTMX and Flask documentation consulted. Patterns are well-established (SSR monolith, expanded target, dual templates, pure calculation engine). The build order is derived from actual component dependencies. |
| Pitfalls | MEDIUM | Well-established financial math and web dev patterns. Web search was unavailable for cross-referencing current community discussions. All pitfalls documented are high-confidence based on domain knowledge. Specific HTMX + Python SSR edge cases may exist that are not captured. |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **pygal ARIA injection:** Verify whether pygal 3.1.0's `render()` method accepts parameters for `<title>`, `<desc>`, and `role="img"`, or whether SVG post-processing is required. Address in Phase 3 planning.
- **HTMX debounce interaction with validation:** The interaction between `delay:500ms` debounce and WTForms validation error display (partial results vs. error state) needs validation during Phase 2 implementation. The HTMX docs describe the mechanism; the specific Flask-WTForms response pattern needs to be confirmed.
- **Competitor feature audit:** The FEATURES.md competitive analysis was limited by inability to scrape calculator UIs. The feature categorization is based on domain knowledge. If Fathom's differentiators are less novel than assumed, revisit during requirements definition.
- **pygal styling for WCAG contrast:** pygal's default color palette may not meet WCAG 2.1 AA contrast ratios against white backgrounds. Audit default styles and prepare custom palette before Phase 3.

## Sources

### Primary (HIGH confidence)
- Flask 3.1.3 — https://pypi.org/project/flask/ (verified 2026-03-10)
- Jinja2 3.1.6 — https://pypi.org/project/jinja2/ (verified 2026-03-10)
- Gunicorn 25.1.0 — https://pypi.org/project/gunicorn/ (verified 2026-03-10)
- HTMX 2.0.8 — https://htmx.org/docs/ (partial page updates, HX-Request, hx-target, hx-swap)
- HTMX examples — https://htmx.org/examples/update-other-content/ (expanded target pattern)
- pygal 3.1.0 — https://pypi.org/project/pygal/ and https://www.pygal.org/en/stable/ (verified 2026-03-10)
- WTForms 3.2.1 — https://pypi.org/project/wtforms/ (verified 2026-03-10)
- Flask-WTF 1.2.2 — https://pypi.org/project/flask-wtf/ (verified 2026-03-10)
- Pydantic 2.12.5 — https://pypi.org/project/pydantic/ (verified 2026-03-10)
- pytest 9.0.2 — https://pypi.org/project/pytest/ (verified 2026-03-10)
- Flask template patterns — https://flask.palletsprojects.com/en/stable/patterns/templateinheritance/
- Python `decimal` module — stdlib documentation (standard financial calculation best practice)
- WCAG 2.1 AA — W3C guidelines for SVG accessibility

### Secondary (MEDIUM confidence)
- Fathom PRD (docs/PRD.md) — primary source for requirements and scope decisions
- Fathom PROJECT.md (.planning/PROJECT.md) — validated requirements and constraints
- Domain expertise: standard loan calculator features, consumer finance UX patterns, amortization math
- Standard amortization formulas: corporate finance reference (verified against $10,000 / 6% APR / 36 months = $304.22/month)

### Tertiary (LOW confidence)
- NerdWallet loan calculator (nerdwallet.com) — competitor inspection (limited detail from fetch)
- Dinkytown loan comparison calculator (dinkytown.net) — competitor inspection (limited detail from fetch)

---
*Research completed: 2026-03-10*
*Ready for roadmap: yes*
