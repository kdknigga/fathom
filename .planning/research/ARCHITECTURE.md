# Architecture Patterns

**Domain:** Financial calculator web application (SSR + HTMX)
**Researched:** 2026-03-10

## Recommended Architecture

Fathom follows a **server-rendered monolith** pattern: a single Flask process handles HTTP requests, renders HTML via Jinja2 templates, performs all financial calculations in Python, and generates SVG charts server-side with pygal. HTMX provides interactivity without a JavaScript build step or client-side state.

```
Browser (HTMX)
    |
    | HTTP POST (form data)
    v
Flask Router
    |
    +---> Input Validation (Pydantic / dataclasses)
    |         |
    |         v
    |     Calculation Engine (pure Python, no I/O)
    |         |
    |         v
    |     Chart Generator (pygal -> inline SVG)
    |         |
    |         v
    |     Template Renderer (Jinja2 -> HTML fragment)
    |
    | HTML fragment response
    v
Browser (HTMX swaps fragment into DOM)
```

There is no database, no background worker, no message queue, and no client-side calculation logic. The entire data flow is: form submission -> validation -> calculation -> rendering -> HTML response.

### Component Boundaries

| Component | Responsibility | Communicates With | Module Path |
|-----------|---------------|-------------------|-------------|
| **Web Layer** | HTTP routing, request parsing, response formatting, HTMX headers | Input Validation, Template Renderer | `src/fathom/web/` |
| **Input Validation** | Parse and validate form data into typed domain objects | Web Layer, Calculation Engine | `src/fathom/models/` |
| **Calculation Engine** | All financial math: amortization, opportunity cost, inflation, tax savings, True Total Cost | Input Validation (receives data), Chart Generator (provides results) | `src/fathom/calc/` |
| **Chart Generator** | Produce SVG charts from calculation results | Calculation Engine (receives data), Template Renderer (provides SVG strings) | `src/fathom/charts/` |
| **Template Renderer** | Jinja2 templates for full pages and HTMX partial fragments | Web Layer (called by routes), Chart Generator (embeds SVG) | `src/fathom/templates/` |
| **Static Assets** | CSS, minimal JS (HTMX library), favicon | Served by Flask static handler | `src/fathom/static/` |

### Data Flow

**Full page load (initial visit):**
1. Browser requests `GET /`
2. Flask renders `index.html` (full page with form, empty results area)
3. HTMX library loaded from static assets

**Calculation request (HTMX partial update):**
1. User fills form, clicks "Calculate" (or live update on input change)
2. HTMX sends `POST /calculate` with form data
3. Flask route parses form data into validated `FinancingOption` objects
4. Calculation engine computes True Total Cost for each option
5. Chart generator creates SVG bar chart and line chart from results
6. Jinja2 renders `results_fragment.html` containing:
   - Summary recommendation card
   - Cost breakdown table
   - Inline SVG charts (rendered as raw SVG strings via `| safe` filter)
7. Flask returns the HTML fragment
8. HTMX swaps fragment into `#results` container

**Multi-target updates (recommended approach):**
Use the **expanded target** pattern: wrap the entire results area (recommendation + table + charts) in a single `<div id="results">` and replace it all at once. This is simpler than out-of-band swaps and avoids the complexity of managing multiple swap targets for what is fundamentally one calculation response. The HTMX docs describe four approaches (expanded target, hx-swap-oob, HX-Trigger events, path dependencies extension) but the expanded target is the right choice here because the results area is a single logical unit that always updates together.

### Domain Model

```
GlobalSettings
  - comparison_period_months: int
  - investment_return_rate: float  (opportunity cost rate)
  - inflation_rate: float
  - tax_bracket: float

FinancingOption (2-4 instances)
  - option_type: enum (cash | loan | promo_0pct | promo_cashback | promo_price_reduction | custom)
  - purchase_price: Decimal
  - down_payment: Decimal
  - interest_rate: float
  - term_months: int
  - promo_details: PromoDetails | None  (cashback amount, price reduction, etc.)

CalculationResult (per option)
  - total_payments: Decimal
  - opportunity_cost: Decimal
  - tax_savings: Decimal
  - inflation_adjustment: Decimal
  - rebates: Decimal
  - true_total_cost: Decimal
  - monthly_timeline: list[MonthlySnapshot]  (for cumulative cost chart)

ComparisonResult
  - options: list[CalculationResult]
  - recommended_option: int  (index)
  - recommendation_text: str
  - caveats: list[str]
```

## Patterns to Follow

