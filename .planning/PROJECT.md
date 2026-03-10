# Fathom — Financing Options Analyzer

## What This Is

Fathom is a web application that helps everyday consumers compare the true total cost of different financing options for large purchases. By modeling opportunity costs, inflation, and tax implications alongside traditional loan math, it reveals which financing option genuinely saves the most money — not just which has the lowest monthly payment. It's purchase-agnostic (cars, appliances, medical bills, etc.), fully anonymous with no accounts or persistent data, and designed as an open-source, self-hostable single-process Python app.

## Core Value

Users can instantly see which financing option truly costs least when opportunity costs, inflation, and taxes are factored in — turning a complex financial comparison into a clear, plain-English recommendation.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Single-page input form with global settings and 2-4 per-option financing configurations
- [ ] Support for 6 option types: cash, traditional loan, 0% promo, promo with cash-back, promo with price reduction, custom/other
- [ ] True Total Cost calculation engine (payments + opportunity cost - rebates - tax savings ± inflation)
- [ ] Opportunity cost modeling with configurable investment return rate (presets + manual)
- [ ] Comparison period normalization across options with different terms
- [ ] Summary recommendation card with plain-English explanation and caveats
- [ ] Cost breakdown table with one column per option
- [ ] True Total Cost bar chart and cumulative cost over time line chart
- [ ] Live result updates as inputs change (HTMX partial page replacement with Calculate button fallback)
- [ ] Responsive layout (two-column desktop, stacked mobile with sticky "View Results" anchor)
- [ ] WCAG 2.1 AA accessibility (visible labels, chart text alternatives, not color-only)
- [ ] Stateless — no persistent storage, no user accounts, no server-side session data
- [ ] Server-side Python for all calculations — no client-side JS calculation logic
- [ ] Open-source with self-hosting support: README, env-var config, Dockerfile

### Out of Scope

- Exportable PDF or shareable reports — complexity for v1
- User accounts or cloud-synced history — conflicts with privacy-first design
- Live interest rate data or bank API integrations — external dependency risk
- More than 4 simultaneous options — UI complexity
- Business-specific calculations (depreciation, asset write-offs) — consumer focus
- Mobile native app — web-first
- Offline support — server-rendered app

## Context

- Python 3.14 with SSR as primary paradigm
- HTMX for partial page updates without full reloads
- Server-rendered SVG charts preferred; Chart.js acceptable fallback
- `uv` for Python environment management, `ruff` for linting/formatting
- `ty` and `pyrefly` for type checking (no mypy/pyright)
- `prek` for pre-commit hooks
- Target: 300ms result render time
- Must deploy as single process with no external database

## Constraints

- **Tech stack**: Python 3.14, SSR, HTMX, uv, ruff, ty, pyrefly, prek — mandated by PRD
- **Privacy**: Zero persistent user data — no logging of inputs or results
- **Deployment**: Single deployable Python process, no external database
- **Performance**: Results rendered within 300ms of form submission
- **Accessibility**: WCAG 2.1 AA compliance required
- **Calculations**: All financial math server-side only — never duplicate in JS

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| SSR with HTMX over SPA | Simpler architecture, no client-side state management, aligns with server-side calculation requirement | — Pending |
| SVG charts preferred over JS charting | Fewer client dependencies, better accessibility, server-rendered | — Pending |
| No persistent storage at all | Privacy-first, simpler deployment, no database dependency | — Pending |
| Purchase-agnostic design | Wider utility, simpler UX (no domain-specific templates) | — Pending |

---
*Last updated: 2026-03-10 after initialization*
