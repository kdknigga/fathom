---
phase: 05-refactor-form-validation-to-use-pydantic
plan: 01
subsystem: models
tags: [pydantic, basemodel, dataclass, domain-models, frozen]

# Dependency graph
requires:
  - phase: 01-core-engine
    provides: "Original dataclass-based domain models"
provides:
  - "Pydantic BaseModel domain models with frozen output types"
  - "pydantic as direct dependency"
affects: [05-02-pydantic-form-validation]

# Tech tracking
tech-stack:
  added: [pydantic]
  patterns: [BaseModel-with-ConfigDict-frozen, Field-default-factory]

key-files:
  created: []
  modified: [src/fathom/models.py, pyproject.toml, uv.lock]

key-decisions:
  - "No consumer files needed changes -- Pydantic BaseModel has identical keyword-construction and dot-access API to dataclasses"
  - "Output models frozen via ConfigDict(frozen=True); input models remain mutable"

patterns-established:
  - "Domain models use Pydantic BaseModel, not dataclasses"
  - "Output/immutable models use model_config = ConfigDict(frozen=True)"
  - "Input models omit frozen config to allow mutation"

requirements-completed: [REFACTOR-01, REFACTOR-05, REFACTOR-06]

# Metrics
duration: 2min
completed: 2026-03-11
---

# Phase 5 Plan 1: Pydantic Model Conversion Summary

**Converted all 7 dataclasses to Pydantic BaseModel with frozen output models and mutable input models, zero test changes required**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-11T01:45:46Z
- **Completed:** 2026-03-11T01:47:08Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Converted all 7 dataclasses (FinancingOption, GlobalSettings, MonthlyDataPoint, OptionResult, PromoResult, Caveat, ComparisonResult) to Pydantic BaseModel
- Added frozen=True to 5 output models; kept 2 input models mutable
- All 154 tests pass without any consumer file changes
- All quality gates pass (ruff, ty, pyrefly)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add pydantic dependency and convert models.py** - `9e043fb` (feat)
2. **Task 2: Update all model consumers and verify full test suite** - No code changes needed; all 154 tests passed as-is

## Files Created/Modified
- `src/fathom/models.py` - Converted 7 dataclasses to Pydantic BaseModel with ConfigDict frozen on output types
- `pyproject.toml` - Added pydantic>=2.12.5 as direct dependency
- `uv.lock` - Updated lockfile

## Decisions Made
- No consumer files needed changes: Pydantic BaseModel has the same keyword-construction and dot-access API as dataclasses, so all existing code (engine, amortization, opportunity, caveats, tests) worked without modification
- Output models use ConfigDict(frozen=True) for immutability; input models remain mutable for form processing compatibility

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None - all tests passed on first run after conversion.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Pydantic BaseModel foundation is in place for Plan 02 to build form validation models
- All existing tests green, all quality gates pass
- Input models remain mutable as needed for form processing in Plan 02

---
*Phase: 05-refactor-form-validation-to-use-pydantic*
*Completed: 2026-03-11*
