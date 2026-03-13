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

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0 | 6 | 16 | Baseline: audit-driven gap closure pattern established |

### Cumulative Quality

| Milestone | Tests | Quality Gate | Zero-Suppression |
|-----------|-------|-------------|------------------|
| v1.0 | 179 | All clean | 0 noqa, 0 type:ignore |

### Top Lessons (Verified Across Milestones)

1. Milestone audits catch real bugs in "complete" code — always run before shipping
