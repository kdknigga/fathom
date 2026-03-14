# Phase 12: Python Linting and Typechecking Cleanup - Research

**Researched:** 2026-03-14
**Domain:** Ruff linting rule expansion, code complexity refactoring
**Confidence:** HIGH

## Summary

This phase expands ruff's lint rule coverage by enabling PL (pylint), PT (pytest), DTZ (datetime), T20 (print), and COM812 (trailing commas), then fixes all resulting violations. The codebase currently passes clean with existing rules. Enabling new rules surfaces 187 violations (excluding PLR2004 per user decision), of which 77 are auto-fixable. The remaining 110 require manual fixes ranging from trivial (per-file-ignores for tests) to moderate (refactoring 2 complex production functions).

The work splits cleanly into three waves: (1) config changes + auto-fix, (2) production code manual fixes + complexity refactoring, (3) test code cleanup. Production code has only 42 violations (32 auto-fixable), while test code has 145 violations (most addressed by per-file-ignores for T201 and PLC0415).

**Primary recommendation:** Apply config changes and auto-fixes first, then refactor the two complex production functions (charts.py:prepare_line_chart, forms.py:validate_by_type), then handle test-specific rules via per-file-ignores.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Enable rule categories: PL (pylint), PT (pytest), DTZ (datetime), T20 (print), COM812 (trailing commas)
- Exclude PLR2004 (magic-value-comparison) -- too noisy (102 hits), low signal for this codebase
- Keep D212 (multi-line-summary-first-line) ignored -- current convention is D213 (summary on second line)
- Keep E501 (line-too-long) ignored -- ruff formatter handles most cases
- Remove COM812 from ignore list -- enable trailing comma enforcement (71 auto-fixable violations)
- Apply `ruff --fix` for all safe auto-fixable violations (trailing commas, if-stmt-min-max, redundant-numeric-union, etc.)
- Manual fixes only for violations that require judgment (complexity refactoring, print replacement)
- Refactor complex functions to comply with ruff's default thresholds (50 statements, 10 McCabe complexity, 12 branches)
- Fix PLR1714 (repeated-equality-comparison) -- use set membership check
- Fix PLW2901 (redefined-loop-name) -- rename loop variable
- Fix PLR0911 (too-many-return-statements) -- refactor to reduce returns
- T20 enabled globally as a guardrail against print() in production code
- T201 added to per-file-ignores for tests/**/*.py -- test verification scripts use print for output
- No production code currently has print statements -- rule prevents future additions

### Claude's Discretion
- PLR0913 (too-many-arguments): Claude reviews the 1 violation and decides whether to refactor (parameter object) or ignore based on whether it improves the code
- CLI entry point prints: Claude checks `__init__.py:main()` and decides between per-file ignore or converting to logging based on what's there
- Exact refactoring approach for complex functions -- extract helpers, restructure conditionals, etc.

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| ruff | >=0.15.5 | Linting and formatting | Already in use, configured in pyproject.toml |
| ty | >=0.0.21 | Type checking | Already in use, must remain clean |
| pyrefly | >=0.55.0 | Type checking | Already in use, must remain clean |

No new dependencies required. This phase modifies only configuration and existing code.

## Architecture Patterns

### Violation Inventory (Verified via `ruff check`)

**Production code (src/):** 42 violations
| Rule | Count | Fix Type | Description |
|------|-------|----------|-------------|
| COM812 | 26 | Auto-fix | Missing trailing commas |
| PLR1730 | 6 | Auto-fix | if-stmt-min-max (use min/max builtins) |
| PLC0415 | 3 | Manual | Import outside top-level (in __init__.py and app.py) |
| PLR0915 | 2 | Refactor | Too many statements (charts.py, forms.py) |
| PLR0912 | 2 | Refactor | Too many branches (charts.py, forms.py) |
| DTZ011 | 1 | Manual | date.today() without timezone (routes.py) |
| PLR0911 | 1 | Refactor | Too many return statements (formatting.py) |
| PLW2901 | 1 | Manual | Redefined loop variable (forms.py) |

