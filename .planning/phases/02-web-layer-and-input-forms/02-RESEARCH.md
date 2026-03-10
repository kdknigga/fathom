# Phase 2: Web Layer and Input Forms - Research

**Researched:** 2026-03-10
**Domain:** Flask SSR + HTMX dynamic forms + Pico CSS styling
**Confidence:** HIGH

## Summary

Phase 2 introduces the web layer: a Flask application serving server-rendered HTML forms with HTMX for dynamic field swapping when the user changes option types. The existing calculation engine (Phase 1) provides well-defined dataclasses (`FinancingOption`, `GlobalSettings`, `OptionType` enum) that map directly to form fields. No web framework is installed yet -- Flask, HTMX, and a CSS framework must be added.

The recommended stack is Flask 3.1.x for routing/templating, HTMX 2.0.x (via CDN) for partial page updates (type-switching field swaps), and Pico CSS 2.x (via CDN) for semantic styling with minimal custom CSS. This stack aligns perfectly with the project's SSR-first, minimal-JS philosophy. WTForms is NOT recommended -- the dynamic option cards with variable field sets are awkward to model in WTForms' `FieldList`/`FormField` system, and manual form handling with Jinja2 templates is simpler for HTMX partial rendering.

**Primary recommendation:** Use Flask 3.1.x + HTMX 2.0.x (CDN) + Pico CSS 2.x (CDN) with manual form handling (no WTForms). Keep validation server-side in a dedicated module that converts POST data to domain models.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Form starts with 2 options pre-filled: Option 1 = "Pay in Full", Option 2 = "Traditional Loan"
- Each option has a custom editable name field, defaulting to the type name
- Users can rename options to anything (e.g., "Best Buy Card", "Credit Union Loan")
- "+" Add financing option" text button below the last option, disappears at 4 options
- New options default to "Traditional Loan" type
- Remove via small x icon in option header, no confirmation dialog
- Remove button hidden when only 2 options remain (minimum enforced)
- No reordering -- options stay in the order added
- Changing option type instantly swaps fields (HTMX server-side swap, no animation)
- Switching type clears all type-specific field values (clean slate)
- Type selector dropdown in option card header, next to editable name and remove button
- "Pay in Full" card body shows explanation text rather than empty
- Card-based sections: Purchase Price card, Financing Options card with sub-cards per option, Global Settings collapsible
- Global settings collapsed by default with "Using defaults" hint
- Clean and neutral aesthetic: white/light gray, subtle borders, system font stack
- Validation fires on submit only (server-side)
- Errors displayed inline under each field, red text
- Page scrolls to first error
- Range validation: APR 0-40%, term 1-360 months, down payment <= purchase price, return rate 0-30%
- Submit button label: "Compare Options"
- CSS approach: Claude's discretion

