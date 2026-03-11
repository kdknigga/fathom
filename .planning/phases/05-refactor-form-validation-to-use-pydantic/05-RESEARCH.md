# Phase 5: Refactor Form Validation to Use Pydantic - Research

**Researched:** 2026-03-10
**Domain:** Pydantic v2 BaseModel migration, form validation, dataclass-to-Pydantic conversion
**Confidence:** HIGH

## Summary

This phase replaces hand-written validation in `forms.py` (414 lines) with Pydantic models, and converts all 7 dataclasses in `models.py` to Pydantic BaseModel. The project already uses Pydantic 2.12.5 transitively via pydantic-settings (see `config.py`), so the library is proven in-project and both `ty` and `pyrefly` already pass clean with Pydantic models.

The core challenge is preserving the exact error key format (`options.0.apr` dot-notation) that templates depend on, while gaining Pydantic's automatic type coercion and validation. Pydantic's `ValidationError.errors()` returns `loc` as tuples like `('options', 0, 'apr')` which need conversion. Cross-field validation errors from `@model_validator` get root-level `loc` by default, requiring careful error location mapping.

**Primary recommendation:** Convert models.py first (mechanical swap, low risk), then replace forms.py parse/validate pipeline with Pydantic validation models. Keep the `pydantic_errors_to_dict` helper simple and test it thoroughly against the existing error key expectations.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Convert ALL dataclasses in models.py to Pydantic BaseModel: FinancingOption, GlobalSettings, OptionResult, PromoResult, MonthlyDataPoint, ComparisonResult, Caveat
- Enums (OptionType, CaveatType, Severity) stay as standard Python Enums -- Pydantic handles them natively
- OptionType stays as `class OptionType(Enum)`, not StrEnum
- Output models (OptionResult, PromoResult, MonthlyDataPoint, ComparisonResult, Caveat) use `model_config = ConfigDict(frozen=True)` for immutability
- Input models (FinancingOption, GlobalSettings) stay mutable
- Keep `Decimal | None` pattern for optional fields (no condecimal range constraints on domain models)
- Add `pydantic` as a direct dependency in pyproject.toml (not just transitive via pydantic-settings)
- All call sites (forms.py, tests, engine, routes) updated for Pydantic construction; tests use `model_construct()` to skip validation when intentionally passing bad data
- Plan must flag all impacted call sites (asdict, dict unpacking, attribute access patterns) before execution
- Per-section Pydantic models: FormInput (top-level), OptionInput (per option), SettingsInput (global settings)
- FormInput contains `options: list[OptionInput]` and `settings: SettingsInput`
- Models live in forms.py (not a separate file)
- Type-dependent validation via `@model_validator(mode='after')` on OptionInput (single model, not discriminated union)
- Cross-field validation (down_payment <= purchase_price, discounted_price < purchase_price) in FormInput model_validator
- Option count (2-4) enforced in FormInput model
- All errors collected in one pass (field_validators for basic checks, model_validator for type-dependent logic)
- `parse_form_data` returns FormInput directly (no intermediate dict), constructing from ImmutableMultiDict
- Helper function `pydantic_errors_to_dict(exc: ValidationError) -> dict[str, str]` converts Pydantic errors to current dot-notation format
- Templates stay unchanged -- zero template modifications for error display
- Custom error messages in all validators via `raise ValueError('APR must be between 0% and 40%')` -- maintain current user-facing message quality
- Cross-field validators set custom error locations to preserve field-level inline error display
- Strip "Value error, " prefix from Pydantic messages in the helper function
- Form input models store raw validated strings (apr: str, term_months: str)
- `build_domain_objects(form: FormInput) -> tuple[list[FinancingOption], GlobalSettings]` handles string-to-Decimal conversion with percentage division
- Route uses try/except pattern: parse_form_data raises ValidationError on invalid input, route catches and converts to error dict
- Keep existing _to_rate, _to_money, _to_int helper functions for use in build_domain_objects

### Claude's Discretion
- Exact Pydantic model_config settings beyond frozen (e.g., str_strip_whitespace, validate_default)
- Whether to use Annotated types or Field() for metadata on model fields
- Order of validators and internal helper organization
- Test refactoring strategy (which tests need model_construct vs normal construction)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic | 2.12.5 | BaseModel, validators, ValidationError | Already in lockfile via pydantic-settings; proven in project config.py |
| pydantic-settings | 2.13.1+ | Already used for config.py | Stays unchanged |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic-core | (transitive) | PydanticCustomError for precise error control | Only if ValueError messages need more structure |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Field() for metadata | Annotated[str, Field(...)] | Annotated is more modern but Field() is simpler for this use case where we mostly need defaults, not constraints |

