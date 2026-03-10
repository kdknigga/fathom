# Phase 1: Calculation Engine - Research

**Researched:** 2026-03-10
**Domain:** Financial calculation engine (Python, Decimal arithmetic, amortization, opportunity cost modeling)
**Confidence:** HIGH

## Summary

Phase 1 builds a pure-computation engine with no web layer. The domain is well-understood financial math (amortization, present value, compound interest) implemented in Python's standard library `decimal` module with `dataclass` domain models. There are no external dependencies needed for the calculation logic itself -- only `pytest` as a dev dependency for verification.

The key complexity lies in the dual-outcome deferred interest model, the decreasing investment pool for opportunity cost, and the comparison period normalization. All formulas are standard and verified. Both `ty` and `pyrefly` pass clean on all patterns needed (dataclasses, Decimal, Enum, list generics).

**Primary recommendation:** Use Python stdlib only (decimal, dataclasses, enum) for all domain models and calculations. Add pytest as the sole dev dependency. Structure as pure functions operating on dataclass inputs/outputs for testability.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Deferred interest modeling: 0% promo has user-specified "post-promo APR" field; toggle for retroactive vs forward-only; engine models BOTH outcomes (paid off in time + not paid off); dual result for promo options
- Opportunity cost: monthly compounding (annual/12); hardcoded presets Conservative 4%, Moderate 7%, Aggressive 10% plus manual override; cash buyer full price as lump-sum investment; loan buyer decreasing investment pool (payments drain it); pool-exhaustion stops opportunity cost; freed-up cash after payoff invested for remainder
- Caveat/risk flagging: three types (deferred_interest_risk, opportunity_cost_dominance, high_interest_total); structured data with type enum + message + severity; generated for ALL options; deferred interest caveat includes break-even date + required payment; opportunity cost dominance flagged on +/-2% sensitivity; high interest when total interest > 30% of purchase price
- Comparison period normalization: no hard max; cash inherits longest loan term; all-cash = instant; engine generates full monthly data series
- Monthly data keeps all calculation logic server-side (TECH-01)

