# Product Requirements Document
## Fathom — Financing Options Analyzer

**Version:** 1.0
**Status:** Draft
**Last Updated:** March 10, 2026

---

## 1. Overview

### 1.1 Product Summary

Fathom is a web and mobile application that helps everyday consumers make smarter decisions when financing a large purchase. By modeling the true total cost of each financing option — including opportunity costs, inflation, and tax implications — the app reveals which option is genuinely best for the user's situation, not just which has the lowest monthly payment.

### 1.2 Problem Statement

When making a large purchase, consumers are typically presented with multiple financing options: pay in cash, take out a loan, or choose a promotional deal (e.g., 0% APR for 24 months, or a cash-back rebate). Most people lack the financial modeling skills to compare these options on a level playing field. They frequently overlook the opportunity cost of paying cash upfront (i.e., the investment returns they forgo), or they misunderstand how a cash-back rebate compares to a low-APR offer. The result is that consumers routinely choose the worse option — sometimes by thousands of dollars.

### 1.3 Goals

- Make it simple for a non-financial consumer to input their scenario and instantly see the true cost of each financing option.
- Surface the "winning" option in plain English, backed by detailed numbers and charts.
- Be purchase-agnostic — useful for cars, appliances, home improvements, medical bills, or any large purchase.
- Require no account or login — fully anonymous, with no user data persisted on the server.

---

## 2. Target Users

**Primary Persona: The Everyday Consumer**

- No formal financial background
- Facing a significant purchase decision (typically $1,000–$100,000+)
- May be comparing a dealer's promotional financing offer against paying cash or taking a personal loan
- Wants a clear answer, not a spreadsheet

**Secondary Persona: The Careful Planner**

- Somewhat financially literate
- Wants to explore how different assumptions (e.g., investment return rates, tax bracket) change the outcome
- May use the app multiple times for the same purchase with different inputs

---

## 3. Scope

### 3.1 In Scope (v1.0)

- Purchase-agnostic financing comparison tool
- Support for the following financing option types:
  - Pay in full (cash)
  - Traditional loan / financing (fixed APR, term)
  - 0% promotional financing
  - Promotional financing with cash-back rebate
  - Promotional financing with price reduction / dealer incentive
  - Other deferred-interest or reduced-rate schemes
- Opportunity cost modeling (investment return on cash not spent)
- Optional inflation adjustment
- Optional tax implication modeling (e.g., deductible interest)
- Single-page input form with live result updates
- Results presented as: plain-English summary recommendation + detailed cost breakdown table + charts
- Fully anonymous — no account required; session state managed server-side per request with no persistent storage of user data
- Responsive design for web (desktop, tablet, mobile)

### 3.2 Out of Scope (v1.0)

- Exportable PDF or shareable reports
- User accounts or cloud-synced history
- Integration with live interest rate data or bank APIs
- Side-by-side comparison of more than 4 options simultaneously
- Business-specific calculations (depreciation schedules, asset write-offs)

---

## 4. Features & Requirements

### 4.1 Input Form

The primary interface is a single-page form. All inputs are visible at once — no wizard or multi-step flow. Results update live as the user types.

#### 4.1.1 Global Inputs (apply to all options)

| Field | Description | Default |
|---|---|---|
| Purchase Price | Total price of the item being purchased | — |
| Investment Return Rate | Annual return rate assumed for invested cash | 7% (S&P 500 historical avg) |
| Enable Inflation Adjustment | Toggle — adjusts all future costs to present value | Off |
| Inflation Rate | Annual inflation rate (shown only if above toggle is on) | 3% |
| Enable Tax Implications | Toggle — account for tax-deductible interest | Off |
| Marginal Tax Rate | User's income tax bracket (shown only if above toggle is on) | 22% |

The investment return rate field must support both a preset selector (Conservative ~4%, Moderate ~7%, Aggressive ~10%) and a free-text manual override.

#### 4.1.2 Per-Option Inputs

Users can define 2–4 financing options to compare. Each option has a type selector that reveals the relevant fields for that option type:

**Pay in Full (Cash)**
- No additional fields. The full purchase price is paid upfront.

**Traditional Loan / Financing**
- Loan APR (%)
- Loan Term (months)
- Down Payment ($)

**0% Promotional Financing**
- Promotional term (months)
- Down Payment ($)
- Deferred interest clause (yes/no toggle) — if yes, adds a warning that unpaid balances accrue back-interest

**Promotional Financing with Cash-Back Rebate**
- Loan APR (%)
- Loan Term (months)
- Cash-Back Amount ($) — applied to reduce effective purchase price
- Down Payment ($)

**Promotional Financing with Price Reduction / Dealer Incentive**
- Discounted Price ($)
- Loan APR (%)
- Loan Term (months)
- Down Payment ($)

**Custom / Other**
- Effective APR (%)
- Loan Term (months)
- Upfront cash required ($)
- Optional label (free text, e.g., "Credit Union Offer")

### 4.2 Calculations Engine

#### 4.2.1 True Total Cost

For each option, the app must calculate and display a **True Total Cost** — the total amount the consumer is effectively "out of pocket" by end of the loan term, accounting for:

1. **Total payments made** (principal + interest over the loan life)
2. **Minus any rebates or price reductions** received
3. **Plus opportunity cost of cash** — for any upfront payment (including a full cash purchase or down payment), model the future value of that money had it been invested instead, then subtract it as a cost (i.e., "what you gave up")
4. **Minus tax savings** (if tax implications are enabled and interest is deductible)
5. **Inflation adjustment** (if enabled, discount all future cash flows to present value)

#### 4.2.2 Opportunity Cost Calculation