**Installation:**
```bash
uv add pydantic
```
This pins pydantic as a direct dependency. The version is already locked at 2.12.5 in uv.lock.

## Architecture Patterns

### Recommended Approach for models.py

Direct mechanical conversion -- every `@dataclass` becomes `class Foo(BaseModel)`. Key mappings:

| Dataclass Pattern | Pydantic Pattern |
|-------------------|------------------|
| `@dataclass` | `class Foo(BaseModel):` |
| `field(default_factory=lambda: Decimal(0))` | `Field(default_factory=lambda: Decimal(0))` |
| `from dataclasses import dataclass, field` | `from pydantic import BaseModel, ConfigDict, Field` |
| No config | Output models: `model_config = ConfigDict(frozen=True)` |

### Recommended Approach for forms.py

Replace the three-function pipeline:

**Before:**
```
parse_form_data(ImmutableMultiDict) -> dict
validate_form_data(dict) -> dict[str, str]  # errors
build_domain_objects(dict) -> tuple[...]
```

**After:**
```
parse_form_data(ImmutableMultiDict) -> FormInput  # raises ValidationError
build_domain_objects(FormInput) -> tuple[...]
```

### Pattern 1: Validation Models in forms.py
```python
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

class OptionInput(BaseModel):
    """Single financing option from form input."""

    model_config = ConfigDict(str_strip_whitespace=True)

    type: str
    label: str = ""
    apr: str = ""
    term_months: str = ""
    down_payment: str = ""
    post_promo_apr: str = ""
    deferred_interest: bool = False
    cash_back_amount: str = ""
    discounted_price: str = ""
    custom_label: str = ""

    @model_validator(mode="after")
    def validate_by_type(self) -> Self:
        """Type-dependent field validation."""
        ...
```

### Pattern 2: Error Location Mapping
```python
def pydantic_errors_to_dict(exc: ValidationError) -> dict[str, str]:
    """Convert Pydantic ValidationError to dot-notation error dict."""
    errors: dict[str, str] = {}
    for err in exc.errors():
        loc_parts = err["loc"]
        # Convert tuple ('options', 0, 'apr') to 'options.0.apr'
        key = ".".join(str(part) for part in loc_parts)
        msg = err["msg"]
        # Strip Pydantic's "Value error, " prefix
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]
        errors[key] = msg
    return errors
```

### Pattern 3: Route Error Handling
```python
@bp.route("/compare", methods=["POST"])
def compare_options() -> str:
    try:
        form_input = parse_form_data(request.form)
    except ValidationError as exc:
        errors = pydantic_errors_to_dict(exc)
        # ... render with errors
    else:
        financing_options, global_settings = build_domain_objects(form_input)
        # ... compute and render results
```

### Pattern 4: Cross-Field Validation with Custom Location

The main challenge: model_validator errors get root loc `()`. For cross-field validations that need field-level error display (e.g., `down_payment > purchase_price`), raise errors that include the field path explicitly.

**Approach:** In the FormInput model_validator, accumulate errors and raise them so they map to the correct field keys. Since Pydantic model_validator only raises a single error, the helper function must handle the conversion carefully.

**Practical solution:** For cross-field validation in FormInput (like `down_payment <= purchase_price`), move the purchase_price into each OptionInput and validate within the OptionInput model_validator. This keeps errors at the correct `options.N.field` location naturally.

Alternatively, perform cross-field validation in the `parse_form_data` function after Pydantic validation, adding errors to the dict manually.

### Anti-Patterns to Avoid
- **Using condecimal or confloat on domain models:** Decision explicitly keeps domain models constraint-free; validation is only in form input models
- **Discriminated union for option types:** Decision explicitly chooses single OptionInput model with model_validator
- **Putting validation models in a separate file:** Decision keeps them in forms.py
- **Float for money:** Continue using Decimal everywhere, Pydantic handles Decimal natively

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Type coercion | Manual str-to-type conversion | Pydantic field types with validators | Pydantic handles edge cases (whitespace, etc.) |
| Error collection | Manual error dict building | Pydantic ValidationError.errors() | Pydantic collects all errors in single pass |
| Immutability | Manual `__setattr__` override | `ConfigDict(frozen=True)` | Battle-tested, raises clear errors |
| Default factories | `dataclasses.field(default_factory=...)` | `pydantic.Field(default_factory=...)` | Same pattern, Pydantic-native |