### Claude's Discretion
- CSS framework/approach (Tailwind, plain CSS, classless library)
- Exact spacing, typography, and border styles
- Form field widths and input formatting (currency prefix, percentage suffix)
- How the "Reset / Start Over" button looks and where it sits
- Mobile sticky "View Results" anchor implementation details

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FORM-01 | User can enter purchase price as primary input | Flask form field with Decimal conversion; Pico CSS styled input |
| FORM-02 | User can set investment return rate via presets or manual override | Radio/select presets + manual input; HTMX not needed (JS-free with radio buttons) |
| FORM-03 | User can toggle inflation adjustment and enter custom rate | Checkbox toggle + conditional input; in collapsible Global Settings section |
| FORM-04 | User can toggle tax implications and enter marginal tax rate | Same pattern as FORM-03 |
| FORM-05 | User can define 2-4 financing options to compare | Dynamic option cards with add/remove via HTMX POST endpoints |
| FORM-06 | User can select option type which reveals relevant fields | HTMX hx-get on select change swaps option card body partial |
| FORM-07 | User can reset form to defaults via "Reset / Start Over" button | Link or button that redirects to GET / (fresh form) |
| OPTY-01 | Configure "Pay in Full (Cash)" option | Card body shows explanation text only, no extra fields |
| OPTY-02 | Configure "Traditional Loan" option | Fields: APR, term, down payment |
| OPTY-03 | Configure "0% Promotional Financing" option | Fields: promo term, down payment, deferred interest toggle |
| OPTY-04 | Configure "Promo with Cash-Back Rebate" option | Fields: APR, term, cash-back amount, down payment |
| OPTY-05 | Configure "Promo with Price Reduction" option | Fields: discounted price, APR, term, down payment |
| OPTY-06 | Configure "Custom/Other" option | Fields: effective APR, term, upfront cash, optional label |
| A11Y-01 | All form inputs have visible labels (WCAG 2.1 AA) | Pico CSS styles visible `<label>` elements natively; use `for` attribute |
| LYOT-01 | Desktop two-column layout (inputs left, results right) | Pico CSS `.grid` with 2 children; collapses at <768px automatically |
| LYOT-02 | Mobile single-column with sticky "View Results" anchor | Pico grid auto-collapses; sticky anchor via `position: sticky` CSS |
| LYOT-03 | All labels use plain consumer-friendly language | Template content concern; no library needed |
| TECH-03 | Form inputs repopulated on response | Pass form data back to template context on POST; Jinja2 renders values |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Flask | 3.1.x (latest 3.1.3) | Web framework, routing, Jinja2 templating | De facto Python micro-framework; built-in Jinja2; perfect for SSR |
| HTMX | 2.0.8 (CDN) | Partial page updates without custom JS | Hypermedia-driven; server returns HTML fragments; no build step |
| Pico CSS | 2.1.1 (CDN) | Semantic HTML styling, forms, grid, cards | Classless/minimal-class; styles native HTML; 7.7KB gzipped; responsive grid collapses <768px |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Flask-WTF | NOT USED | -- | Avoid: WTForms FieldList/FormField is awkward for dynamic HTMX-swapped option cards |
| Markupsafe | (bundled with Flask) | HTML escaping | Automatic in Jinja2 templates |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pico CSS | Tailwind CSS | Tailwind needs build step or CDN bloat; Pico works with semantic HTML out of the box |
| Pico CSS | Plain CSS | More custom code; Pico gives professional forms/cards/grid for free |
| Manual forms | WTForms | WTForms fights HTMX partial rendering; dynamic field sets require FieldList/FormField complexity |

**Installation:**
```bash
uv add flask
# HTMX and Pico CSS are CDN-only, no Python package needed
```

**CDN links (in base template):**
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
<script src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.8/dist/htmx.min.js"></script>
```

## Architecture Patterns

### Recommended Project Structure
```
src/fathom/
├── __init__.py          # main() creates Flask app
├── app.py               # Flask app factory, route registration
├── routes.py            # Route handlers (GET /, POST /compare, HTMX endpoints)
├── forms.py             # Form parsing, validation, conversion to domain models
├── models.py            # (existing) Domain models
├── engine.py            # (existing) Calculation engine
├── templates/
│   ├── base.html        # Base template: CDN links, layout shell
│   ├── index.html       # Main form page (extends base)
│   └── partials/
│       ├── option_card.html       # Single option card (full card with header + body)
│       ├── option_fields/
│       │   ├── cash.html          # "Pay in Full" body content
│       │   ├── traditional.html   # Traditional Loan fields
│       │   ├── promo_zero.html    # 0% Promo fields
│       │   ├── promo_cashback.html # Cash-Back fields
│       │   ├── promo_price.html   # Price Reduction fields
│       │   └── custom.html        # Custom/Other fields
│       ├── option_list.html       # All option cards + add button
│       └── global_settings.html   # Collapsible settings section
└── static/
    └── style.css        # Minimal custom CSS overrides (sticky anchor, error styles)
