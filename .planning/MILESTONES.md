# Milestones

## v1.1 Deeper Insights (Shipped: 2026-03-14)

**Phases:** 6 (7-12) | **Plans:** 13 | **LOC:** 3,944 Python + 5,700 test | **Timeline:** 2 days (2026-03-13 → 2026-03-14)
**Git range:** `v1.0..HEAD` | **Commits:** 90 | **Files changed:** 112 (+15,490/-1,046) | **Tests:** 241 passing | **Requirements:** 23/23

**Key accomplishments:**
1. OS-preference dark mode with CSS custom properties and SVG chart theming
2. Comma-normalized numeric inputs with server-side parsing and client-side blur formatting
3. Tooltip popovers on all form fields and result metrics with 2025 IRS tax bracket reference
4. JSON export/import for saving and restoring form inputs with Pydantic validation
5. Detailed per-period cost breakdown table with tabs, compare view, and column toggles
6. Expanded ruff lint coverage (PL, PT, DTZ, T20) and refactored all complex functions below default thresholds

---

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