**Test code (tests/):** 145 violations
| Rule | Count | Fix Type | Description |
|------|-------|----------|-------------|
| T201 | 46 | Per-file-ignore | print statements (playwright_verify.py) |
| COM812 | 45 | Auto-fix | Missing trailing commas |
| PLC0415 | 44 | Per-file-ignore | Import outside top-level (playwright_verify.py) |
| PLR0915 | 4 | Per-file-ignore | Too many statements (playwright_verify.py) |
| PT015 | 3 | Manual | pytest-assert-always-false (test_forms.py) |
| PLR0912 | 1 | Per-file-ignore | Too many branches (playwright_verify.py) |
| PLR0913 | 1 | Discretion | Too many arguments (test_results_helpers.py) |
| PLR1714 | 1 | Manual | Repeated equality comparison (playwright_verify.py) |

### pyproject.toml Changes Required

**select line:** Add "PL", "PT", "DTZ", "T20" to the select list.

**ignore line:** Add "PLR2004". Remove "COM812" (currently ignored, needs to be enforced).

**per-file-ignores:** Extend `tests/**/*.py` to include "T201", "PLC0415", "PLR0915", "PLR0912".

Current: `"tests/**/*.py" = ["S101", "ANN", "TCH"]`
Target: `"tests/**/*.py" = ["S101", "ANN", "TCH", "T201", "PLC0415", "PLR0915", "PLR0912"]`

### Complexity Refactoring Targets

Two production functions need significant refactoring:

1. **`src/fathom/charts.py:prepare_line_chart`** (line 147)
   - 54 statements (limit: 50), 15 branches (limit: 12)
   - Strategy: Extract dataset preparation into helper functions

2. **`src/fathom/forms.py:validate_by_type`** (line 141)
   - 62 statements (limit: 50), 26 branches (limit: 12)
   - Strategy: Extract per-type validation into separate methods

3. **`src/fathom/formatting.py:comma_format`** (line 13)
   - 8 return statements (limit: 6)
   - Strategy: Consolidate early-exit paths or use match/case

### PLC0415 in Production Code

Three violations in `__init__.py` and `app.py` are deferred/lazy imports inside `create_app()`. These are a Flask pattern (avoiding circular imports). Options:
- Add per-file-ignore for these specific files
- Restructure imports (risky for circular import reasons)
- Recommendation: Per-file-ignore for `__init__.py` and `app.py` since these are intentional Flask patterns

### PT015 Fixes

Three instances of `assert False, "message"` in test_forms.py should become `pytest.fail("message")`.

### DTZ011 Fix

`date.today()` in routes.py line 494 should become `datetime.now(tz=timezone.utc).date()`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Trailing comma insertion | Manual editing | `ruff check --fix --select COM812` | 71 violations, all auto-fixable |
| Min/max simplification | Manual rewriting | `ruff check --fix --select PLR1730` | 6 violations, all auto-fixable |

## Common Pitfalls

### Pitfall 1: Breaking Existing Tests with Refactoring
**What goes wrong:** Extracting helper functions from validate_by_type or prepare_line_chart changes behavior subtly.
**How to avoid:** Run `uv run pytest` after each refactoring step. The 241 existing tests cover these functions well.
**Warning signs:** Test failures in test_forms.py or test_charts.py.

### Pitfall 2: Circular Imports from PLC0415 Fixes
**What goes wrong:** Moving lazy imports to top-level in Flask app factory functions creates circular import errors.
**How to avoid:** Use per-file-ignores for __init__.py and app.py rather than restructuring imports.

### Pitfall 3: Formatting Drift After Auto-Fix
**What goes wrong:** `ruff --fix` adds trailing commas, which may cause formatter to reflow lines.
**How to avoid:** Run `uv run ruff format .` after `ruff check --fix` to ensure formatting stays clean.

### Pitfall 4: ty/pyrefly Failures After Refactoring
**What goes wrong:** Extracting functions may introduce type annotation issues that ty or pyrefly catch.
**How to avoid:** Run `uv run ty check` and `uv run pyrefly check` after refactoring, before committing.

