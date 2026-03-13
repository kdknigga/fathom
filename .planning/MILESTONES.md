# Milestones

## v1.0 MVP (Shipped: 2026-03-13)

**Phases:** 6 | **Plans:** 16 | **LOC:** 2,898 Python | **Timeline:** 4 days (2026-03-10 → 2026-03-13)
**Git range:** `feat(01-01)` → `feat(06-02)` | **Tests:** 179 passing | **Requirements:** 48/48

**Key accomplishments:**
1. True Total Cost calculation engine with Decimal arithmetic, opportunity cost modeling, inflation adjustment, and tax savings
2. Complete web form layer with Flask SSR, all 6 option types, HTMX interactivity, and responsive layout
3. Results display with recommendation card, cost breakdown table, SVG bar/line charts with accessible data tables
4. Production-ready deployment: Dockerfile, pydantic-settings config, vendor asset bundling, MIT license, README
5. Pydantic refactor replacing all dataclasses and hand-written validation with Pydantic BaseModel
6. Gap closure: retroactive interest UI, server-side option count validation, test hardening

**Tech debt remaining (3 cosmetic, 0 blockers):**
- `compute_opportunity_cost_series` dead code in opportunity.py
- 03-VERIFICATION.md frontmatter/body status inconsistency
- `sorted_options` naming overlap across analyze_results/prepare_charts

---
