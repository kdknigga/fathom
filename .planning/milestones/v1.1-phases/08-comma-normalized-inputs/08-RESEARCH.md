# Phase 8: Comma-Normalized Inputs - Research

**Researched:** 2026-03-13
**Domain:** Form input formatting (client-side JS + server-side Python + Jinja templates)
**Confidence:** HIGH

## Summary

This phase adds comma formatting to monetary input fields across Fathom's form. The work spans three layers: (1) server-side comma stripping in `_try_decimal()` and `_to_money()` before Decimal conversion, (2) a Jinja custom filter for rendering comma-formatted values in templates, and (3) a small vanilla JS file for focus/blur/paste event handling on monetary fields.

The codebase is well-structured for this change. All monetary fields already use `type="text"` with `inputmode="decimal"` (accepting commas natively), while non-monetary fields use `type="number"`. The `_try_decimal()` function is the single chokepoint for Decimal parsing -- adding comma/dollar stripping there covers all server-side parsing paths. The `extract_form_data()` function is where comma formatting should be applied for re-rendered values.

**Primary recommendation:** Use a `data-monetary` attribute on input fields to identify which fields get JS formatting. Implement a single delegated event listener on the form element for HTMX compatibility. Server-side changes are minimal -- modify `_try_decimal()` and `_to_money()` to strip `$`, commas, and spaces before conversion, and add a Jinja filter for display formatting.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Comma formatting applies to **monetary fields only** -- purchase price, monthly payment, cash-back amount, price reduction, custom monthly payment, down payment
- Rate fields (APR, return rate, inflation rate, tax rate) and term fields (months) are excluded
- **On focus:** strip commas so user sees raw number (e.g., '25,000' -> '25000')
- **On blur:** add commas to the value (e.g., '25000' -> '25,000')
- No real-time formatting while typing
- Support decimal places as-entered -- '25000' shows '25,000', '25000.50' shows '25,000.50'
- **Server renders monetary values with commas** in the HTML value attribute
- **Initial page load defaults also show commas** via Jinja filter
- **HTMX-swapped fields arrive pre-formatted** -- switching option types renders new fields with comma-formatted defaults
- **Client-side paste:** strip `$`, commas, and spaces on paste event
- **Server-side:** also strip `$`, commas, and spaces before Decimal conversion (belt and suspenders)
- **US format only** -- commas are thousands separators, dots are decimal points

### Claude's Discretion
- JS implementation approach: data attribute vs class-based selector for identifying monetary inputs
- Event delegation vs per-element listeners for HTMX compatibility
- Jinja filter implementation for server-side comma formatting
- Exact list of which template fields are "monetary" (Claude identifies from codebase)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INPUT-01 | User can type or paste numbers with commas into any numeric field and the value is accepted | Server-side `_try_decimal()` strips commas before Decimal conversion; client-side paste handler strips `$`/commas/spaces |
| INPUT-02 | Numeric fields display comma-formatted values after the user leaves the field (blur formatting) | JS blur handler applies `toLocaleString()` formatting; server-side Jinja filter pre-formats on render |
| INPUT-03 | Server-side parsing strips commas before Decimal conversion -- no silent failures | `_try_decimal()` and `_to_money()` modified to strip `$,` and spaces; belt-and-suspenders with client-side |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Vanilla JS | N/A | Focus/blur/paste event handlers | No framework needed; ~30 lines of code |
| Flask/Jinja2 | 3.1.3 / bundled | Custom template filter for comma formatting | Already in stack |
| Python `re` | stdlib | Stripping `$`, commas, spaces from form values | Already imported in forms.py |

### Supporting
No additional libraries needed. Python's built-in string formatting (`f"{value:,}"`) and JS's `Number.toLocaleString("en-US")` handle US comma formatting natively.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Vanilla JS | Alpine.js / Stimulus | Overkill for 3 event handlers; adds dependency for no benefit |
| `toLocaleString()` | Custom regex formatting | `toLocaleString` is reliable for US format, handles edge cases |
| Python `f"{:,}"` | `locale.format_string()` | `locale` requires system locale config; `:,` format spec is simpler and always uses commas |

## Architecture Patterns

### Recommended Approach