## Common Pitfalls

### Pitfall 1: "Value error, " Prefix in Messages
**What goes wrong:** Pydantic prepends "Value error, " to ValueError messages raised in validators.
**Why it happens:** Pydantic wraps ValueError messages with this prefix in the error output.
**How to avoid:** Strip the prefix in `pydantic_errors_to_dict` helper: `msg.removeprefix("Value error, ")`.
**Warning signs:** Error messages in templates showing "Value error, APR is required." instead of "APR is required."

### Pitfall 2: model_validator Error Location is Root
**What goes wrong:** Errors raised in `@model_validator(mode='after')` get `loc = ()` (empty tuple) instead of pointing to a specific field.
**Why it happens:** Pydantic doesn't know which field a model_validator error pertains to.
**How to avoid:** For OptionInput type-dependent validation, raise ValueError with a message that includes enough context, OR structure the model so field-level validators handle per-field checks and model_validator only handles truly cross-field logic. The `pydantic_errors_to_dict` helper can map root-level errors to specific fields based on message content or custom error types.
**Warning signs:** Errors not appearing inline next to the correct form field.

### Pitfall 3: model_construct() Doesn't Run Validators
**What goes wrong:** Tests using `model_construct()` skip ALL validation, including type coercion.
**Why it happens:** `model_construct()` bypasses the entire Pydantic validation pipeline.
**How to avoid:** Only use `model_construct()` in tests that intentionally need invalid data. For tests with valid data, use normal construction.
**Warning signs:** Test fixtures silently having wrong types (str instead of Decimal, etc.).

### Pitfall 4: Dataclass-to-BaseModel Breaking Changes
**What goes wrong:** `dataclasses.asdict()` no longer works; dict unpacking patterns may change.
**Why it happens:** BaseModel instances are not dataclasses; they use `model_dump()` instead.
**How to avoid:** Search for all `asdict` usage (grep confirms: NONE in current codebase). Attribute access (`.field_name`) works identically.
**Warning signs:** ImportError on `dataclasses.asdict`, AttributeError on model instances.

### Pitfall 5: frozen=True Breaks Existing Construction Patterns
**What goes wrong:** Code that creates a model then modifies attributes will fail.
**Why it happens:** `ConfigDict(frozen=True)` prevents attribute assignment after construction.
**How to avoid:** Only output models (OptionResult, PromoResult, etc.) are frozen. Input models (FinancingOption, GlobalSettings) stay mutable. Check engine.py -- it constructs models via keyword args (no post-construction mutation found).
**Warning signs:** `ValidationError: Instance is frozen` at runtime.

