# Phase 16: Custom Option Cleanup - Research

**Researched:** 2026-03-15
**Domain:** Jinja2 template rendering, Python form processing, label disambiguation
**Confidence:** HIGH

## Summary

This phase wires the existing `custom_label` form field into the results display pipeline and clarifies that the upfront cash field is optional. The codebase already parses `custom_label` from form data (forms.py:342) and stores it on `OptionInput`, but `build_domain_objects()` (forms.py:637) ignores it -- using `opt.label or option_type.value` instead. The fix is a targeted change in `build_domain_objects()` to prefer `custom_label` for CUSTOM option types, plus a disambiguation loop to ensure label uniqueness (required because engine.py:706-726 keys results by `option.label`).

The template pipeline already renders option names correctly everywhere via `opt["name"]` in display data (results.py:243). Once `build_domain_objects()` sets the right label, all downstream display (recommendation card, breakdown table, bar chart, line chart) works automatically with zero template changes.

**Primary recommendation:** Change label assignment in `build_domain_objects()`, add disambiguation loop, update custom.html field labels/tooltips, and add tests proving the label flows through rendered HTML.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Auto-disambiguate all label collisions with parenthetical numeric suffix: "My Plan", "My Plan (2)", "My Plan (3)"
- Applies universally -- custom-vs-custom AND custom-vs-default-label collisions (e.g., user types "Traditional Loan" as custom label)
- Disambiguation runs in `build_domain_objects()` (forms.py) -- labels are unique before reaching the engine
- Results dict keyed by `option.label` (engine.py:710-722) depends on uniqueness, so this must happen upstream
- Full replacement -- custom label becomes the option name everywhere: recommendation card, breakdown table, bar chart, line chart
- No "(Custom)" subtitle or type indicator in results
- Implementation: set `label = custom_label.strip()` in `build_domain_objects()` when type is CUSTOM and label is non-empty
- Rename form field label from "Description (optional)" to "Option Name (optional)"
- Update placeholder from "Notes about this option" to something like "e.g., Store Credit Card"
- No tooltip needed on the option name field
- Rename field label from "Upfront Cash Required" to "Down Payment (optional)" -- consistent with other option types
- Update tooltip text to reflect optional nature (e.g., "Optional upfront payment toward the purchase price. Leave blank if none.")
- When `custom_label` is empty or whitespace, fall back to "Custom" (title-cased, matches OptionType.CUSTOM enum value)
- Same auto-disambiguation rules apply to fallback labels -- two empty custom options become "Custom", "Custom (2)"
- Add HTML `maxlength` attribute (~40 chars) on the custom label input to prevent chart layout breakage

### Claude's Discretion
- Exact maxlength value for custom label input
- Tooltip popover ID naming convention
- Placeholder text wording (given the "e.g., Store Credit Card" direction)
- Test structure and assertion patterns
- How to handle edge cases (whitespace-only labels, special characters)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CUST-01 | Custom option's `custom_label` field is displayed in results as the option name | Label assignment change in `build_domain_objects()` + disambiguation loop; display pipeline already uses `option.label` everywhere |
| CUST-02 | Custom option's upfront cash field is clearly marked as optional in both UI and validation | Rename label in custom.html from "Upfront Cash Required" to "Down Payment (optional)", update tooltip; validation already treats it as optional (forms.py:222-232) |
| TEST-05 | Tests verify custom_label appears in rendered results | POST to `/compare` with custom option form data, assert custom label text in response HTML |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Jinja2 | (bundled with Flask) | Template rendering | Already in use for all templates |
| Flask | (existing) | Route handling, test client | Already in use |
| Pydantic | (existing) | Form validation | Already in use for OptionInput/FormInput |
| pytest | (existing) | Test framework | Already in use |

No new libraries needed for this phase.

## Architecture Patterns

### Label Flow Pipeline (Existing)
```
Form data (custom_label field)
  -> parse_form_data() -> OptionInput.custom_label
  -> build_domain_objects() -> FinancingOption.label  [CHANGE HERE]
  -> compare() -> ComparisonResult.results[label]
  -> analyze_results() -> display_data.options_data[].name
  -> Templates: opt.name, display.winner_name, bar.label
```

The entire display pipeline is keyed by `option.label`. Setting it correctly in `build_domain_objects()` is sufficient -- no template changes needed for display.

