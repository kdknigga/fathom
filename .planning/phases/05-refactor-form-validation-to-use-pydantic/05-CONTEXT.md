# Phase 5: Refactor Form Validation to Use Pydantic - Context

**Gathered:** 2026-03-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the hand-written parse/validate/build pipeline in `forms.py` with Pydantic models for form validation and domain object construction. Convert all dataclasses in `models.py` to Pydantic BaseModel for consistency. No new features or UI changes — this is a pure internal refactor.

</domain>

<decisions>
## Implementation Decisions

### Domain model migration
- Convert ALL dataclasses in models.py to Pydantic BaseModel: FinancingOption, GlobalSettings, OptionResult, PromoResult, MonthlyDataPoint, ComparisonResult, Caveat
- Enums (OptionType, CaveatType, Severity) stay as standard Python Enums — Pydantic handles them natively
- OptionType stays as `class OptionType(Enum)`, not StrEnum
- Output models (OptionResult, PromoResult, MonthlyDataPoint, ComparisonResult, Caveat) use `model_config = ConfigDict(frozen=True)` for immutability
- Input models (FinancingOption, GlobalSettings) stay mutable
- Keep `Decimal | None` pattern for optional fields (no condecimal range constraints on domain models)
- Add `pydantic` as a direct dependency in pyproject.toml (not just transitive via pydantic-settings)
- All call sites (forms.py, tests, engine, routes) updated for Pydantic construction; tests use `model_construct()` to skip validation when intentionally passing bad data
- Plan must flag all impacted call sites (asdict, dict unpacking, attribute access patterns) before execution

### Validation model design
- Per-section Pydantic models: FormInput (top-level), OptionInput (per option), SettingsInput (global settings)
- FormInput contains `options: list[OptionInput]` and `settings: SettingsInput`
- Models live in forms.py (not a separate file)
- Type-dependent validation via `@model_validator(mode='after')` on OptionInput (single model, not discriminated union)
- Cross-field validation (down_payment <= purchase_price, discounted_price < purchase_price) in FormInput model_validator
- Option count (2-4) enforced in FormInput model
- All errors collected in one pass (field_validators for basic checks, model_validator for type-dependent logic)
- `parse_form_data` returns FormInput directly (no intermediate dict), constructing from ImmutableMultiDict

### Error key compatibility
- Helper function `pydantic_errors_to_dict(exc: ValidationError) -> dict[str, str]` converts Pydantic errors to current dot-notation format (e.g., `options.0.apr`)
- Templates stay unchanged — zero template modifications for error display
- Custom error messages in all validators via `raise ValueError('APR must be between 0% and 40%')` — maintain current user-facing message quality
- Cross-field validators set custom error locations to preserve field-level inline error display
- Strip "Value error, " prefix from Pydantic messages in the helper function

### Conversion boundary
- Form input models store raw validated strings (apr: str, term_months: str)
- `build_domain_objects(form: FormInput) -> tuple[list[FinancingOption], GlobalSettings]` handles string-to-Decimal conversion with percentage division
- Route uses try/except pattern: parse_form_data raises ValidationError on invalid input, route catches and converts to error dict
- Keep existing _to_rate, _to_money, _to_int helper functions for use in build_domain_objects

### Claude's Discretion
- Exact Pydantic model_config settings beyond frozen (e.g., str_strip_whitespace, validate_default)
- Whether to use Annotated types or Field() for metadata on model fields
- Order of validators and internal helper organization
- Test refactoring strategy (which tests need model_construct vs normal construction)

</decisions>

<specifics>
## Specific Ideas

- The refactor should be a clean swap: same external behavior, same error messages, same template rendering — only internal implementation changes
- pydantic-settings already established the pattern in config.py (Phase 4) — this extends Pydantic to the rest of the codebase
- The three-function pipeline (parse -> validate -> build) collapses to two steps: parse_form_data (returns FormInput or raises) + build_domain_objects (converts to domain types)

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `forms.py`: 414-line file with parse_form_data, validate_form_data, build_domain_objects + helpers — all being refactored
- `models.py`: 177-line file with 7 dataclasses + 3 Enums — all dataclasses converting to BaseModel
- `config.py`: Already uses pydantic-settings (FathomSettings BaseSettings model) — established Pydantic pattern
- `_to_rate`, `_to_money`, `_to_int` helpers: Retained for build_domain_objects conversion step

### Established Patterns
- Decimal arithmetic throughout (never float for money)
- Flask app factory in app.py with Jinja2 templates
- Error keys use dot notation (options.0.apr, settings.return_rate) mapped to inline template display
- pydantic-settings in config.py established the Pydantic pattern in the project

### Integration Points
- `routes.py`: Calls parse_form_data -> validate_form_data -> build_domain_objects — route API changes to try/except
- `engine.py`: Imports FinancingOption, GlobalSettings, OptionResult, etc. from models.py — all becoming BaseModel
- `amortization.py`, `opportunity.py`, `inflation.py`, `tax.py`, `caveats.py`: Import and construct domain models
- `results.py`, `charts.py`: Access OptionResult/ComparisonResult attributes — should work unchanged with BaseModel
- `tests/`: Construct domain models directly — some tests may need model_construct() for intentionally invalid data
- Jinja2 templates: Access model attributes (dot notation) — should work unchanged with BaseModel

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 05-refactor-form-validation-to-use-pydantic*
*Context gathered: 2026-03-10*