### Pitfall 6: ty/pyrefly Compatibility with Pydantic
**What goes wrong:** Type checkers may not understand Pydantic's metaclass magic (e.g., model_config, validators).
**Why it happens:** ty has an open issue (#2403) for dedicated Pydantic support; it is not yet fully integrated.
**How to avoid:** The project already passes ty and pyrefly clean with pydantic-settings BaseSettings in config.py. Test incrementally after each change. If ty complains about model_config or validators, the pattern from config.py (which already works) can guide the fix.
**Warning signs:** ty errors about ConfigDict, model_validator signatures, or Field() types.

### Pitfall 7: Pydantic Validates on Construction
**What goes wrong:** Engine code that constructs FinancingOption or GlobalSettings with values that don't match type hints will now fail at runtime.
**Why it happens:** Unlike dataclasses, Pydantic BaseModel validates on construction by default.
**How to avoid:** Domain models have no constraints (decision: no condecimal), so Pydantic will only enforce type matching. Since the engine always passes correct types (Decimal, int, bool, etc.), this should be safe. Watch for any code passing strings where Decimal is expected.
**Warning signs:** ValidationError during engine computation, not during form processing.

## Code Examples

### Domain Model Conversion (models.py)

```python
# Source: Pydantic docs + existing config.py pattern
from pydantic import BaseModel, ConfigDict, Field

class FinancingOption(BaseModel):
    """A single financing option to compare."""

    option_type: OptionType
    label: str
    purchase_price: Decimal
    apr: Decimal | None = None
    term_months: int | None = None
    down_payment: Decimal | None = None
    post_promo_apr: Decimal | None = None
    deferred_interest: bool = False
    retroactive_interest: bool = True
    cash_back_amount: Decimal | None = None
    discounted_price: Decimal | None = None


class MonthlyDataPoint(BaseModel):
    """Data for a single month in the schedule."""

    model_config = ConfigDict(frozen=True)

    month: int
    payment: Decimal
    interest_portion: Decimal
    principal_portion: Decimal
    remaining_balance: Decimal
    investment_balance: Decimal
    cumulative_cost: Decimal
```

### GlobalSettings with default_factory

```python
class GlobalSettings(BaseModel):
    """Global comparison settings."""

    return_rate: Decimal
    inflation_enabled: bool = False
    inflation_rate: Decimal = Field(default_factory=lambda: Decimal(0))
    tax_enabled: bool = False
    tax_rate: Decimal = Field(default_factory=lambda: Decimal(0))
```

### Validation Error Conversion

```python
from pydantic import ValidationError

def pydantic_errors_to_dict(exc: ValidationError) -> dict[str, str]:
    """Convert Pydantic ValidationError to template-compatible error dict.

    Converts loc tuples to dot-notation strings matching the existing
    error key format (e.g., ``options.0.apr``, ``settings.return_rate``).
    """
    errors: dict[str, str] = {}
    for err in exc.errors():
        loc_parts = err["loc"]
        key = ".".join(str(part) for part in loc_parts)
        msg = err["msg"]
        # Pydantic prefixes ValueError messages
        msg = msg.removeprefix("Value error, ")
        if key:  # Skip empty keys from root-level errors
            errors[key] = msg
    return errors
```

## Impacted Call Sites

### models.py Consumers (ALL need updating for BaseModel construction)

| File | Models Used | Pattern | Risk |
|------|-------------|---------|------|
| `engine.py` | All 7 models | Keyword construction, attribute access | LOW -- same syntax |
| `forms.py` | FinancingOption, GlobalSettings, OptionType | Keyword construction | LOW -- same syntax |
| `caveats.py` | Caveat, GlobalSettings, FinancingOption + enums | Keyword construction | LOW -- same syntax |
| `amortization.py` | MonthlyDataPoint | Keyword construction | LOW -- same syntax |
| `opportunity.py` | FinancingOption, GlobalSettings, OptionType | Attribute access | LOW -- same syntax |
| `results.py` | OptionResult, PromoResult, ComparisonResult + enums | Attribute access | LOW -- same syntax |
| `charts.py` | ComparisonResult, OptionResult, PromoResult | Attribute access | LOW -- same syntax |
| `routes.py` | OptionType | Enum access only | NONE |
| `conftest.py` | FinancingOption, GlobalSettings, OptionType | Keyword construction in fixtures | LOW |
| `test_engine.py` | All models | Keyword construction | LOW |
| `test_caveats.py` | Multiple models | Keyword construction | LOW |
| `test_charts.py` | Multiple models | Keyword construction | LOW |
| `test_results_helpers.py` | Multiple models | Keyword construction | LOW |
| `test_opportunity.py` | FinancingOption, GlobalSettings | Keyword construction | LOW |
| `test_amortization.py` | FinancingOption | Keyword construction | LOW |
| `test_forms.py` | OptionType | Enum access | NONE (but API changes) |
| `test_edge_cases.py` | None (uses forms functions) | Function calls | API changes |

### Key Observation: No asdict Usage
Grep confirms zero usage of `dataclasses.asdict()` anywhere in the codebase. All model access is via dot-notation attribute access, which works identically on BaseModel.

### forms.py Consumers (API changes)
| File | Current Call | New Call |
|------|-------------|----------|
| `routes.py:compare_options` | `parse_form_data(form)` then `validate_form_data(parsed)` | `try: parse_form_data(form)` with `except ValidationError` |
| `routes.py:add_option` | `parse_form_data(request.form)` returns dict | Returns FormInput -- route needs dict conversion for template |
| `routes.py:remove_option` | `parse_form_data(request.form)` returns dict | Same -- needs dict for template context |
| `test_forms.py` | Tests `parse_form_data` returns dict, tests `validate_form_data` | API completely changes |
| `test_edge_cases.py` | Tests `validate_form_data` | API completely changes |

### Critical Route Consideration
`add_option` and `remove_option` call `parse_form_data` but do NOT validate (they just restructure form data for re-rendering). These routes need `parse_form_data` to NOT raise on invalid data, since the form may be partially filled. Options:
1. Add a `validate=False` parameter to `parse_form_data`
2. Create a separate `extract_form_data` function that returns raw dicts (no validation)
3. Have `parse_form_data` always validate, and wrap add/remove calls in try/except that ignores errors

**Recommendation:** Option 2 -- keep a simple extraction function for add/remove routes (they just need to restructure form keys), and have `parse_form_data` do full Pydantic validation for the compare route.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| dataclasses.dataclass | pydantic.BaseModel | Pydantic v2 (2023) | Full validation, serialization, frozen support |
| Manual validation loops | @field_validator + @model_validator | Pydantic v2 | Declarative, automatic error collection |
| dataclasses.asdict() | model.model_dump() | Pydantic v2 | Not needed in this codebase |
| allow_mutation=False | ConfigDict(frozen=True) | Pydantic v2 | Clean immutability |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2+ |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/test_forms.py tests/test_edge_cases.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REFACTOR-01 | models.py BaseModel conversion | unit | `uv run pytest tests/test_engine.py tests/test_amortization.py -x` | Yes |
| REFACTOR-02 | forms.py Pydantic validation | unit | `uv run pytest tests/test_forms.py -x` | Yes (needs rewrite) |
| REFACTOR-03 | Error key compatibility | unit | `uv run pytest tests/test_forms.py tests/test_edge_cases.py -x` | Yes (needs rewrite) |
| REFACTOR-04 | Route integration | integration | `uv run pytest tests/test_routes.py -x` | Yes |
| REFACTOR-05 | Frozen output models | unit | `uv run pytest tests/test_engine.py -x` | Yes |
| REFACTOR-06 | ty + pyrefly clean | lint | `uv run ty check && uv run pyrefly check` | N/A |

### Sampling Rate
- **Per task commit:** `uv run pytest -x && uv run ruff check . && uv run ty check && uv run pyrefly check`
- **Per wave merge:** `uv run pytest && uv run prek run`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
None -- existing test infrastructure covers all phase requirements. Test files for forms and edge cases exist and will be rewritten to match the new API.

## Open Questions

1. **Cross-field validation error locations**
   - What we know: model_validator errors get root-level loc. The `pydantic_errors_to_dict` helper needs to map these to field-specific keys.
   - What's unclear: Whether to encode field location in the error message and parse it out, or use PydanticCustomError with metadata.
   - Recommendation: Use a simple approach -- for cross-field validations that need specific field locations (like `down_payment > purchase_price`), perform them in OptionInput's model_validator where the error naturally gets `options.N.down_payment` location, passing purchase_price through a model field or context.

2. **add_option/remove_option routes**
   - What we know: These routes call parse_form_data but don't validate. They need raw form data restructuring.
   - What's unclear: Exact API design for non-validating parse.
   - Recommendation: Separate `extract_form_data` (returns raw dict for template re-rendering) from `parse_form_data` (returns FormInput, validates). This cleanly separates concerns.

3. **model_construct() in tests**
   - What we know: Some tests intentionally pass invalid data to test validation error paths.
   - What's unclear: Which specific tests need model_construct() vs normal construction.
   - Recommendation: Audit during implementation. Most test fixtures pass valid data (conftest.py fixtures all look valid). Only test_forms.py validation tests need adjustment -- and those test the form validation models, not domain models.

## Sources

### Primary (HIGH confidence)
- Pydantic 2.12.5 -- already locked in uv.lock, proven with config.py
- [Pydantic Validators docs](https://docs.pydantic.dev/latest/concepts/validators/) -- field_validator, model_validator patterns
- [Pydantic Models docs](https://docs.pydantic.dev/latest/concepts/models/) -- BaseModel, ConfigDict, model_construct
- [Pydantic Error Handling docs](https://docs.pydantic.dev/latest/errors/errors/) -- ValidationError.errors(), loc format
- Existing codebase (`config.py`, `models.py`, `forms.py`, `routes.py`) -- read directly

### Secondary (MEDIUM confidence)
- [Pydantic Configuration docs](https://docs.pydantic.dev/latest/api/config/) -- ConfigDict options
- [Pydantic custom error locations issue #8092](https://github.com/pydantic/pydantic/issues/8092) -- confirmed model_validator loc limitations
- [ty Pydantic support issue #2403](https://github.com/astral-sh/ty/issues/2403) -- ty doesn't have full Pydantic support yet, but existing config.py works

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- Pydantic 2.12.5 already in lockfile and working in config.py
- Architecture: HIGH -- patterns well-documented, decisions locked in CONTEXT.md
- Pitfalls: HIGH -- verified through docs and existing codebase analysis
- Error location mapping: MEDIUM -- model_validator loc behavior confirmed but cross-field solution needs implementation validation

**Research date:** 2026-03-10
**Valid until:** 2026-04-10 (Pydantic 2.x is stable, unlikely to change)
