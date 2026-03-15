# Phase 13: Centralize Monetary Rounding - Research

**Researched:** 2026-03-15
**Domain:** Python refactoring (Decimal rounding deduplication)
**Confidence:** HIGH

## Summary

This phase is a mechanical refactor with zero ambiguity. Five modules define identical `CENTS = Decimal("0.01")` and `quantize_money()` pairs. The task is to extract these into a new `src/fathom/money.py` module and update all imports. No behavioral change, no new dependencies, no design decisions.

The codebase has 283 tests that serve as a regression safety net. No tests directly import `quantize_money` or `CENTS` -- they exercise it indirectly through the calculation modules. This means the refactor only touches production code imports; test files need zero changes.

**Primary recommendation:** Create `money.py` with `CENTS` and `quantize_money()`, update 6 files (5 definers + 1 consumer), delete duplicate definitions, run full test suite to confirm zero behavior change.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- This is a mechanical refactor with no user-facing decisions
- All gray areas are technical implementation details (Claude's discretion)

### Claude's Discretion
- Module structure of `money.py` (function, constant, docstrings)
- Import update strategy across 5 consumer modules
- Whether to re-export from consumer modules for backward compatibility (not needed -- all internal)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ENG-03 | Monetary rounding utility centralized into single `money.py` module, replacing 5 duplicate `quantize_money()` definitions | All 5 duplicate locations identified with exact line numbers; `engine.py` consumer import identified; `money.py` module structure defined below |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| decimal (stdlib) | Python 3.14 | Precise monetary arithmetic | Already in use; `Decimal.quantize()` is the standard Python pattern for rounding |

No new dependencies required. This phase uses only the Python standard library.

## Architecture Patterns

### New Module: `src/fathom/money.py`

```python
"""
Centralized monetary rounding utilities.

All monetary rounding in Fathom flows through this module to ensure
consistent two-decimal-place (cent) precision across calculations.
"""

from decimal import Decimal

CENTS = Decimal("0.01")


def quantize_money(value: Decimal) -> Decimal:
    """Round a Decimal value to the nearest cent (two decimal places)."""
    return value.quantize(CENTS)
```

### Files to Modify (6 total)

| File | Change | Lines Affected |
|------|--------|----------------|
| `src/fathom/money.py` | **CREATE** -- new canonical module | New file |
| `src/fathom/amortization.py` | Remove `CENTS` + `quantize_money` definition; add `from fathom.money import quantize_money` | Lines 13-18 |
| `src/fathom/opportunity.py` | Remove `CENTS` + `quantize_money` definition; add `from fathom.money import quantize_money` | Lines 15-20 |
| `src/fathom/inflation.py` | Remove `CENTS` + `quantize_money` definition; add `from fathom.money import quantize_money` | Lines 11-16 |
| `src/fathom/caveats.py` | Remove `CENTS` + `quantize_money` definition; add `from fathom.money import quantize_money` | Lines 23-28 |
| `src/fathom/tax.py` | Remove `CENTS` + `quantize_money` definition; add `from fathom.money import quantize_money` | Lines 10-15 |
| `src/fathom/engine.py` | Change `from fathom.amortization import amortization_schedule, quantize_money` to separate imports: `from fathom.money import quantize_money` and `from fathom.amortization import amortization_schedule` | Line 11 |

### Files NOT Modified
- **No test files** -- zero tests import `quantize_money` or `CENTS` directly
- **No other source files** -- grep confirms no other references

### Import Pattern

Each of the 5 consumer modules replaces its local definition with:
```python
from fathom.money import quantize_money
```

The `CENTS` constant does NOT need to be exported -- it is only used internally by `quantize_money()`.

### Anti-Patterns to Avoid
- **Do NOT re-export from consumer modules:** There is no backward compatibility concern since nothing imports `quantize_money` from `opportunity.py`, `inflation.py`, `caveats.py`, or `tax.py`. Only `engine.py` imports it from `amortization.py`, and that import gets redirected to `money.py`.
- **Do NOT add rounding mode parameters:** All 5 definitions use the default `ROUND_HALF_EVEN`. Adding configurability would change the function signature and is out of scope.
- **Do NOT rename the function:** `quantize_money` is used 25+ times across the codebase. Keep the name identical for minimal diff.

## Don't Hand-Roll

Not applicable -- this phase uses only stdlib `decimal.Decimal.quantize()`. No libraries needed.

## Common Pitfalls

### Pitfall 1: Circular Imports
**What goes wrong:** If `money.py` were to import from any calculation module, it could create a circular dependency.
**How to avoid:** `money.py` imports ONLY from `decimal` (stdlib). It has zero intra-project dependencies. This is inherently safe.

### Pitfall 2: Missing an Import Update
**What goes wrong:** Leaving a stale local `quantize_money` definition means two copies exist, defeating the purpose.
**How to avoid:** After refactoring, grep for `def quantize_money` -- it must appear in exactly ONE file (`money.py`). Grep for `CENTS = Decimal` -- same rule.
**Verification command:** `grep -rn "def quantize_money\|CENTS = Decimal" src/fathom/`

### Pitfall 3: Ruff Import Ordering
**What goes wrong:** Adding `from fathom.money import quantize_money` may violate ruff's `I` (isort) rules if placed in wrong position relative to other imports.
**How to avoid:** Run `uv run ruff check --fix .` after changes to auto-sort imports.

### Pitfall 4: Missing Module Docstring
**What goes wrong:** Ruff's `D` rules require module docstrings on all public modules. A new `money.py` without a docstring will fail linting.
**How to avoid:** Include a module docstring (shown in the pattern above).

## Code Examples

### Before (repeated in 5 files)
```python
from decimal import Decimal

CENTS = Decimal("0.01")

def quantize_money(value: Decimal) -> Decimal:
    """Round a Decimal value to the nearest cent (two decimal places)."""
    return value.quantize(CENTS)
```

### After (in each consumer)
```python
from fathom.money import quantize_money
```

### engine.py Before
```python
from fathom.amortization import amortization_schedule, quantize_money
```

### engine.py After
```python
from fathom.amortization import amortization_schedule
from fathom.money import quantize_money
```

## State of the Art

Not applicable -- this is a pure Python refactoring using stable stdlib features (`decimal` module unchanged since Python 3.3).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/ -x -q` |
| Full suite command | `uv run pytest tests/` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ENG-03 | All monetary rounding uses single `money.py` | Existing regression suite (no new tests needed) | `uv run pytest tests/ -x -q` | N/A -- existing tests cover behavior |

### Verification Commands
| Check | Command | Purpose |
|-------|---------|---------|
| No duplicate definitions | `grep -rn "def quantize_money" src/fathom/` | Must show exactly 1 match in `money.py` |
| No duplicate CENTS | `grep -rn "CENTS = Decimal" src/fathom/` | Must show exactly 1 match in `money.py` |
| Full test suite | `uv run pytest tests/` | All 283 tests pass -- zero behavior change |
| Ruff lint | `uv run ruff check .` | Clean |
| Ruff format | `uv run ruff format --check .` | Clean |
| ty type check | `uv run ty check` | Clean |
| pyrefly type check | `uv run pyrefly check` | Clean |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/ -x -q` + `uv run ruff check .`
- **Per wave merge:** `uv run pytest tests/` + full quality gate suite
- **Phase gate:** All quality gates green before `/gsd:verify-work`

### Wave 0 Gaps
None -- existing test infrastructure covers all phase requirements. This is a pure refactor; the 283 existing tests serve as the regression suite. No new test files needed.

## Sources

### Primary (HIGH confidence)
- Direct codebase inspection of all 5 duplicate locations (exact line numbers verified)
- `grep` verification of all `quantize_money` and `CENTS` references across `src/` and `tests/`
- `pytest --co` enumeration of all 283 tests confirming zero direct `quantize_money` imports in tests

### Secondary
None needed -- this phase requires no external library knowledge.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- stdlib `decimal` only, no external deps
- Architecture: HIGH -- exact file changes enumerated and verified against codebase
- Pitfalls: HIGH -- common Python refactoring pitfalls, well-understood

**Research date:** 2026-03-15
**Valid until:** Indefinite -- this is a one-time mechanical refactor of stable code