### Pitfall 5: Noqa/Type-Ignore Suppressions
**What goes wrong:** Project policy forbids `# noqa` and `# type: ignore` -- tempting to use during cleanup.
**How to avoid:** Use only per-file-ignores in pyproject.toml or fix violations properly.

## Code Examples

### Auto-Fix Command Sequence
```bash
# Step 1: Apply all safe auto-fixes
uv run ruff check --fix .

# Step 2: Re-format after fixes
uv run ruff format .

# Step 3: Verify no regressions
uv run pytest
uv run ty check
uv run pyrefly check
```

### PT015 Fix Pattern
```python
# Before (violation)
try:
    parse_form_data(form)
    assert False, "Should have raised ValidationError"  # noqa: B011
except ValidationError:
    pass

# After (correct)
import pytest

try:
    parse_form_data(form)
    pytest.fail("Should have raised ValidationError")
except ValidationError:
    pass
```

### DTZ011 Fix Pattern
```python
# Before (violation)
filename = f"fathom-{date.today().isoformat()}.json"

# After (correct)
from datetime import datetime, timezone
filename = f"fathom-{datetime.now(tz=timezone.utc).date().isoformat()}.json"
```

### PLW2901 Fix Pattern
```python
# Before (violation)
for line in msg.split("\n"):
    line = line.strip()

# After (correct)
for raw_line in msg.split("\n"):
    line = raw_line.strip()
```

### PLR1714 Fix Pattern
```python
# Before (violation)
winner_bg != "rgba(0, 0, 0, 0)" and winner_bg != "transparent"

# After (correct)
winner_bg not in {"rgba(0, 0, 0, 0)", "transparent"}
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=9.0.2 |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| N/A-01 | Ruff passes clean with expanded rules | lint | `uv run ruff check .` | N/A (tool check) |
| N/A-02 | ty passes clean after refactoring | typecheck | `uv run ty check` | N/A (tool check) |
| N/A-03 | pyrefly passes clean after refactoring | typecheck | `uv run pyrefly check` | N/A (tool check) |
| N/A-04 | All existing tests still pass | regression | `uv run pytest` | Exists (241 tests) |
| N/A-05 | No noqa/type-ignore suppressions added | policy | `grep -r "# noqa\|# type: ignore" src/ tests/` | N/A (grep check) |

### Sampling Rate
- **Per task commit:** `uv run ruff check . && uv run pytest -x`
- **Per wave merge:** `uv run ruff check . && uv run ruff format --check . && uv run ty check && uv run pyrefly check && uv run pytest`
- **Phase gate:** Full suite green before verification

### Wave 0 Gaps
None -- existing test infrastructure covers all phase requirements. No new test files needed; this phase modifies configuration and refactors existing code.

## Open Questions

1. **PLC0415 for Flask app factory imports**
   - What we know: 3 violations in __init__.py and app.py use deferred imports to avoid circular dependencies (standard Flask pattern)
   - Recommendation: Add per-file-ignores for these files rather than restructuring

2. **PLR0913 in test helper (Claude's Discretion)**
   - What we know: `_make_option_result` in test_results_helpers.py has 7 params (limit 5)
   - Recommendation: Add PLR0913 to tests per-file-ignores since test helper functions commonly need many parameters for factory patterns

3. **playwright_verify.py complexity rules**
   - What we know: 4 PLR0915 + 1 PLR0912 violations in playwright_verify.py (long verification functions)
   - Recommendation: Add to per-file-ignores since this is a verification script, not production code

## Sources

### Primary (HIGH confidence)
- Direct `ruff check` output against codebase -- all violation counts verified
- pyproject.toml -- current configuration read directly
- CONTEXT.md -- user decisions locked

### Secondary (MEDIUM confidence)
- Ruff rule documentation for PLC0415, PLR0915, PLR0912 behavior and thresholds

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new dependencies, all tools already in use
- Architecture: HIGH - all violations enumerated via direct ruff check
- Pitfalls: HIGH - based on concrete codebase analysis, not hypothetical

**Research date:** 2026-03-14
**Valid until:** 2026-04-14 (stable -- ruff config changes, no external dependencies)