- For a cash purchase: model the full purchase price invested at the user-specified annual return rate over the comparison period (defaulting to the longest loan term among the options being compared)
- For options with a down payment: model the down payment invested over the loan term
- Compound annually

#### 4.2.3 Comparison Period Normalization

When options have different terms, all options must be normalized to the same comparison period (the longest term among all active options) so comparisons are apples-to-apples. Any option that ends early should model the remaining freed-up cash (no longer paying a monthly payment) as being invested for the remainder of the comparison period.

### 4.3 Results Display

Results are shown on the same page as the inputs, below or alongside the form, updating live.

#### 4.3.1 Summary Recommendation Card

A prominent card at the top of the results section that:
- Names the winning option (e.g., "Take the 0% Financing")
- States the savings in plain English (e.g., "This saves you $2,340 compared to paying cash, because your $18,000 earns more invested than the loan costs you in fees.")
- Flags any important caveats (e.g., deferred interest risk on promotional offers)

#### 4.3.2 Cost Breakdown Table

A detailed table with one column per financing option, showing:
- Total payments made
- Total interest paid
- Rebate / discount received
- Opportunity cost of upfront cash
- Tax savings (if enabled)
- Inflation adjustment (if enabled)
- **True Total Cost** (bold, highlighted row)

#### 4.3.3 Charts & Visualizations

Two charts are required:

**Chart 1 — True Total Cost Bar Chart**
A simple horizontal or vertical bar chart comparing the True Total Cost of each option. The winning bar is highlighted (e.g., green). This is the primary "at a glance" visual.

**Chart 2 — Cumulative Cost Over Time Line Chart**
A line chart showing how the cumulative out-of-pocket cost of each option evolves month by month over the comparison period. This helps users visualize breakeven points (e.g., when does the cash purchase "catch up" to the financed option due to investment gains?).

### 4.4 Sensitivity / Assumption Exploration

When the user changes the Investment Return Rate (or other global assumptions), all results and charts update. This allows users to answer questions like "what if the market only returns 4% — does that change which option wins?"

No separate "scenario comparison" screen is required in v1.0 — updating the form and resubmitting is sufficient. Where technically feasible with the SSR architecture (e.g., via HTMX partial page replacement), inputs should trigger result updates without a full page reload. A visible "Calculate" submit button must always be present as a fallback.

### 4.5 Session State

- All calculations are performed server-side on each form submission or partial update request.
- No user input or result data is persisted on the server beyond the lifetime of a single request/response cycle.
- Form inputs are repopulated on the rendered response so the user's values are not lost between submissions.
- A "Reset / Start Over" button clears the form to defaults.
- No `localStorage` or client-side persistence is required.

---

## 5. UX & Design Requirements

### 5.1 Layout

- **Desktop:** Two-column layout — inputs on the left, results on the right (or below on narrower screens). Results update live as inputs change.
- **Mobile/Tablet:** Single-column, stacked layout. Results appear below the form. A sticky "View Results" anchor link helps users jump to results without scrolling.

### 5.2 Tone & Language

- All labels, field names, and explanatory copy must use plain, consumer-friendly language.
- Avoid jargon. No tooltips or financial glossary required in v1.0.
- The summary recommendation must always be written in complete, plain English sentences.

### 5.3 Accessibility

- WCAG 2.1 AA compliance
- All form inputs must have visible labels
- Charts must include accessible text alternatives (data tables or ARIA labels)
- Color must not be the sole differentiator in charts (use patterns or labels as well)

---

## 6. Technical Stack & Deployment

### 6.1 Technology Stack

| Layer | Choice |
|---|---|
| Language | Python 3.14 |
| Rendering | Server-side rendering (SSR) as the primary paradigm |
| Interactivity | Minimal client-side JS; prefer HTMX or equivalent for partial page updates where live feedback is needed |
| Charts | Server-rendered SVG charts preferred; a lightweight JS charting library (e.g., Chart.js) is acceptable if SVG proves limiting |
| Styling | To be determined by implementer; must support responsive layout |
| Python environment management | The `uv` tool should be used to manage the Python virtual environment and dependancies |
| Python linting | The `ruff` tool should be used to enforce code quality standards with the preconfigured rules in pyproject.toml |
| Python formatting | The `ruff` tool should also be used to enforce code formatting standards |
| Python type checking | The use of two type checkers, `ty` and `pyrefly` is required.  No other type checkers should be used (no mypy, no pyright, etc). |
| git pre-commit hooks | `prek`, a `pre-commit` drop-in replacement, shall be used to run standards checks before a git commit.

All financial calculations must be implemented in Python on the server. No calculation logic should be duplicated in client-side JavaScript.

All issues reported by `ruff`, `ty`, and `pyrefly` must be addressed.  The proper way to address them is to fix the reported issue, not ignore the error or disable the rule.


### 6.2 Open Source & Self-Hosting

Fathom will be released as an open-source project. The following requirements apply:

- Source code published under a permissive open-source license (e.g., MIT or Apache 2.0)
- A `README` must include clear self-hosting instructions, including how to run locally with minimal dependencies
- Configuration (e.g., default investment return rate, branding) should be overridable via environment variables or a config file to support self-hosters who wish to customize defaults
- The application must run as a single deployable Python process with no external database dependency in the default configuration
- A `Dockerfile` and/or `docker-compose.yml` should be provided for easy containerized self-hosting

---

## 7. Non-Functional Requirements

| Requirement | Target |
|---|---|
| Platform support | Modern browsers (Chrome, Firefox, Safari, Edge); iOS Safari; Android Chrome |
| Performance | Results page rendered and returned within 300ms of form submission |
| Offline support | Not required |
| Privacy | No user input data stored or logged on the server |
| Accessibility | WCAG 2.1 AA |