```

### Pattern 1: HTMX Partial Rendering for Type Switching
**What:** When user changes option type dropdown, HTMX swaps just the card body with new fields.
**When to use:** Every time the type `<select>` changes.
**Example:**
```html
<!-- In option_card.html -->
<article id="option-{{ idx }}">
  <header>
    <div class="grid">
      <input type="text" name="options[{{ idx }}][label]" value="{{ opt.label }}">
      <select name="options[{{ idx }}][type]"
              hx-get="/partials/option-fields/{{ idx }}"
              hx-target="#option-{{ idx }}-fields"
              hx-swap="innerHTML"
              hx-include="this">
        {% for otype in option_types %}
        <option value="{{ otype.value }}" {% if otype == opt.type %}selected{% endif %}>
          {{ otype.label }}
        </option>
        {% endfor %}
      </select>
      {% if can_remove %}
      <button type="button" class="outline secondary"
              hx-delete="/partials/option/{{ idx }}"
              hx-target="#options-container"
              hx-swap="innerHTML"
              aria-label="Remove option">x</button>
      {% endif %}
    </div>
  </header>
  <div id="option-{{ idx }}-fields">
    {% include option_template %}
  </div>
</article>
```

### Pattern 2: Form Data Naming Convention for Dynamic Options
**What:** Use indexed bracket notation so multiple options parse cleanly from POST data.
**When to use:** All option form fields.
**Example:**
```python
# In forms.py - parsing POST data
def parse_options(form_data: dict) -> list[dict]:
    """Parse indexed option fields from form POST data."""
    options = []
    idx = 0
    while f"options[{idx}][type]" in form_data:
        options.append({
            "type": form_data[f"options[{idx}][type]"],
            "label": form_data[f"options[{idx}][label]"],
            "apr": form_data.get(f"options[{idx}][apr]"),
            "term_months": form_data.get(f"options[{idx}][term_months]"),
            # ... other fields
        })
        idx += 1
    return options
```

### Pattern 3: App Factory
**What:** Create Flask app via factory function for testability.
**When to use:** Always.
**Example:**
```python
# In app.py
from flask import Flask

def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev"  # overridden via env in production

    from fathom.routes import bp
    app.register_blueprint(bp)

    return app
```

### Pattern 4: Dual Response (Full Page vs HTMX Partial)
**What:** Check for HX-Request header to decide whether to return full page or partial.
**When to use:** Routes that serve both initial page load and HTMX requests.
**Example:**
```python
from flask import request, render_template

@bp.get("/partials/option-fields/<int:idx>")
def option_fields(idx: int) -> str:
    """Return the fields partial for the selected option type."""
    option_type = request.args.get("options[{idx}][type]", "traditional_loan")
    template = OPTION_TYPE_TEMPLATES[option_type]
    return render_template(f"partials/option_fields/{template}", idx=idx)
