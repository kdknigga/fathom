# Phase 13: Centralize Monetary Rounding - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Extract 5 duplicate `quantize_money()` + `CENTS` definitions into a single `src/fathom/money.py` module. Pure refactor — zero behavior change.

</domain>

<decisions>
## Implementation Decisions

### Scope
- This is a mechanical refactor with no user-facing decisions
- All gray areas are technical implementation details (Claude's discretion)

### Claude's Discretion
- Module structure of `money.py` (function, constant, docstrings)
- Import update strategy across 5 consumer modules
- Whether to re-export from consumer modules for backward compatibility (not needed — all internal)

</decisions>

<specifics>
## Specific Ideas

No specific requirements — the roadmap and requirements fully specify this phase.

</specifics>

<code_context>
## Existing Code Insights

### Duplicate Locations (5 identical definitions)
- `src/fathom/amortization.py`: lines 13-18 (CENTS + quantize_money)
- `src/fathom/opportunity.py`: lines 15-20
- `src/fathom/inflation.py`: lines 11-16
- `src/fathom/caveats.py`: lines 23-28
- `src/fathom/tax.py`: lines 10-15

### Consumer
- `src/fathom/engine.py`: imports `quantize_money` from `amortization` (line 11)

### Pattern
- All 5 are identical: `CENTS = Decimal("0.01")` and `value.quantize(CENTS)`
- Default rounding mode (ROUND_HALF_EVEN) used everywhere — no custom rounding

### Integration Points
- New `money.py` becomes the canonical import for all 5 modules + engine.py

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 13-centralize-monetary-rounding*
*Context gathered: 2026-03-15*