### Pattern 1: Dual Templates (Full Page + Fragment)
**What:** Every page that supports HTMX partial updates has two templates: a full page template and a fragment template. The full page template includes the fragment via Jinja2's `{% include %}`.
**When:** Any route that serves both initial page loads and HTMX updates.
**Why:** Avoids conditional logic in templates. The `HX-Request` header determines which template to render. Flask's template inheritance (base.html with `{% block %}` tags, child templates with `{% extends %}`) keeps the full-page structure DRY, while fragment templates stand alone without extending the base.
**Example:**
```python
@app.route("/calculate", methods=["POST"])
def calculate():
    data = parse_form(request.form)
    results = engine.calculate(data)
    charts = generate_charts(results)
    context = {"results": results, "charts": charts}

    if request.headers.get("HX-Request"):
        return render_template("partials/results.html", **context)
    # Full page fallback (progressive enhancement)
    return render_template("index.html", **context)
```

### Pattern 2: Pure Calculation Engine
**What:** The calculation engine is a pure Python module with no Flask imports, no I/O, no template awareness. It takes typed dataclass/Pydantic inputs and returns typed outputs.
**When:** Always. This is the core of the application.
**Why:** Testable in isolation without HTTP. Enforces the "all calculations server-side" constraint naturally. Makes it impossible to accidentally leak calculation logic to the client.
**Example:**
```python
# src/fathom/calc/engine.py
from fathom.models import GlobalSettings, FinancingOption, ComparisonResult

def compare_options(
    settings: GlobalSettings,
    options: list[FinancingOption],
) -> ComparisonResult:
    """Compare financing options and return the full analysis."""
    # Pure math, no I/O, no Flask context
    ...
```

### Pattern 3: Chart Generation as a Service Function
**What:** Chart generation is a standalone module that accepts calculation results and returns SVG strings. It does not know about Flask, templates, or HTTP.
**When:** Any time charts need rendering.
**Why:** Decoupled from web layer. Can be tested by asserting SVG output contains expected elements. pygal's `render()` method returns SVG as a string that can be embedded directly in HTML.
**Example:**
```python
# src/fathom/charts/builder.py
import pygal

def build_cost_bar_chart(results: ComparisonResult) -> str:
    """Return inline SVG string for the cost comparison bar chart."""
    chart = pygal.Bar(
        title="True Total Cost Comparison",
        disable_xml_declaration=True,  # For inline embedding
    )
    for option in results.options:
        chart.add(option.label, float(option.true_total_cost))
    return chart.render(is_unicode=True)
```

### Pattern 4: Progressive Enhancement
**What:** The application works without JavaScript. HTMX enhances but does not replace the form submit flow.
**When:** Always, as a design principle.
**Why:** WCAG 2.1 AA compliance, resilience, and simplicity. If HTMX fails to load, the form still posts and the full page response includes results.
**Example:** The form has a standard `action="/calculate" method="POST"` alongside HTMX attributes (`hx-post="/calculate" hx-target="#results" hx-swap="innerHTML"`). The server checks `HX-Request` header and responds with either a fragment or full page.

### Pattern 5: Decimal Arithmetic for Money
**What:** Use Python's `decimal.Decimal` for all monetary calculations. Never use `float` for money.
**When:** Any calculation involving currency amounts.
**Why:** Float arithmetic produces rounding errors (e.g., `0.1 + 0.2 != 0.3`). For a financial tool, precision errors would undermine trust. Rates (interest, inflation, return rates) can remain as `float` since they are percentages, not currency.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Client-Side Calculation Duplication
**What:** Performing any financial calculation in JavaScript (even "simple" ones like total payment).
**Why bad:** Creates two sources of truth. Divergence between JS and Python results destroys user trust. Violates the project's core constraint.
**Instead:** All math stays in `src/fathom/calc/`. The client only submits data and displays server-rendered HTML.

### Anti-Pattern 2: Monolithic Route Handler
**What:** Putting validation, calculation, chart generation, and template rendering in a single Flask route function.
**Why bad:** Untestable, hard to modify, violates single responsibility. A 200-line route function is a common Flask anti-pattern.
**Instead:** Route handlers should be thin orchestrators: parse input, call calculation engine, call chart generator, render template. Each step is a separate module.

### Anti-Pattern 3: Global Mutable State
**What:** Storing calculation results in Flask's `g`, session, or module-level variables to avoid passing data between functions.
**Why bad:** Violates statelessness constraint. Creates race conditions under concurrent requests. Makes testing order-dependent.
**Instead:** Pass all data explicitly through function arguments and return values. The entire request lifecycle is: input in, result out.

