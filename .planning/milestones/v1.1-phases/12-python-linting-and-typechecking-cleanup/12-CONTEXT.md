# Phase 12: Python Linting and Typechecking Cleanup - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Tighten ruff linting rules, resolve all new violations, and refactor complex functions to comply with default thresholds. All three tools (ruff, ty, pyrefly) already pass clean — this phase expands rule coverage and fixes what surfaces.

</domain>

<decisions>
## Implementation Decisions

### Rule Expansion
- Enable rule categories: PL (pylint), PT (pytest), DTZ (datetime), T20 (print), COM812 (trailing commas)
- Exclude PLR2004 (magic-value-comparison) — too noisy (102 hits), low signal for this codebase
- Keep D212 (multi-line-summary-first-line) ignored — current convention is D213 (summary on second line), no reason to change
- Keep E501 (line-too-long) ignored — ruff formatter handles most cases, remaining are URLs/long strings
- Remove COM812 from ignore list — enable trailing comma enforcement (71 auto-fixable violations)

### Auto-Fix Strategy
- Apply `ruff --fix` for all safe auto-fixable violations (trailing commas, if-stmt-min-max, redundant-numeric-union, etc.)
- Manual fixes only for violations that require judgment (complexity refactoring, print replacement)

### Complexity Refactoring
- Refactor complex functions to comply with ruff's default thresholds (50 statements, 10 McCabe complexity, 12 branches)
- Fix PLR1714 (repeated-equality-comparison) — use set membership check
- Fix PLW2901 (redefined-loop-name) — rename loop variable
- Fix PLR0911 (too-many-return-statements) — refactor to reduce returns

### Print Statement Policy
- T20 enabled globally as a guardrail against print() in production code
- T201 added to per-file-ignores for tests/**/*.py — test verification scripts use print for output (PASS/FAIL, screenshots, section headers)
- No production code currently has print statements — rule prevents future additions

### Claude's Discretion
- PLR0913 (too-many-arguments): Claude reviews the 1 violation and decides whether to refactor (parameter object) or ignore based on whether it improves the code
- CLI entry point prints: Claude checks `__init__.py:main()` and decides between per-file ignore or converting to logging based on what's there
- Exact refactoring approach for complex functions — extract helpers, restructure conditionals, etc.

</decisions>

<specifics>
## Specific Ideas

No specific requirements — standard code quality cleanup. Follow ruff defaults and refactor for clarity.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- pyproject.toml `[tool.ruff.lint]` section: current select/ignore lists to modify
- pyproject.toml `[tool.ruff.lint.per-file-ignores]` section: test exclusions to extend
- All existing tests pass — refactoring must not break them

### Established Patterns
- Tests excluded from ANN, TCH, S101 rules — this pattern extends to T201
- ruff, ty, pyrefly all run as pre-commit hooks via `prek`
- Zero `# noqa` or `# type: ignore` suppressions in codebase — must stay that way

### Integration Points
- pyproject.toml is the single config file for all ruff settings
- Pre-commit hooks (`prek`) enforce all rules on every commit
- CI via GitHub Actions also runs these checks

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 12-python-linting-and-typechecking-cleanup*
*Context gathered: 2026-03-14*
