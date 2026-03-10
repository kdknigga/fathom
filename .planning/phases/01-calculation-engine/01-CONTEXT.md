# Phase 1: Calculation Engine - Context

**Gathered:** 2026-03-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Domain models, financial calculation logic with Decimal arithmetic, and code quality tooling. The engine accepts financing option configurations and global settings, and returns a ComparisonResult with True Total Cost for each option, monthly data series for charts, and structured caveats. No UI, no web layer — pure computation with automated tests against known values.

</domain>

<decisions>
## Implementation Decisions

### Deferred interest modeling
- 0% promo option has a user-specified "post-promo APR" field (not a fixed default)
- Toggle for retroactive vs forward-only interest calculation (both models supported)
- Engine models BOTH outcomes: "paid off in time" and "not paid off" — dual result for promo options
- "Paid off in time" scenario calculates the required monthly payment to clear balance before promo expiry
- "Not paid off" scenario amortizes remaining balance + retroactive interest at post-promo APR, matched to comparison period
- When deferred interest is toggled OFF, remaining balance still converts to regular APR on remaining balance (not truly free)
- Post-promo APR field is always relevant for 0% promo options regardless of deferred interest toggle
- 0% promo supports optional down payment

### Opportunity cost assumptions
- Monthly compounding applied uniformly (annual rate / 12), regardless of investment vehicle type
- Hardcoded return rate presets: Conservative 4%, Moderate 7%, Aggressive 10% (plus manual override)
- Cash buyer: full purchase price modeled as lump-sum investment from month 1
- Loan buyer: purchase price minus down payment stays invested; investment balance decreases as monthly payments are made (payments come from investment pool)
- When investment pool hits zero, remaining payments are pure out-of-pocket cost with no further opportunity cost
- After shorter loan payoff, freed-up monthly payments are invested for remainder of comparison period (CALC-04)

### Caveat/risk flagging
- Three caveat types: deferred interest risk, opportunity cost dominance, high interest total
- Caveats returned as structured data: type enum + human-readable message + severity level
- Caveats generated for ALL options, not just the winner
- Deferred interest caveat includes break-even date AND required monthly payment to avoid penalty
- Opportunity cost dominance: flagged when winner changes if return rate shifts ±2% (sensitivity check)
- High interest total: flagged when total interest exceeds 30% of purchase price

### Comparison period normalization
- No hard maximum on comparison period — accept any term length
- Cash purchase inherits comparison period from longest loan term among other options
- All-cash comparison: instant — all options cost the same (no investment modeling needed)
- Engine generates full monthly data series (payments, investment balance, cumulative cost) for chart rendering in Phase 3
- Monthly data keeps all calculation logic server-side (TECH-01 compliance)

### Claude's Discretion
- Domain model class hierarchy (single class with optionals vs separate classes per option type)
- Internal data structures and method organization
- Test framework choice (pytest assumed)
- Amortization algorithm implementation details
- Exact monthly data series format

</decisions>

<specifics>
## Specific Ideas

- Dual-outcome model for deferred interest is key — users should see the "trap" cost alongside the "disciplined" cost
- Investment pool is a decreasing balance, not a static lump sum — payments drain it realistically
- Sensitivity check (±2% return rate) for opportunity cost dominance is a concrete, testable threshold
- Break-even date with required payment amount makes the deferred interest caveat actionable, not just a warning

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield codebase. Only `src/fathom/__init__.py` with a hello-world `main()` exists.

### Established Patterns
- `pyproject.toml` fully configured: ruff (extensive rules including D docstring rules), ty, pyrefly, prek
- Python 3.14 target, `uv` for package management
- Entry point: `src/fathom/__init__.py:main()`
- No dependencies yet — `dependencies = []`

### Integration Points
- Engine output types will be consumed by Phase 2 (web layer) and Phase 3 (results display)
- Monthly data series feeds directly into cumulative cost chart (RSLT-06)
- Structured caveats feed into recommendation card (RSLT-03)

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-calculation-engine*
*Context gathered: 2026-03-10*