```

### Anti-Patterns to Avoid
- **WTForms for dynamic HTMX forms:** WTForms expects form class to be defined before request; dynamic option cards with varying field sets fight this model.
- **Client-side validation:** Project explicitly requires server-side only. Do not add JS validation.
- **Duplicating OptionType definitions:** The form's type dropdown must be driven from the `OptionType` enum, not hardcoded strings in templates.
- **Float conversion for money:** Always convert form inputs to `Decimal`, never `float`. Use `Decimal(form_value)` in the parsing layer.
- **Inline styles for layout:** Use Pico CSS grid and semantic elements. Custom CSS only for gaps Pico doesn't cover (sticky anchor, error styling).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Form styling (inputs, labels, buttons) | Custom CSS for every form element | Pico CSS semantic styling | Pico styles `<input>`, `<select>`, `<label>`, `<button>` natively |
| Responsive grid | CSS media queries from scratch | Pico CSS `.grid` class | Auto-collapses <768px; exactly matches LYOT-01/LYOT-02 requirements |
| Card components | Custom card CSS | Pico CSS `<article>` element | Styled with optional `<header>`/`<footer>` sections |
| Collapsible sections | JS accordion | HTML `<details>`/`<summary>` (Pico-styled) | Native browser support, no JS, Pico styles it |
| Partial page updates | Custom fetch/XMLHttpRequest JS | HTMX attributes | Declarative HTML attributes, no JS to write |
| HTML escaping | Manual escaping | Jinja2 autoescaping | On by default in Flask's Jinja2 environment |

**Key insight:** Pico CSS + HTMX + native HTML elements (`<details>`, `<article>`, `<fieldset>`) eliminate almost all custom CSS and JS. The only custom CSS needed is for error styling, the sticky "View Results" anchor, and minor layout tweaks.

## Common Pitfalls

### Pitfall 1: HTMX Swap Losing Form State
**What goes wrong:** When HTMX swaps an option card's fields, other form data outside the swap target can be lost if the swap target is too broad.
**Why it happens:** Using `hx-swap="outerHTML"` on the entire form or a too-large container replaces everything.
**How to avoid:** Target only the specific `<div id="option-{idx}-fields">` for field swaps. Never swap the entire form. Use `innerHTML` swap strategy on the fields container.
**Warning signs:** After changing option type, other option cards or purchase price field loses its value.

### Pitfall 2: Form Field Name Collisions
**What goes wrong:** Multiple options use the same field names (e.g., just `apr`) and only the last value is submitted.
**Why it happens:** HTML forms submit all fields with the same name; without indexing, values overwrite.
**How to avoid:** Use indexed names: `options[0][apr]`, `options[1][apr]`, etc. Parse with index-based extraction.
**Warning signs:** Only the last option's values appear in the submitted data.

### Pitfall 3: Decimal Conversion Errors
**What goes wrong:** User enters "5.5" for APR and it becomes a float, introducing precision errors downstream.
**Why it happens:** `float("5.5")` is the natural Python conversion, but the engine requires `Decimal`.
**How to avoid:** Always use `Decimal(str_value)` in the form parsing layer. Handle empty strings and None before conversion.
**Warning signs:** Calculation results have tiny rounding differences from expected values.

### Pitfall 4: Pico CSS Grid in Classless Mode
**What goes wrong:** Using Pico's classless version but needing `.grid` for two-column layout.
**Why it happens:** `.grid` requires the standard (class-light) version of Pico, not the classless version.
**How to avoid:** Use the standard Pico CSS (`pico.min.css`), not the classless version (`pico.classless.min.css`).
**Warning signs:** Two-column layout doesn't work; everything stacks.

### Pitfall 5: HTMX Request Detection
**What goes wrong:** HTMX endpoint returns a full page instead of a partial, causing nested page rendering.
**Why it happens:** Not checking for the `HX-Request` header, or the check is wrong.
**How to avoid:** For dedicated partial endpoints (under `/partials/`), always return just the partial template. For shared endpoints, check `request.headers.get("HX-Request")`.
**Warning signs:** Duplicated page chrome (headers, footers) appearing inside the form.

### Pitfall 6: CSRF for Stateless App
**What goes wrong:** Adding Flask-WTF CSRF protection requires sessions/secret keys, adding complexity to a stateless tool.
**Why it happens:** CSRF protection is a security best practice, but this app has no user accounts or persistent state.
**How to avoid:** This is a stateless calculator with no authentication. CSRF risk is minimal. If desired, use Flask's built-in session (cookie-based) with `CSRFProtect`. For Phase 2, keep it simple -- the form only writes to the response, never to any server state.
**Warning signs:** Unnecessary 403 errors on form submission.

## Code Examples

### Flask App Factory with Pico CSS + HTMX Base Template
```python
# src/fathom/app.py
from flask import Flask

def create_app() -> Flask:
    """Create and configure the Fathom Flask application."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "fathom-dev-key"

    from fathom.routes import bp
    app.register_blueprint(bp)

    return app
```

```html
<!-- src/fathom/templates/base.html -->
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}Fathom{% endblock %}</title>
  <link rel="stylesheet"
    href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
  <script src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.8/dist/htmx.min.js"></script>
</head>
<body>
  <main class="container">
    {% block content %}{% endblock %}
  </main>
</body>
</html>
```

### Two-Column Layout with Pico Grid
```html
<!-- Desktop: side-by-side. Mobile (<768px): stacked automatically -->
<div class="grid">
  <div>
    <!-- Left column: form inputs -->
    <form method="post" action="/compare">
      {% block form_content %}{% endblock %}
    </form>
  </div>
  <div>
    <!-- Right column: results placeholder (Phase 3) -->
    <article id="results">
      <p>Fill in your financing options and click "Compare Options" to see results.</p>
    </article>
  </div>
</div>
```

### Collapsible Global Settings with `<details>`
```html
<details>
  <summary>
    Global Settings
    <small>Using defaults</small>
  </summary>
  <div class="grid">
    <label>
      Investment Return Rate
      <fieldset>
        <label><input type="radio" name="return_preset" value="0.04"> Conservative (4%)</label>
        <label><input type="radio" name="return_preset" value="0.07" checked> Moderate (7%)</label>
        <label><input type="radio" name="return_preset" value="0.10"> Aggressive (10%)</label>
      </fieldset>
    </label>
  </div>
  <!-- Inflation and tax toggles -->
</details>
```

### Server-Side Validation with Inline Errors
```python
# src/fathom/forms.py
from decimal import Decimal, InvalidOperation

def validate_option(data: dict, purchase_price: Decimal) -> dict[str, str]:
    """Validate a single option's fields, returning field->error mapping."""
    errors: dict[str, str] = {}
    option_type = data.get("type", "")

    if option_type in ("traditional_loan", "promo_cash_back", "promo_price_reduction", "custom"):
        apr_str = data.get("apr", "").strip()
        if not apr_str:
            errors["apr"] = "APR is required."
        else:
            try:
                apr = Decimal(apr_str)
                if apr < 0 or apr > Decimal("40"):
                    errors["apr"] = "APR must be between 0% and 40%."
            except InvalidOperation:
                errors["apr"] = "Please enter a valid number."

    return errors