### Claude's Discretion
- Domain model class hierarchy (single class with optionals vs separate classes per option type)
- Internal data structures and method organization
- Test framework choice (pytest assumed)
- Amortization algorithm implementation details
- Exact monthly data series format

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CALC-01 | Compute total payments (principal + interest) using standard amortization | Standard amortization formula verified: M = P*r*(1+r)^n / ((1+r)^n - 1); check value $304.22/mo confirmed |
| CALC-02 | Compute opportunity cost of upfront cash at user-specified return rate | Compound interest with decreasing pool model verified; monthly compounding r = annual_rate / 12 |
| CALC-03 | Normalize all options to same comparison period (longest term) | Straightforward: find max term, extend all shorter options with post-payoff investment modeling |
| CALC-04 | Model freed-up cash after shorter loan ends as invested | After loan payoff, monthly payment amount goes into investment pool for remaining months |
| CALC-05 | Compute True Total Cost = total payments + opportunity cost - rebates - tax savings +/- inflation | Aggregation formula over per-option computed values |
| CALC-06 | Apply inflation adjustment (discount future cash flows to present value) | PV = FV / (1 + r_monthly)^month; verified r_monthly = annual_inflation / 12 |
| CALC-07 | Compute tax savings (deductible interest x marginal tax rate) | Per-month interest portion from amortization schedule times tax rate |
| CALC-08 | Use Decimal arithmetic for all monetary calculations | Python stdlib decimal module; initialize from strings; quantize(Decimal("0.01")) for output |
| TECH-01 | All financial calculations server-side Python | Pure Python module, no JS -- architectural constraint satisfied by design |
| TECH-02 | No data persisted beyond request/response | Stateless computation functions -- no storage by design |
| TECH-04 | Single deployable Python process, no external database | No database needed for calculation engine |
| QUAL-01 | All code passes ruff check (no #noqa) | Ruff rules configured in pyproject.toml; D rules require docstrings |
| QUAL-02 | All code passes ruff format | Black-compatible, double quotes, 88 char lines |
| QUAL-03 | All code passes ty check (no #type:ignore) | Verified: ty passes clean on dataclass+Decimal+Enum patterns |
| QUAL-04 | All code passes pyrefly check | Verified: pyrefly passes clean on same patterns |
| QUAL-05 | All public modules/classes/functions have docstrings | Ruff D rules enforce this; use multi-line-summary-second-line style |
| QUAL-06 | prek pre-commit hooks pass on all commits | Hooks configured: pre-commit-hooks, ruff, ty, pyrefly |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| decimal (stdlib) | Python 3.14 | All monetary arithmetic | Required by CALC-08; no float rounding errors |
| dataclasses (stdlib) | Python 3.14 | Domain models (input/output types) | Clean, typed, immutable-friendly; both ty and pyrefly support fully |
| enum (stdlib) | Python 3.14 | Option types, caveat types, severity levels | Type-safe categorical values |

### Supporting (Dev Dependencies)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | >=8.0 | Test framework | All automated verification; add as dev dependency |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| dataclasses | Pydantic | Pydantic adds runtime validation but is overkill for internal engine with no user input parsing in this phase; adds dependency; potential type checker friction |
| dataclasses | attrs | Similar to dataclasses but external dependency for minimal gain |
| decimal.Decimal | int-cents | Storing cents as integers avoids Decimal overhead but loses natural readability and makes formulas harder to verify |

**Installation:**
```bash
uv add --dev pytest
```

No runtime dependencies needed -- everything is Python stdlib.

## Architecture Patterns

### Recommended Project Structure
```
src/fathom/
    __init__.py          # main() entry point (existing)
    models.py            # Domain models (dataclasses, enums)
    amortization.py      # Amortization and payment calculations
    opportunity.py       # Opportunity cost / investment pool modeling
    inflation.py         # Present value discounting
    tax.py               # Tax savings computation
    caveats.py           # Caveat generation logic
    engine.py            # Top-level compare() function orchestrating all modules
tests/
    __init__.py
    conftest.py          # Shared fixtures (standard options, global settings)
    test_amortization.py # Amortization formula tests
    test_opportunity.py  # Opportunity cost tests
    test_inflation.py    # Inflation adjustment tests
    test_tax.py          # Tax savings tests
    test_caveats.py      # Caveat generation tests
    test_engine.py       # Integration tests (full comparison scenarios)
```

### Pattern 1: Pure Functions on Dataclasses
**What:** All calculation functions take dataclass inputs and return dataclass outputs. No side effects, no state.
**When to use:** Every calculation module.
**Example:**
```python
from decimal import Decimal
from fathom.models import FinancingOption, GlobalSettings, OptionResult

def compute_option_result(
    option: FinancingOption,
    settings: GlobalSettings,
    comparison_period: int,
) -> OptionResult:
    """Compute True Total Cost for a single financing option."""
    ...
```

### Pattern 2: Decimal Initialization from Strings
**What:** Always create Decimal from string literals, never floats.
**When to use:** Every constant, every user-facing value.
**Example:**
```python
# CORRECT
rate = Decimal("0.06")
zero = Decimal("0")
penny = Decimal("0.01")

# WRONG -- introduces float imprecision
rate = Decimal(0.06)  # noqa: this creates Decimal('0.05999999999999...')
```

### Pattern 3: Quantize at Boundaries Only
**What:** Keep full precision during intermediate calculations. Only quantize (round to cents) at output boundaries.
**When to use:** When producing final payment amounts, total costs, display values.
**Example:**
```python
from decimal import Decimal, ROUND_HALF_UP

CENTS = Decimal("0.01")

def quantize_money(value: Decimal) -> Decimal:
    """Round to cents using banker-standard rounding."""
    return value.quantize(CENTS, rounding=ROUND_HALF_UP)
```

### Pattern 4: Explicit Zero-Interest Guard
**What:** The amortization formula divides by `(1+r)^n - 1`, which is zero when r=0. Always handle 0% APR as a special case.
**When to use:** Any function that uses the amortization formula.
**Example:**
```python
def monthly_payment(principal: Decimal, apr: Decimal, term: int) -> Decimal:
    """Compute monthly payment using standard amortization."""
    if apr == Decimal("0"):
        return principal / term
    r = apr / 12
    payment = principal * r * (1 + r) ** term / ((1 + r) ** term - 1)
    return quantize_money(payment)
```

### Pattern 5: Dual-Outcome for Promo Options
**What:** 0% promo options return TWO OptionResults -- one for "paid off in time" and one for "not paid off."
**When to use:** Any option with promo period and deferred interest.
**Example:**
```python
@dataclass
class PromoResult:
    """Dual outcome for promotional financing."""

    paid_on_time: OptionResult    # disciplined scenario
    not_paid_on_time: OptionResult  # trap scenario
    required_monthly_payment: Decimal  # to clear before promo expires
    break_even_date: int  # month number
```

### Anti-Patterns to Avoid
- **Float anywhere in money pipeline:** Even a single `float()` call contaminates Decimal precision. Use `Decimal(str(value))` if converting from external sources.
- **Rounding in intermediate steps:** Causes cumulative errors over 36+ months. Only round at final output.
- **Mutable state in calculation functions:** Makes testing harder and introduces hidden dependencies. Return new dataclass instances.
- **Mixing monthly and annual rates:** Always convert to monthly at the boundary and work in monthly units internally.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Decimal rounding | Custom rounding logic | `Decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)` | Edge cases with negative numbers, ties, precision |
| Test framework | Custom assertions | pytest with `Decimal("304.22")` exact comparisons | pytest handles Decimal equality natively |
| Amortization formula | Iterative guess-and-check | Direct formula: `P*r*(1+r)^n / ((1+r)^n - 1)` | Closed-form solution is exact and fast |

**Key insight:** The entire calculation engine uses Python stdlib. No external libraries needed for computation. The complexity is in correctly implementing financial formulas and edge cases, not in tooling.

## Common Pitfalls

### Pitfall 1: Float Contamination
**What goes wrong:** A single `float()` or float literal in the Decimal pipeline introduces binary rounding errors that accumulate over 36+ payment periods.
**Why it happens:** Python operators auto-coerce: `Decimal("0.06") / 12` works, but `Decimal("0.06") * 0.5` raises TypeError. Developers might use `float()` to "fix" it.
**How to avoid:** Use `Decimal("12")` not `12` for Decimal division (though int divisors work fine). Never mix Decimal with float. Decimal + int is safe; Decimal + float is not.
**Warning signs:** `TypeError: unsupported operand type(s) for *: 'decimal.Decimal' and 'float'`

### Pitfall 2: Amortization Off-by-One
**What goes wrong:** Final payment doesn't match expected total because of accumulated rounding. Last payment must be adjusted to clear exact remaining balance.
**Why it happens:** Quantizing each monthly payment to cents means the sum of 36 payments of $304.22 = $10,951.92, but the exact total might differ by a penny.
**How to avoid:** Track remaining balance. Last payment = remaining balance + final interest charge. Test against known values.
**Warning signs:** Total payments off by $0.01-$0.02 from expected values.

### Pitfall 3: Zero-Rate Division by Zero
**What goes wrong:** Amortization formula has `(1+r)^n - 1` in denominator. When r=0 (cash or 0% promo), this is division by zero.
**Why it happens:** 0% promotional financing is a core use case, not an edge case.
**How to avoid:** Explicit guard: `if apr == Decimal("0"): return principal / term`.
**Warning signs:** `decimal.InvalidOperation` or `ZeroDivisionError`.

### Pitfall 4: Investment Pool Going Negative
**What goes wrong:** Monthly payments exceed investment pool balance, resulting in negative "invested" amounts.
**Why it happens:** When the loan payment is large relative to the initial investment, the pool depletes before term ends.
**How to avoid:** Clamp pool to zero: `pool = max(pool, Decimal("0"))`. Once pool is zero, remaining payments are pure out-of-pocket with no opportunity cost. Track the month when pool hits zero.
**Warning signs:** Negative opportunity cost values.

### Pitfall 5: Type Checker Conflicts Between ty and pyrefly
**What goes wrong:** Code passes one type checker but fails the other.
**Why it happens:** `ty` and `pyrefly` have different type inference engines and may disagree on edge cases.
**How to avoid:** Test patterns early (verified: dataclass + Decimal + Enum + list generics pass both). Use explicit type annotations everywhere. Avoid advanced generics or Protocol types unless needed.
**Warning signs:** One checker passes while the other reports errors on the same code.

### Pitfall 6: Docstring Style Violations
**What goes wrong:** Ruff's D rules reject docstrings that don't match the configured style.
**Why it happens:** pyproject.toml ignores D203 and D212, meaning: no blank line before class docstring, and multi-line summary starts on second line (Google/numpy style).
**How to avoid:** Use this pattern:
```python
def function() -> None:
    """One-line summary.

    Extended description if needed.
    """
```
For classes, no blank line between class definition and docstring.
**Warning signs:** `D` rule violations from `ruff check`.

## Code Examples

### Standard Amortization (Verified)
```python
# Verified: $10,000 / 6% APR / 36 months = $304.22/month
from decimal import Decimal, ROUND_HALF_UP, getcontext

getcontext().prec = 28  # Default is 28, but be explicit

CENTS = Decimal("0.01")


def monthly_payment(principal: Decimal, apr: Decimal, term_months: int) -> Decimal:
    """Compute monthly payment using standard amortization formula.

    Args:
        principal: Loan amount after down payment.
        apr: Annual percentage rate as decimal (e.g., Decimal("0.06") for 6%).
        term_months: Number of monthly payments.

    Returns:
        Monthly payment amount rounded to cents.
    """
    if apr == Decimal("0"):
        return (principal / term_months).quantize(CENTS, rounding=ROUND_HALF_UP)
    r = apr / 12
    n = term_months
    payment = principal * r * (1 + r) ** n / ((1 + r) ** n - 1)
    return payment.quantize(CENTS, rounding=ROUND_HALF_UP)
```

### Present Value Discounting (Inflation Adjustment)
```python
# Verified: $304.22 at month 12, 3% annual inflation -> PV = $295.24
def present_value(
    future_value: Decimal,
    annual_inflation: Decimal,
    month: int,
) -> Decimal:
    """Discount a future value to present value.

    Args:
        future_value: Nominal future amount.
        annual_inflation: Annual inflation rate (e.g., Decimal("0.03")).
        month: Number of months from present.

    Returns:
        Present value of the future amount.
    """
    r_monthly = annual_inflation / 12
    return future_value / (1 + r_monthly) ** month
```

### Opportunity Cost with Decreasing Pool
```python
# Verified: $8,000 pool, $304.22/mo payment, 7% return -> pool exhausts before 36 months
def compute_opportunity_cost(
    initial_pool: Decimal,
    monthly_payment: Decimal,
    annual_return: Decimal,
    months: int,
) -> tuple[Decimal, list[Decimal]]:
    """Compute opportunity cost with decreasing investment pool.

    Pool grows by monthly return, then payment is deducted.
    When pool hits zero, remaining payments are pure out-of-pocket.

    Returns:
        Tuple of (total_opportunity_cost, monthly_balances).
    """
    r_monthly = annual_return / 12
    pool = initial_pool
    total_returns = Decimal("0")
    balances: list[Decimal] = []

    for _month in range(months):
        if pool <= Decimal("0"):
            balances.append(Decimal("0"))
            continue
        monthly_return = pool * r_monthly
        total_returns += monthly_return
        pool = pool + monthly_return - monthly_payment
        if pool < Decimal("0"):
            pool = Decimal("0")
        balances.append(pool)

    return total_returns, balances
```

### Tax Savings Calculation
```python
def compute_tax_savings(
    interest_payments: list[Decimal],
    marginal_tax_rate: Decimal,
) -> Decimal:
    """Compute tax savings from deductible interest.

    Args:
        interest_payments: Per-month interest portions from amortization.
        marginal_tax_rate: User's marginal tax rate (e.g., Decimal("0.22")).

    Returns:
        Total tax savings over the loan term.
    """
    total_interest = sum(interest_payments)
    return total_interest * marginal_tax_rate
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `float` for money | `decimal.Decimal` | Always been best practice | Eliminates binary rounding errors |
| `namedtuple` for models | `@dataclass` | Python 3.7+ (2018) | Mutable defaults, type annotations, field metadata |
| `unittest.TestCase` | `pytest` functions | Mature since ~2015 | Less boilerplate, better assertions, fixtures |
| Manual type stubs | Built-in generics (`list[X]`) | Python 3.9+ (2020) | `list[MonthlyDataPoint]` instead of `List[MonthlyDataPoint]` |

**Deprecated/outdated:**
- `typing.List`, `typing.Dict`, etc.: Use built-in `list`, `dict` directly (Python 3.9+)
- `unittest` style: Use pytest functions with plain `assert` statements

## Open Questions

1. **Domain model: single class vs. separate per option type**
   - What we know: CONTEXT.md gives Claude discretion on this. Six option types with different field requirements.
   - What's unclear: Whether a single `FinancingOption` with optional fields or a class hierarchy is cleaner for ty/pyrefly.
   - Recommendation: Use a single `@dataclass` with `OptionType` enum and optional fields. Simpler for both type checkers. Validation logic can check required fields based on type. Avoids complex inheritance that may cause type checker divergence.

2. **Monthly data series format**
   - What we know: CONTEXT.md gives Claude discretion. Data feeds Phase 3 charts.
   - What's unclear: Exact fields needed for chart rendering.
   - Recommendation: Use `MonthlyDataPoint(month, payment, investment_balance, cumulative_cost)` as a starting point. Can add fields later without breaking the interface.

3. **Rounding policy for intermediate amortization steps**
   - What we know: Quantize at output boundaries only. But per-month interest/principal split is used for tax savings (CALC-07).
   - What's unclear: Whether to quantize each month's interest for tax calculations or keep full precision.
   - Recommendation: Track per-month interest at full precision internally. Quantize only the final tax savings total. This avoids accumulated rounding errors while still producing correct per-month data for charts.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=8.0 (must be added as dev dependency) |
| Config file | None -- Wave 0 must add pytest config to pyproject.toml |
| Quick run command | `uv run pytest tests/ -x -q` |
| Full suite command | `uv run pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CALC-01 | Standard amortization produces correct payments | unit | `uv run pytest tests/test_amortization.py -x` | No -- Wave 0 |
| CALC-02 | Opportunity cost of upfront cash computed correctly | unit | `uv run pytest tests/test_opportunity.py -x` | No -- Wave 0 |
| CALC-03 | Normalization to longest comparison period | unit | `uv run pytest tests/test_engine.py::test_normalization -x` | No -- Wave 0 |
| CALC-04 | Freed-up cash after payoff invested | unit | `uv run pytest tests/test_opportunity.py::test_freed_cash -x` | No -- Wave 0 |
| CALC-05 | True Total Cost formula aggregation | integration | `uv run pytest tests/test_engine.py::test_true_total_cost -x` | No -- Wave 0 |
| CALC-06 | Inflation adjustment (PV discounting) | unit | `uv run pytest tests/test_inflation.py -x` | No -- Wave 0 |
| CALC-07 | Tax savings calculation | unit | `uv run pytest tests/test_tax.py -x` | No -- Wave 0 |
| CALC-08 | Decimal arithmetic throughout | unit | `uv run pytest tests/test_amortization.py::test_decimal_types -x` | No -- Wave 0 |
| TECH-01 | All calculations server-side | architectural | N/A -- enforced by design (no JS in this phase) | N/A |
| TECH-02 | No persistence | architectural | N/A -- no database code exists | N/A |
| TECH-04 | Single process, no DB | architectural | N/A -- no external dependencies | N/A |
| QUAL-01 | ruff check clean | lint | `uv run ruff check .` | N/A -- existing |
| QUAL-02 | ruff format clean | format | `uv run ruff format --check .` | N/A -- existing |
| QUAL-03 | ty check clean | type | `uv run ty check` | N/A -- existing |
| QUAL-04 | pyrefly check clean | type | `uv run pyrefly check` | N/A -- existing |
| QUAL-05 | Docstrings on all public API | lint | Covered by ruff D rules | N/A -- existing |
| QUAL-06 | prek hooks pass | hooks | `uv run prek run` | N/A -- existing |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/ -x -q && uv run ruff check . && uv run ruff format --check . && uv run ty check && uv run pyrefly check`
- **Per wave merge:** `uv run pytest tests/ -v && uv run prek run`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `uv add --dev pytest` -- add pytest as dev dependency
- [ ] `pyproject.toml` -- add `[tool.pytest.ini_options]` section with `testpaths = ["tests"]`
- [ ] `tests/__init__.py` -- package init
- [ ] `tests/conftest.py` -- shared fixtures (standard test options, global settings)
- [ ] `tests/test_amortization.py` -- covers CALC-01, CALC-08
- [ ] `tests/test_opportunity.py` -- covers CALC-02, CALC-04
- [ ] `tests/test_inflation.py` -- covers CALC-06
- [ ] `tests/test_tax.py` -- covers CALC-07
- [ ] `tests/test_caveats.py` -- covers caveat generation
- [ ] `tests/test_engine.py` -- covers CALC-03, CALC-05 (integration)

## Sources

### Primary (HIGH confidence)
- Python stdlib decimal module -- tested directly with Python 3.14 in project environment
- Python stdlib dataclasses -- tested with ty and pyrefly in project environment
- Amortization formula -- verified: $10,000 / 6% / 36mo = $304.22/mo (matches success criteria)
- Present value formula -- verified: $304.22 at month 12, 3% inflation = $295.24 PV
- Opportunity cost model -- verified: decreasing pool exhausts correctly with given parameters
- pyproject.toml ruff configuration -- read directly from project

### Secondary (MEDIUM confidence)
- [pytest PyPI](https://pypi.org/project/pytest/) -- latest version ~8.x-9.x
- [Python decimal docs](https://docs.python.org/3/library/decimal.html) -- ROUND_HALF_UP, quantize, precision

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- Python stdlib only, no external dependencies for computation, verified with project's type checkers
- Architecture: HIGH -- Pure functions on dataclasses is well-established; verified patterns pass ty+pyrefly
- Pitfalls: HIGH -- Financial calculation pitfalls are well-documented; verified key edge cases (zero rate, pool exhaustion, rounding)
- Formulas: HIGH -- All formulas verified computationally against known check values

**Research date:** 2026-03-10
**Valid until:** 2026-04-10 (stable domain, stdlib only)
