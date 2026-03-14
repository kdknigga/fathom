# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-13
**Phases:** 6 | **Plans:** 16

### What Was Built
- True Total Cost calculation engine with Decimal arithmetic, 6 option types, opportunity cost, inflation, tax
- Flask SSR web app with HTMX interactivity, Pico CSS responsive layout, server-rendered SVG charts
- Accessible results: recommendation card, cost breakdown table, bar/line charts with data tables
- Production infrastructure: Dockerfile, pydantic-settings, vendor assets, MIT license, README
- Pydantic validation layer replacing dataclasses and hand-written validators
- Gap closure phase fixing 3 integration bugs and hardening tests

### What Worked
- Calculation engine first was the right call — every subsequent phase consumed its types cleanly
- Pydantic migration was seamless — BaseModel has identical API to dataclasses, zero consumer changes
- Milestone audit caught 3 real integration gaps (retroactive_interest UI, server-side option count, return_preset format) that would have shipped broken
- Playwright-automated browser verification eliminated "needs human" deferral pattern
- All 16 plans executed in ~70 minutes total with zero rollbacks

### What Was Inefficient
- Phase 4 Deployment was marked incomplete in roadmap despite all 3 plans having SUMMARYs — checkbox maintenance lag
- Some ROADMAP.md plan checkboxes fell out of sync with disk state (plans completed but not checked)
- Phase 3 VERIFICATION.md had conflicting status in frontmatter vs body — fixed but revealed verification write-once assumption
- `compute_opportunity_cost_series` was written but never used — dead code from Plan 01-02

### Patterns Established
- Three-function form pipeline: parse → validate → build_domain_objects
- TYPE_CHECKING block for imports only used in type annotations (TC003)
- Pattern IDs prefixed per chart type to avoid SVG scope collisions
- CSS `:has()` selectors in Playwright for targeting elements by content
- Defense-in-depth: both Pydantic validators AND `build_domain_objects` enforce business rules

### Key Lessons
1. Milestone audits are high-value: the v1.0 audit found 3 real bugs in "complete" code
2. Pydantic is a strict superset of dataclasses for domain modeling — migration is mechanical
3. Server-rendered SVG charts with data tables achieve accessibility without JS charting libraries
4. HTMX partial page replacement is simple with Flask — just detect HX-Request header
5. Decimal arithmetic throughout prevents float rounding errors but requires explicit str/format conversions at boundaries

### Cost Observations
- Model mix: quality profile (opus-heavy)
- Sessions: ~6 sessions across 4 days
- Notable: Plans averaged 4.4 min each — fast execution due to clear phase goals

---

## Milestone: v1.1 — Deeper Insights

**Shipped:** 2026-03-14
**Phases:** 6 (7-12) | **Plans:** 13 | **Commits:** 90

### What Was Built
- OS-preference dark mode with CSS custom properties for all custom styles and SVG charts
- Comma-normalized numeric inputs: server-side stripping, Jinja filter, client-side blur formatting
- Tooltip popovers on all form fields and result metrics using HTML Popover API + CSS Anchor Positioning
- 2025 IRS tax bracket reference with click-to-fill for marginal tax rate
- JSON export/import with Pydantic validation for form input persistence
- Detailed per-period cost breakdown table with tabs, compare view, column toggles, and monthly/annual granularity
- Full linting cleanup: PL, PT, DTZ, T20 rules enabled, all complex functions refactored below thresholds

### What Worked
- Phase 12 (linting cleanup) as a dedicated phase was highly efficient — auto-fixes handled 80%+ of violations, manual refactors were focused
- HTML Popover API eliminated all tooltip JS state management — browser handles Escape, focus, and outside-click natively
- CSS Anchor Positioning with @supports fallback provides progressive enhancement without degraded experience
- HTMX hx-include on detail tab buttons kept the detail endpoint stateless — no server-side session needed
- Event delegation pattern across formatting.js, tooltips.js, and detail_toggle.js means HTMX-swapped content works automatically
- All 13 plans executed in 2 days with zero rollbacks

### What Was Inefficient
- ROADMAP.md phase 10-12 progress table rows had wrong column alignment (milestone column missing) — cosmetic but required manual fix
- Some SUMMARY.md files lacked one_liner fields, so automated extraction returned nulls — manual extraction was needed
- Phase 12 per-file-ignores for complexity rules in Plan 01 were immediately removed in Plan 02 — could have been one plan

### Patterns Established
- CSS variables for SVG chart colors: `var(--chart-*)` in fill/stroke attributes, overridden in `@media (prefers-color-scheme: dark)`
- `_clean_monetary` helper for DRY dollar/comma/space stripping before Decimal conversion
- Tooltip text as Python dict on breakdown row objects — templates render conditionally
- `formaction` + `hx-disable` pattern for bypassing HTMX on file download buttons
- Tuple variable pattern `(_errors)` for except clauses maintaining pre-commit hook compatibility
- Per-period cost factor decomposition: separate fields alongside aggregate totals

### Key Lessons
1. HTML Popover API + CSS Anchor Positioning is production-ready with @supports fallback — eliminates tooltip library dependencies
2. Event delegation is essential for HTMX apps — any JS that binds directly to elements will break on partial page swaps
3. Dedicated linting cleanup phases are efficient because auto-fix handles most violations and refactoring is focused
4. Per-period Decimal rounding accumulates over 36+ months — tolerance widening (0.02→0.05) is pragmatic and should be documented
5. Stateless endpoints via hx-include are simpler than server sessions for HTMX-driven interactive features

### Cost Observations
- Model mix: quality profile (opus-heavy)
- Sessions: ~4 sessions across 2 days
- Notable: Plans averaged 4.6 min each — similar to v1.0 baseline, consistent velocity

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0 | 6 | 16 | Baseline: audit-driven gap closure pattern established |
| v1.1 | 6 | 13 | Linting cleanup as dedicated phase; HTML Popover API adoption; event delegation pattern |

### Cumulative Quality

| Milestone | Tests | Quality Gate | Zero-Suppression |
|-----------|-------|-------------|------------------|
| v1.0 | 179 | All clean | 0 noqa, 0 type:ignore |
| v1.1 | 241 | All clean | 0 noqa, 0 type:ignore |

### Top Lessons (Verified Across Milestones)

1. Milestone audits catch real bugs in "complete" code — always run before shipping
2. Event delegation is essential for HTMX apps — verified across formatting (v1.0), tooltips, and detail toggles (v1.1)
3. Consistent plan velocity (~4.5 min/plan) across both milestones suggests planning quality is stable