```

```html
<!-- In a field partial template -->
<label for="option-{{ idx }}-apr">
  Annual Interest Rate (APR)
  <input type="text" id="option-{{ idx }}-apr"
         name="options[{{ idx }}][apr]"
         value="{{ opt.apr or '' }}"
         inputmode="decimal"
         placeholder="e.g., 5.99"
         {% if errors.get('apr') %}aria-invalid="true"{% endif %}>
  {% if errors.get('apr') %}
  <small class="error">{{ errors.apr }}</small>
  {% endif %}
</label>
```

### Form Repopulation (TECH-03)
```python
@bp.post("/compare")
def compare():
    """Handle form submission: validate, compute, render results."""
    form_data = request.form
    purchase_price_str = form_data.get("purchase_price", "").strip()
    options_raw = parse_options(form_data)

    errors = validate_all(purchase_price_str, options_raw)
    if errors:
        # Re-render form with errors and original values
        return render_template(
            "index.html",
            purchase_price=purchase_price_str,
            options=options_raw,
            errors=errors,
        )

    # Convert to domain models and compute
    # ... (calls engine.compare())
    return render_template("index.html", purchase_price=purchase_price_str,
                           options=options_raw, results=result)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| WTForms for all Flask forms | Manual handling + HTMX partials for dynamic forms | 2023-2024 (HTMX adoption) | Simpler code for dynamic field sets |
| jQuery/AJAX for partial updates | HTMX declarative attributes | 2020+ (HTMX 1.0+) | Zero custom JS needed |
| Bootstrap/heavy CSS frameworks | Pico CSS / classless / minimal-class CSS | 2022+ (Pico 2.0) | No build step, semantic HTML, tiny footprint |
| Client-side form validation | Server-side validation with HTMX swap | Ongoing trend with HTMX | Single source of truth, no JS duplication |

**Deprecated/outdated:**
- Flask-Script: replaced by `flask` CLI and `click` (since Flask 2.0)
- `flask.ext.*` imports: replaced by direct package imports years ago
- HTMX 1.x: migrated to 2.0 with breaking changes (attribute naming, default behaviors)

## Open Questions

1. **CSRF protection scope**
   - What we know: App is stateless, no user accounts, no persistent server state. CSRF risk is minimal for a calculator.
   - What's unclear: Whether to add Flask-WTF CSRFProtect anyway for defense-in-depth.
   - Recommendation: Skip CSRF for Phase 2 (pure calculator). Can add in Phase 4 hardening if needed.

2. **Add/remove option via HTMX**
   - What we know: Add/remove needs to update the options container and re-index fields.
   - What's unclear: Whether to store option state in a server-side session or reconstruct from form data on each HTMX request.
   - Recommendation: Use `hx-include` to send current form state with add/remove requests. Server reconstructs option list, adds/removes, returns updated `option_list.html` partial. No server session needed.

