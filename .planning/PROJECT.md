# Fathom — Financing Options Analyzer

## What This Is

Fathom is a web application that helps everyday consumers compare the true total cost of different financing options for large purchases. By modeling opportunity costs, inflation, and tax implications alongside traditional loan math, it reveals which financing option genuinely saves the most money — not just which has the lowest monthly payment. It's purchase-agnostic (cars, appliances, medical bills, etc.), fully anonymous with no accounts or persistent data, and designed as an open-source, self-hostable single-process Python app.

## Core Value

Users can instantly see which financing option truly costs least when opportunity costs, inflation, and taxes are factored in — turning a complex financial comparison into a clear, plain-English recommendation.

## Requirements

### Validated

- ✓ Single-page input form with global settings and 2-4 per-option financing configurations — v1.0
- ✓ Support for 6 option types: cash, traditional loan, 0% promo, promo with cash-back, promo with price reduction, custom/other — v1.0
- ✓ True Total Cost calculation engine (payments + opportunity cost - rebates - tax savings ± inflation) — v1.0
- ✓ Opportunity cost modeling with configurable investment return rate (presets + manual) — v1.0
- ✓ Comparison period normalization across options with different terms — v1.0
- ✓ Summary recommendation card with plain-English explanation and caveats — v1.0
- ✓ Cost breakdown table with one column per option — v1.0
- ✓ True Total Cost bar chart and cumulative cost over time line chart — v1.0
- ✓ Live result updates as inputs change (HTMX partial page replacement with Calculate button fallback) — v1.0
- ✓ Responsive layout (two-column desktop, stacked mobile with sticky "View Results" anchor) — v1.0
- ✓ WCAG 2.1 AA accessibility (visible labels, chart text alternatives, not color-only) — v1.0
- ✓ Stateless — no persistent storage, no user accounts, no server-side session data — v1.0
- ✓ Server-side Python for all calculations — no client-side JS calculation logic — v1.0
- ✓ Open-source with self-hosting support: README, env-var config, Dockerfile — v1.0
- ✓ Dark mode — `prefers-color-scheme` support — v1.1
- ✓ Comma-normalized number inputs — accept and display large numbers with commas — v1.1
- ✓ Input tooltips — `?` icon popovers explaining form options — v1.1
- ✓ Output tooltips — `?` icon popovers explaining result terms — v1.1
- ✓ US-centric tax rate guidance — 2025 IRS bracket reference with click-to-fill — v1.1
- ✓ Detailed cost breakdown table — per-option period-by-period view with tabs, column toggles, compare tab — v1.1
- ✓ JSON export/import — download current inputs as JSON file, upload to restore — v1.1
- ✓ Expanded ruff lint coverage (PL, PT, DTZ, T20) with zero violations — v1.1
- ✓ Complex function refactoring below default complexity thresholds — v1.1

### Active

(None — next milestone requirements TBD via `/gsd:new-milestone`)

### Out of Scope

- User accounts or cloud-synced history — conflicts with privacy-first design
- Live interest rate data or bank API integrations — external dependency risk
- More than 4 simultaneous options — UI complexity
- Business-specific calculations (depreciation, asset write-offs) — consumer focus
- Mobile native app — web-first, responsive design sufficient
- Offline support — server-rendered app
- Multi-currency support — adds complexity for minimal user base; math is currency-agnostic
- Wizard/multi-step form — hides context; single-page comparison needs all options visible
- Client-side calculation logic — creates divergence bugs; server is source of truth

## Context

Shipped v1.1 with 3,944 LOC Python, 5,700 LOC tests, 1,310 LOC templates across 12 phases (29 plans total).
Tech stack: Python 3.14, Flask, Pydantic, HTMX, Pico CSS, server-rendered SVG charts.
241 tests passing. All quality gates clean (ruff, ty, pyrefly, prek). Zero inline suppressions.

v1.1 added: dark mode, comma-formatted inputs, tooltip popovers on all form/result fields, IRS tax bracket reference, JSON export/import, detailed per-period cost breakdown with tabs and compare view, and full linting/complexity cleanup.

### Development Tools (MCP Servers)

- **Serena** — Semantic code analysis/editing for token-efficient navigation
- **Context7** — Always fetch current library docs instead of relying on training data
- **Tavily** — Web search and content extraction for research
- **Playwright** — Browser automation for testing the web application

### Browser-Based Validation Policy

All browser-based validation (visual layout, responsive design, HTMX interactivity, CSS rendering, accessibility checks) MUST be automated via the Playwright MCP server. Do not mark browser checks as "manual-only" or "needs human."

### Code Quality Standards

All code must pass with zero errors/warnings:
1. `uv run ruff check .` — linting (fix issues, never suppress with `# noqa`)
2. `uv run ruff format .` — Black-compatible, double quotes, 88 char lines
3. `uv run ty check` — type checking (fix issues, never suppress with `# type: ignore`)
4. `uv run pyrefly check` — type checking (both checkers must pass independently)
5. `uv run prek run` — all pre-commit hooks

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
| SSR with HTMX over SPA | Simpler architecture, no client-side state management, aligns with server-side calculation requirement | ✓ Good — clean separation, no JS state bugs |
| SVG charts preferred over JS charting | Fewer client dependencies, better accessibility, server-rendered | ✓ Good — accessible data tables built in, no Chart.js needed |
| No persistent storage at all | Privacy-first, simpler deployment, no database dependency | ✓ Good — true single-process deployment |
| Purchase-agnostic design | Wider utility, simpler UX (no domain-specific templates) | ✓ Good — works for any purchase type |
| Single FinancingOption with OptionType enum | Simpler than class hierarchy, optional fields per type | ✓ Good — clean, flat domain model |
| Pydantic BaseModel over dataclasses | Type-safe validation, identical API, better error reporting | ✓ Good — seamless migration, richer validation |
| Three-function pipeline (parse → validate → build) | Separation of concerns for form processing | ✓ Good — testable, each stage independent |
| Decimal arithmetic for all money | Eliminates float rounding errors in financial calculations | ✓ Good — exact cent precision |
| CSS variables for dark mode theming | Enables SVG chart colors to switch via media query without Python-side logic | ✓ Good — single source of truth in CSS |
| :root:not([data-theme]) dark selector | Matches Pico CSS convention for auto dark mode detection | ✓ Good — no conflict with Pico framework |
| HTML Popover API + CSS Anchor Positioning for tooltips | Native browser API, no JS toggle logic, accessible by default | ✓ Good — Escape/focus handling free, @supports fallback for older browsers |
| Tooltip text as Python dict on breakdown rows | Keeps content with data, templates just render conditionally | ✓ Good — single source of truth, easy to update |
| formaction with hx-disable for Export button | Bypasses HTMX interception for file download | ✓ Good — clean separation of HTMX vs standard requests |
| HTMX hx-include on detail tab buttons | Stateless detail endpoint — tabs POST current form data | ✓ Good — no server-side session state needed |
| Per-period cost factor decomposition | Separate opportunity/inflation/tax per month alongside aggregates | ✓ Good — enables detailed breakdown without changing aggregate math |
| Cumulative rounding tolerance widened to 0.05 | Per-period Decimal rounding over 36+ months accumulates | ✓ Good — pragmatic, documented in tests |

---
*Last updated: 2026-03-14 after v1.1 milestone*