**Layer 1: Server-side parsing (forms.py)**
Modify `_try_decimal()` to strip `$`, commas, and whitespace before Decimal conversion. This is the single point where all monetary string-to-Decimal conversions happen, so one change covers all fields.

```python
def _try_decimal(value: str) -> Decimal | None:
    if not value or not value.strip():
        return None
    cleaned = value.strip().replace("$", "").replace(",", "").replace(" ", "")
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None
```

Similarly update `_to_money()` and `_to_rate()` (rates won't have commas, but belt-and-suspenders is harmless).

**Layer 2: Server-side display (Jinja filter)**
Register a custom Jinja filter in `app.py` that formats Decimal/string values with commas:

```python
def comma_filter(value: str) -> str:
    if not value or not value.strip():
        return value
    cleaned = value.strip().replace("$", "").replace(",", "").replace(" ", "")
    try:
        dec = Decimal(cleaned)
    except InvalidOperation:
        return value
    if dec == dec.to_integral_value():
        return f"{int(dec):,}"
    return f"{dec:,}"
```

Usage in templates: `value="{{ opt.fields.down_payment|default('')|comma }}"` and `value="{{ purchase_price|comma }}"`.

**Layer 3: Client-side formatting (JS)**
A small JS file with event delegation on the form element:

```javascript
// Identify monetary fields by data-monetary attribute
document.getElementById('comparison-form').addEventListener('focusin', function(e) {
  if (e.target.dataset.monetary !== undefined) {
    e.target.value = e.target.value.replace(/,/g, '');
  }
});

document.getElementById('comparison-form').addEventListener('focusout', function(e) {
  if (e.target.dataset.monetary !== undefined) {
    var val = e.target.value.replace(/,/g, '');
    if (val && !isNaN(val)) {
      var num = parseFloat(val);
      // Preserve decimal places as-entered
      var parts = val.split('.');
      if (parts.length === 2) {
        e.target.value = num.toLocaleString('en-US', {
          minimumFractionDigits: parts[1].length,
          maximumFractionDigits: parts[1].length
        });
      } else {
        e.target.value = num.toLocaleString('en-US');
      }
    }
  }
});

document.getElementById('comparison-form').addEventListener('paste', function(e) {
  if (e.target.dataset.monetary !== undefined) {
    e.preventDefault();
    var text = (e.clipboardData || window.clipboardData).getData('text');
    e.target.value = text.replace(/[$,\s]/g, '');
  }
});
```

### Monetary Fields Inventory (from template analysis)

| Template | Field | Name Attribute | Monetary? |
|----------|-------|---------------|-----------|
| index.html | Purchase Price | `purchase_price` | YES |
| traditional.html | Down Payment | `options[N][down_payment]` | YES |
| promo_zero.html | Down Payment | `options[N][down_payment]` | YES |
| promo_cashback.html | Cash-Back Amount | `options[N][cash_back_amount]` | YES |
| promo_cashback.html | Down Payment | `options[N][down_payment]` | YES |
| promo_price.html | Discounted Price | `options[N][discounted_price]` | YES |
| promo_price.html | Down Payment | `options[N][down_payment]` | YES |
| custom.html | Down Payment | `options[N][down_payment]` | YES |
| traditional.html | APR | `options[N][apr]` | NO (rate) |
| promo_zero.html | Term Months | `options[N][term_months]` | NO (integer) |
| promo_zero.html | Post-Promo APR | `options[N][post_promo_apr]` | NO (rate) |

### HTMX Compatibility Pattern
**Use event delegation on the form element**, not per-element listeners. When HTMX swaps in new option field partials (type switching, add/remove), delegated listeners on the parent form automatically cover new elements without re-binding. This is the standard pattern for dynamic content with HTMX.

### Anti-Patterns to Avoid
- **Per-element `addEventListener`:** Breaks when HTMX swaps DOM content; requires re-binding via `htmx:afterSwap` events. Delegation is cleaner.
- **`MutationObserver` for re-binding:** Overcomplicated. Delegation solves the same problem with zero overhead.
- **`type="number"` for monetary fields:** Cannot display commas. All monetary fields already use `type="text"` with `inputmode="decimal"` -- do not change this.
- **Formatting in `_try_decimal` return value:** Parsing and display are separate concerns. `_try_decimal` strips and parses; the Jinja filter formats.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Comma formatting numbers | Custom digit-grouping regex | Python `f"{val:,}"` / JS `toLocaleString('en-US')` | Handles edge cases (negatives, decimals) correctly |
| Stripping non-numeric chars | Field-by-field cleaning | Single `_try_decimal()` modification | One change point, all fields covered |

**Key insight:** The existing `_try_decimal()` is already the single parse path. Modifying it once handles INPUT-01 and INPUT-03 for all current and future monetary fields.

## Common Pitfalls

### Pitfall 1: Commas in `Decimal()` constructor
**What goes wrong:** `Decimal("25,000")` raises `InvalidOperation`. If commas reach `Decimal()` without stripping, parsing silently returns `None` via `_try_decimal()`.
**Why it happens:** Client-side JS might not run (disabled JS, slow load), so commas arrive at the server.
**How to avoid:** Strip commas in `_try_decimal()` before `Decimal()` conversion. Belt-and-suspenders: client strips on paste, server strips on parse.
**Warning signs:** Form submissions with comma-containing values silently producing empty/default values.

### Pitfall 2: Double-formatting on re-render
**What goes wrong:** Value is already comma-formatted in `extract_form_data()`, then Jinja filter adds commas again (e.g., `"25,000"` -> `"25,000"` is fine, but `"1,000,000"` could get mangled if filter doesn't handle existing commas).
**Why it happens:** `extract_form_data()` returns raw form values which may already contain commas from the previous submission.
**How to avoid:** The Jinja filter should strip commas first, then re-format. The `_try_decimal` pattern (strip then parse) already handles this; the filter should follow the same approach.

### Pitfall 3: Cursor position jumps on focus
**What goes wrong:** If formatting happens on focus instead of stripping, the cursor jumps to end of field.
**Why it happens:** Changing `value` programmatically resets cursor position.
**How to avoid:** On focus, only strip commas (shorter string, cursor stays roughly in place). On blur, format with commas (user isn't editing, cursor position doesn't matter).

### Pitfall 4: `parseFloat` precision for display
**What goes wrong:** `parseFloat("25000.10")` becomes `25000.1`, losing trailing zero.
**Why it happens:** JS parseFloat drops trailing zeros.
**How to avoid:** Split on `.` and count decimal places from the original string, then use `toLocaleString` with explicit `minimumFractionDigits` / `maximumFractionDigits` matching the original.

### Pitfall 5: HTMX swap loses formatting
**What goes wrong:** After HTMX swaps in new option fields (type change, add), values appear unformatted.
**Why it happens:** Server renders the new HTML, but if the Jinja filter isn't applied to new field templates, values arrive raw.
**How to avoid:** Apply `|comma` filter to ALL monetary field `value` attributes in ALL option field templates. Event delegation handles JS-side automatically.

## Code Examples

### Server-side comma stripping (forms.py)
```python
# Source: Direct codebase analysis of _try_decimal at forms.py:44
def _try_decimal(value: str) -> Decimal | None:
    """Attempt to convert a string to Decimal, stripping $, commas, spaces."""
    if not value or not value.strip():
        return None
    cleaned = value.strip().replace("$", "").replace(",", "").replace(" ", "")
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None
```

### Jinja filter registration (app.py)
```python
# In create_app():
from fathom.formatting import comma_format
app.jinja_env.filters["comma"] = comma_format
```

### Template usage (all monetary fields)
```html
<!-- Before -->
value="{{ opt.fields.down_payment|default('') }}"

<!-- After -->
value="{{ opt.fields.down_payment|default('')|comma }}"
```

### JS event delegation (new static file)
```javascript
// src/fathom/static/formatting.js
(function() {
  var form = document.getElementById('comparison-form');
  if (!form) return;

  form.addEventListener('focusin', function(e) {
    if (!e.target.hasAttribute('data-monetary')) return;
    e.target.value = e.target.value.replace(/,/g, '');
  });

  form.addEventListener('focusout', function(e) {
    if (!e.target.hasAttribute('data-monetary')) return;
    var raw = e.target.value.replace(/,/g, '');
    if (!raw || isNaN(raw)) return;
    var parts = raw.split('.');
    var num = parseFloat(raw);
    if (parts.length === 2) {
      e.target.value = num.toLocaleString('en-US', {
        minimumFractionDigits: parts[1].length,
        maximumFractionDigits: parts[1].length
      });
    } else {
      e.target.value = num.toLocaleString('en-US');
    }
  });

  form.addEventListener('paste', function(e) {
    if (!e.target.hasAttribute('data-monetary')) return;
    e.preventDefault();
    var text = (e.clipboardData || window.clipboardData).getData('text');
    e.target.value = text.replace(/[$,\s]/g, '');
  });
})();
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `type="number"` for money | `type="text"` + `inputmode="decimal"` | ~2020 | Allows commas in display, mobile shows numeric keyboard |
| Per-element event binding | Event delegation | Always standard | Works with dynamic DOM (HTMX swaps) |
| `locale.format_string()` | `f"{val:,}"` format spec | Python 3.6+ | No locale dependency, always uses commas |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `uv run pytest tests/test_forms.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INPUT-01 | Comma-containing strings parsed to correct Decimal | unit | `uv run pytest tests/test_forms.py -x -k "comma"` | Needs new tests |
| INPUT-01 | Dollar-sign strings parsed correctly | unit | `uv run pytest tests/test_forms.py -x -k "dollar"` | Needs new tests |
| INPUT-01 | Paste `$100,000` into field, submit, correct result | e2e | `uv run python tests/playwright_verify.py` | Needs new tests |
| INPUT-02 | Blur formats value with commas | e2e | `uv run python tests/playwright_verify.py` | Needs new tests |
| INPUT-02 | Focus strips commas from value | e2e | `uv run python tests/playwright_verify.py` | Needs new tests |
| INPUT-02 | Server-rendered values show commas | unit | `uv run pytest tests/test_routes.py -x -k "comma"` | Needs new tests |
| INPUT-03 | `_try_decimal("25,000")` returns `Decimal(25000)` | unit | `uv run pytest tests/test_forms.py -x -k "try_decimal"` | Needs new tests |
| INPUT-03 | `_try_decimal("$100,000.50")` returns correct Decimal | unit | `uv run pytest tests/test_forms.py -x -k "try_decimal"` | Needs new tests |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_forms.py -x`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green + Playwright verification before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] New test cases in `tests/test_forms.py` for comma/dollar stripping in `_try_decimal` and `_to_money`
- [ ] New test cases in `tests/test_routes.py` for comma-formatted values in rendered HTML
- [ ] Playwright test scenarios for focus/blur/paste behavior

## Open Questions

1. **`extract_form_data()` comma formatting**
   - What we know: `extract_form_data()` returns raw form values for re-rendering. These values pass through to templates.
   - What's unclear: Should `extract_form_data()` apply comma formatting to monetary values before returning, or should templates handle it via the `|comma` filter?
   - Recommendation: Use the Jinja `|comma` filter in templates. Keep `extract_form_data()` returning raw values -- the filter handles formatting at the display layer, which is cleaner separation of concerns.

2. **`build_domain_objects()` Decimal conversion with commas**
   - What we know: `build_domain_objects()` calls `Decimal(form.purchase_price)` directly (line 456), not through `_try_decimal()`.
   - What's unclear: If `form.purchase_price` still contains commas after Pydantic validation, this will crash.
   - Recommendation: The Pydantic validator `validate_purchase_price` calls `_try_decimal()` (which will strip commas), but the raw string is returned. `build_domain_objects()` then calls `Decimal()` on that raw string. Either strip commas in the validator before returning, or modify `build_domain_objects()` to strip commas before `Decimal()` conversion. The cleanest fix: have the Pydantic validator return the cleaned string.

## Sources

### Primary (HIGH confidence)
- Direct codebase analysis of `forms.py`, `routes.py`, `app.py`, all option field templates
- Python stdlib documentation for `Decimal` and format spec `:,`
- MDN Web Docs for `Number.toLocaleString()` and `inputmode` attribute

### Secondary (MEDIUM confidence)
- HTMX event delegation patterns (standard DOM behavior, not HTMX-specific)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - vanilla JS + Python stdlib, no external dependencies needed
- Architecture: HIGH - clear three-layer approach (parse/display/interact), single modification points identified
- Pitfalls: HIGH - based on direct codebase analysis of actual parsing paths and template patterns

**Research date:** 2026-03-13
**Valid until:** 2026-04-13 (stable domain, no moving targets)