3. **Mobile sticky "View Results" anchor**
   - What we know: Needs to appear on mobile when results are below the fold.
   - What's unclear: Exact implementation (CSS-only sticky vs JS intersection observer).
   - Recommendation: CSS `position: sticky; bottom: 0` on a small bar with anchor link `#results`. Show only below 768px via media query. Pure CSS, no JS.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.x (already installed as dev dependency) |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/ -x -q` |
| Full suite command | `uv run pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FORM-01 | Purchase price input renders and submits | integration | `uv run pytest tests/test_routes.py::test_purchase_price_field -x` | No -- Wave 0 |
| FORM-02 | Return rate presets and manual override | integration | `uv run pytest tests/test_routes.py::test_return_rate_presets -x` | No -- Wave 0 |
| FORM-03 | Inflation toggle and custom rate | integration | `uv run pytest tests/test_routes.py::test_inflation_toggle -x` | No -- Wave 0 |
| FORM-04 | Tax toggle and rate | integration | `uv run pytest tests/test_routes.py::test_tax_toggle -x` | No -- Wave 0 |
| FORM-05 | 2-4 options with add/remove | integration | `uv run pytest tests/test_routes.py::test_add_remove_options -x` | No -- Wave 0 |
| FORM-06 | Type change reveals correct fields | integration | `uv run pytest tests/test_routes.py::test_type_switch_fields -x` | No -- Wave 0 |
| FORM-07 | Reset returns defaults | integration | `uv run pytest tests/test_routes.py::test_reset_form -x` | No -- Wave 0 |
| OPTY-01 to OPTY-06 | Each option type renders correct fields | unit | `uv run pytest tests/test_forms.py::test_option_type_fields -x` | No -- Wave 0 |
| A11Y-01 | All inputs have visible labels | integration | `uv run pytest tests/test_routes.py::test_labels_present -x` | No -- Wave 0 |
| LYOT-01 | Two-column grid class present | integration | `uv run pytest tests/test_routes.py::test_grid_layout -x` | No -- Wave 0 |
| LYOT-03 | Consumer-friendly language | manual-only | N/A (content review) | N/A |
| TECH-03 | Form repopulation after submit | integration | `uv run pytest tests/test_routes.py::test_form_repopulation -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/ -x -q`
- **Per wave merge:** `uv run pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_routes.py` -- Flask test client integration tests for all form routes
- [ ] `tests/test_forms.py` -- Unit tests for form parsing and validation logic
- [ ] `tests/conftest.py` -- Add Flask app fixture (`create_app` + `client` fixture)

## Sources

### Primary (HIGH confidence)
- [Pico CSS official docs](https://picocss.com/docs) -- Grid, forms, cards, accordion
- [HTMX official docs](https://htmx.org/docs/) -- Attributes, swap strategies, triggering
- [Flask official docs](https://flask.palletsprojects.com/en/stable/) -- App factory, testing, template inheritance

### Secondary (MEDIUM confidence)
- [GeeksforGeeks: Dynamic Forms with HTMX + Flask](https://www.geeksforgeeks.org/python/dynamic-forms-handling-with-htmx-and-python-flask/) -- Pattern examples
- [DEV: HTMX with Flask and Jinja2](https://dev.to/hexshift/implementing-htmx-with-flask-and-jinja2-for-dynamic-content-rendering-2bck) -- Integration patterns
- [Miguel Grinberg: Dynamic Forms with Flask](https://blog.miguelgrinberg.com/post/dynamic-forms-with-flask) -- WTForms FieldList limitations
- [Flask PyPI](https://pypi.org/project/Flask/) -- Version 3.1.3 confirmed

### Tertiary (LOW confidence)
- None -- all findings verified with official documentation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- Flask 3.1.x, HTMX 2.0.8, Pico CSS 2.1.1 are all current stable releases verified via official sources
- Architecture: HIGH -- Flask + HTMX + Jinja2 partials is a well-documented pattern with multiple authoritative guides
- Pitfalls: HIGH -- Based on known HTMX/Flask integration patterns and the specific form requirements
- CSS choice (Pico): MEDIUM -- Pico is a strong fit for semantic HTML + minimal-class approach, but exact integration with all form patterns needs validation during implementation

**Research date:** 2026-03-10
**Valid until:** 2026-04-10 (stable libraries, slow-moving ecosystem)