### Pattern 1: Label Assignment with Custom Label Support
**What:** Replace current label logic with custom_label awareness
**When to use:** In `build_domain_objects()` for CUSTOM option types

Current code (forms.py:637):
```python
label = opt.label or option_type.value
```

New code:
```python
if option_type == OptionType.CUSTOM and opt.custom_label.strip():
    label = opt.custom_label.strip()
elif option_type == OptionType.CUSTOM:
    label = "Custom"  # Title-cased fallback
else:
    label = opt.label or option_type.value
```

### Pattern 2: Label Disambiguation
**What:** Ensure all labels are unique before passing to engine
**When to use:** After all labels are assigned in `build_domain_objects()`, before returning

```python
# After building all options, disambiguate labels
seen: dict[str, int] = {}
for option in options:
    base = option.label
    if base in seen:
        seen[base] += 1
        option.label = f"{base} ({seen[base]})"
    else:
        seen[base] = 1
```

Note: This needs to handle the case where a collision creates a new collision (e.g., user names one option "Custom (2)" and another has no label). A simpler approach: collect all labels first, then rename duplicates in a second pass.

### Pattern 3: Template Field Updates (custom.html)
**What:** Update field labels and attributes in the custom option template
**Where:** `src/fathom/templates/partials/option_fields/custom.html`

Changes needed:
- Line 44: `"Upfront Cash Required"` -> `"Down Payment (optional)"`
- Line 45: Update tooltip popovertarget ID
- Line 47-48: Update tooltip text to "Optional upfront payment toward the purchase price. Leave blank if none."
- Line 67: `"Description (optional)"` -> `"Option Name (optional)"`
- Line 69-73: Add `maxlength` attribute, update placeholder
- Line 73: `"Notes about this option"` -> `"e.g., Store Credit Card"`

### Anti-Patterns to Avoid
- **Modifying templates to display custom labels:** The display pipeline already works -- only `build_domain_objects()` needs the label change
- **Disambiguation in the engine:** Engine expects unique labels as input; disambiguation must happen upstream
- **Using `opt.label` for custom options:** `opt.label` is the hidden form field that stores the option card header (e.g., "Custom/Other") -- `opt.custom_label` is the user-provided name

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Label uniqueness | Complex hash-based dedup | Simple counter-based suffix loop | File system naming pattern is familiar, 10 lines of code |

## Common Pitfalls

### Pitfall 1: Confusing `opt.label` and `opt.custom_label`
**What goes wrong:** `opt.label` on OptionInput is the hidden field storing the option type display name (e.g., "Custom/Other"), not the user's custom name. Using it for custom options would show "Custom/Other" in results.
**Why it happens:** The field name `label` suggests it's the user-visible label.
**How to avoid:** Always use `opt.custom_label` for CUSTOM option types. The current code at line 637 uses `opt.label`, which is why custom options show as "custom" (the enum value) in results today.

### Pitfall 2: Non-unique labels crashing the engine
**What goes wrong:** If two options have the same label, `results[option.label]` overwrites the first result with the second. The comparison loses an option silently.
**Why it happens:** Engine uses label as dict key (engine.py:706-726).
**How to avoid:** Disambiguation loop in `build_domain_objects()` BEFORE returning options to the engine. Must handle: two empty custom labels, custom label matching a default label, custom label matching another custom label.

### Pitfall 3: FinancingOption.label is a frozen/read-only field
**What goes wrong:** If `FinancingOption` uses frozen=True or similar, post-construction label assignment in disambiguation won't work.
**How to avoid:** Check if FinancingOption allows mutation. If not, disambiguation must happen on the label strings before constructing FinancingOption objects. Build labels list first, disambiguate, then construct.

### Pitfall 4: Title-casing the fallback
**What goes wrong:** `OptionType.CUSTOM.value` is `"custom"` (lowercase). The CONTEXT.md requires `"Custom"` (title-cased).
**How to avoid:** Explicit fallback string `"Custom"` rather than using `option_type.value` for custom type.

## Code Examples

### Custom Label in build_domain_objects()
```python
# In build_domain_objects(), replace label assignment:
for opt in form.options:
    option_type = OptionType(opt.type)
    if option_type == OptionType.CUSTOM and opt.custom_label.strip():
        label = opt.custom_label.strip()
    elif option_type == OptionType.CUSTOM:
        label = "Custom"
    else:
        label = opt.label or option_type.value
    # ... rest of option construction
```