### Anti-Pattern 4: JSON API + Client Rendering
**What:** Building a JSON API and rendering results with JavaScript templates or DOM manipulation.
**Why bad:** Defeats the purpose of SSR + HTMX. Adds JavaScript complexity, creates accessibility challenges, and duplicates rendering logic.
**Instead:** Return HTML fragments. HTMX swaps them into the DOM. The server does all rendering.

### Anti-Pattern 5: Dynamic Chart Updates via JavaScript
**What:** Using Chart.js or similar to render charts client-side from JSON data.
**Why bad:** Requires shipping calculation results as JSON to the client, tempting duplication. Adds a JS dependency and build complexity. SVG charts are more accessible (text is DOM-selectable, alt text is native).
**Instead:** Use pygal to render SVG server-side. Embed the SVG string directly in the HTML fragment response.

## Recommended Project Structure

```
src/fathom/
    __init__.py           # main() entry point, Flask app factory
    web/
        __init__.py
        routes.py         # Flask route handlers (thin orchestrators)
        forms.py          # Form parsing and HTMX response helpers
    models/
        __init__.py
        options.py        # FinancingOption, GlobalSettings dataclasses
        results.py        # CalculationResult, ComparisonResult dataclasses
    calc/
        __init__.py
        engine.py         # compare_options() - main entry point
        amortization.py   # Loan amortization schedules
        opportunity.py    # Opportunity cost calculations
        inflation.py      # Inflation adjustments
        tax.py            # Tax savings calculations
    charts/
        __init__.py
        builder.py        # Chart generation functions (pygal -> SVG)
        styles.py         # Chart color schemes, accessibility styles
    templates/
        base.html         # Base layout (head, body, HTMX script tag)
        index.html        # Full page: form + results area
        partials/
            results.html  # HTMX fragment: recommendation + table + charts
            form_errors.html  # Validation error messages
    static/
        css/
            main.css      # Application styles
        js/
            htmx.min.js   # HTMX library (vendored, no CDN)
```

## Build Order (Component Dependencies)

Components should be built in this order due to data flow dependencies:

```
Phase 1: Models (no dependencies)
    GlobalSettings, FinancingOption, CalculationResult dataclasses
    |
Phase 2: Calculation Engine (depends on Models)
    Pure math functions, fully testable without web layer
    |
Phase 3: Web Layer + Templates (depends on Models)
    Flask app, routes, base templates, form handling
    Can use stub/mock calculation results initially
    |
Phase 4: Chart Generator (depends on Models + Calculation Engine)
    pygal SVG generation from CalculationResult objects
    |
Phase 5: Integration (depends on all above)
    Wire calculation engine + charts into routes
    HTMX partial updates
    Progressive enhancement
    |
Phase 6: Polish
    Responsive layout, accessibility audit, error handling
    Performance optimization (300ms target)
```

**Key dependency insight:** The calculation engine and the web layer can be developed in parallel after models are defined, because the web layer can use hardcoded/mock results while the engine is being built. The chart generator depends on having real calculation output structures but not on the web layer.

## Scalability Considerations

| Concern | At 1 user | At 100 users | At 1K concurrent |
|---------|-----------|--------------|-------------------|
| Compute | Trivial | Trivial | pygal SVG rendering may be bottleneck |
| Memory | Minimal | Minimal | Each request is independent, no accumulation |
| State | None | None | None (stateless by design) |
| Deployment | `uv run fathom` | Same + reverse proxy | Gunicorn workers behind nginx |

For this application's scope (self-hosted calculator), scalability beyond a few concurrent users is unlikely to matter. The stateless design means horizontal scaling is trivial if ever needed: just add Gunicorn workers.

**Performance note for 300ms target:** The primary performance concern is pygal SVG rendering time. For 2-4 options with monthly timelines up to ~120 months, pygal should render in under 50ms. The calculation engine with Decimal arithmetic should be sub-10ms. The 300ms budget is generous for this workload.

## Sources

- HTMX documentation: https://htmx.org/docs/ (partial page updates, hx-target, hx-swap, HX-Request header)
- HTMX examples - updating other content: https://htmx.org/examples/update-other-content/ (expanded target pattern, OOB swaps, HX-Trigger events)
- Flask documentation: https://flask.palletsprojects.com/en/stable/ (template inheritance, blueprints, request handling)
- Flask template inheritance: https://flask.palletsprojects.com/en/stable/patterns/templateinheritance/ (Jinja2 blocks, includes)
- pygal documentation: https://www.pygal.org/en/stable/ (SVG output, render() method, chart types)