### Disambiguation Loop
```python
# After building all (label, option_kwargs) pairs but before constructing FinancingOption:
labels = [pair[0] for pair in option_pairs]
final_labels: list[str] = []
seen: dict[str, int] = {}
for label in labels:
    if label in seen:
        seen[label] += 1
        final_labels.append(f"{label} ({seen[label]})")
    else:
        seen[label] = 1
        final_labels.append(label)
```

### Test: Custom Label in Rendered Results (TEST-05 pattern)
```python
def test_custom_label_in_results(self, client):
    """Custom option label appears in rendered comparison results."""
    data = {
        "purchase_price": "25000",
        "options[0][type]": "cash",
        "options[0][label]": "Pay in Full",
        "options[1][type]": "custom",
        "options[1][label]": "",
        "options[1][custom_label]": "Store Credit Card",
        "options[1][apr]": "18.99",
        "options[1][term_months]": "24",
        "return_preset": "0.07",
        "return_rate_custom": "",
        "inflation_rate": "3",
        "tax_rate": "22",
    }
    response = client.post("/compare", data=data)
    html = response.data.decode()
    assert "Store Credit Card" in html
    assert response.status_code == 200
```

### Test: Disambiguation
```python
def test_duplicate_custom_labels_disambiguated(self):
    """Two custom options with same label get numeric suffixes."""
    form = FormInput(
        purchase_price="25000",
        options=[
            OptionInput(type="cash", label="Pay in Full"),
            OptionInput(type="custom", custom_label="My Plan", apr="5", term_months="12"),
            OptionInput(type="custom", custom_label="My Plan", apr="8", term_months="24"),
        ],
        settings=...,
    )
    options, _ = build_domain_objects(form)
    labels = [o.label for o in options]
    assert "My Plan" in labels
    assert "My Plan (2)" in labels
```

## State of the Art

No library or framework changes apply. This is purely application-level wiring of existing data through existing display pipeline.

## Open Questions

1. **Is FinancingOption mutable?**
   - What we know: It's a dataclass-like domain model in models.py
   - What's unclear: Whether label can be modified after construction
   - Recommendation: If frozen, build labels array first, disambiguate, then construct objects. If mutable, can disambiguate after construction. Either approach works -- just check before implementing.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | pyproject.toml |
| Quick run command | `uv run pytest tests/test_forms.py tests/test_routes.py -x -q` |
| Full suite command | `uv run pytest -x -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CUST-01 | Custom label flows into FinancingOption.label | unit | `uv run pytest tests/test_forms.py -x -k "custom_label"` | No - Wave 0 |
| CUST-01 | Custom label appears in rendered HTML results | integration | `uv run pytest tests/test_routes.py -x -k "custom_label"` | No - Wave 0 |
| CUST-01 | Duplicate labels disambiguated | unit | `uv run pytest tests/test_forms.py -x -k "disambigu"` | No - Wave 0 |
| CUST-01 | Empty custom_label falls back to "Custom" | unit | `uv run pytest tests/test_forms.py -x -k "fallback"` | No - Wave 0 |
| CUST-02 | Down payment field labeled as optional in template | integration | `uv run pytest tests/test_routes.py -x -k "down_payment_optional"` | No - Wave 0 |
| TEST-05 | custom_label text present in rendered comparison HTML | integration | `uv run pytest tests/test_routes.py -x -k "custom_label_in_results"` | No - Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_forms.py tests/test_routes.py -x -q`
- **Per wave merge:** `uv run pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_forms.py` -- new tests for custom_label -> label flow, disambiguation, fallback
- [ ] `tests/test_routes.py` -- new tests for custom label in rendered HTML (TEST-05)
- No framework install needed -- pytest already configured

## Sources

### Primary (HIGH confidence)
- Direct codebase inspection: forms.py, models.py, engine.py, results.py, custom.html, test_forms.py, test_routes.py
- CONTEXT.md decisions from user discussion

### Secondary (MEDIUM confidence)
- None needed -- this is application-level wiring with no external library questions

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new libraries, all existing code
- Architecture: HIGH - traced label flow through entire pipeline via codebase inspection
- Pitfalls: HIGH - identified from actual code patterns (dict keying, field naming)

**Research date:** 2026-03-15
**Valid until:** 2026-04-15 (stable -- internal application code)
