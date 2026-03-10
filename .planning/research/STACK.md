# Technology Stack

**Project:** Fathom -- Financing Options Analyzer
**Researched:** 2026-03-10
**Overall confidence:** MEDIUM-HIGH (versions verified via PyPI; some choices based on training data ecosystem knowledge)

## Recommended Stack

### Core Framework

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Flask | 3.1.3 | Web framework, SSR, routing | Best Python framework for SSR + HTMX. Lightweight, Jinja2-native, massive ecosystem. FastAPI is API-first (wrong paradigm for SSR HTML). Django is overkill for a single-page stateless app with no database. Flask hits the sweet spot: template rendering is first-class, HTMX partial responses are trivial (just render a template fragment), and the learning curve is minimal. | HIGH |
| Jinja2 | 3.1.6 | HTML templating | Ships with Flask. Industry standard for Python SSR. Supports template inheritance, macros, and partial rendering -- all needed for HTMX fragment responses. No reason to consider alternatives. | HIGH |
| Gunicorn | 25.1.0 | Production WSGI server | Standard production server for Flask. Single-process constraint is fine -- Gunicorn with 1-4 workers in a single container. Uvicorn is ASGI (wrong protocol for Flask WSGI). | HIGH |

### Frontend (CDN / Static)

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| HTMX | 2.0.8 | Partial page updates | Mandated by PRD. 16KB, zero dependencies. Enables live result updates by swapping HTML fragments from the server. No build step needed -- serve from CDN or vendor locally. | HIGH |

### Charting

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| pygal | 3.1.0 | SVG chart generation | Purpose-built for server-side SVG chart rendering in Python. Supports bar charts (True Total Cost comparison) and line charts (cumulative cost over time) -- the two chart types the PRD requires. Outputs clean SVG that can be embedded directly in HTML. Actively maintained (latest release Dec 2025). Alternatives: matplotlib can output SVG but produces raster-style graphics with poor web integration; Chart.js requires client-side JS (acceptable fallback per PRD but not preferred). pygal's SVG output is WCAG-friendly: text is real text (not rasterized), and the library supports custom styling/colors. | HIGH |

### Form Handling and Validation

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| WTForms | 3.2.1 | Form definition and validation | Server-side form validation for financing option inputs. Handles type coercion (strings to Decimal), range validation, conditional required fields. Integrates natively with Flask via Flask-WTF. Pydantic is an alternative but is model-validation focused, not HTML-form focused -- WTForms generates HTML labels and error messages directly, which matters for WCAG compliance. | HIGH |
| Flask-WTF | 1.2.2 | Flask + WTForms integration | CSRF protection (needed even for HTMX POST requests), form rendering helpers, file upload handling (not needed but comes free). | HIGH |

### Data Modeling and Calculation

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python `decimal` | stdlib | Financial calculations | Mandated by financial accuracy requirements. IEEE 754 floats produce rounding errors in currency math. `decimal.Decimal` with explicit precision avoids this. Zero dependencies -- it is in the standard library. | HIGH |
| Pydantic | 2.12.5 | Internal data models | Type-safe data containers for calculation inputs/outputs. Validates and coerces data between form layer and calculation engine. Excellent type checker support (important for ty and pyrefly). Use for internal models only -- WTForms handles the HTTP form layer. | MEDIUM |

### Testing

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| pytest | 9.0.2 | Test runner | Standard Python test runner. Flask has built-in test client that works with pytest. | HIGH |
| pytest-cov | 7.0.0 | Coverage reporting | Standard coverage plugin for pytest. | HIGH |

### CSS / Styling

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Simple CSS (classless or minimal) | N/A | Styling | For a single-page calculator, a heavyweight CSS framework is unnecessary. Use a classless CSS base like Simple.css or Pico CSS (served from CDN) for sensible defaults, then add custom CSS for the specific layout (two-column desktop, stacked mobile, sticky anchor). This keeps the frontend dependency-free with no build step. Tailwind requires a build step and Node.js -- unnecessary complexity for this scope. Bootstrap is 150KB+ of unused CSS. | MEDIUM |

### Infrastructure

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Docker | N/A | Containerization | PRD mandates self-hosting with Dockerfile. Single-stage build: `python:3.14-slim` base, `uv sync`, `gunicorn` entrypoint. | HIGH |
| uv | latest | Package management | Mandated by PRD. Replaces pip, poetry, conda. Handles venv creation, dependency resolution, and script running. | HIGH |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Web framework | Flask | FastAPI | FastAPI is API-first (JSON responses). SSR with FastAPI requires bolting on Jinja2 manually and fighting the framework's assumptions. Flask was designed for HTML rendering. |
| Web framework | Flask | Django | Massive framework with ORM, admin, auth -- none of which Fathom needs. Django's template engine is less flexible than Jinja2 (no expressions in templates). Deployment overhead for zero benefit. |
| Web framework | Flask | Starlette | Lower-level than Flask. Would need to manually wire templating, form handling, and error pages. Good for APIs, not SSR apps. |
| Charting | pygal | matplotlib | matplotlib outputs SVG but the SVGs are bloated raster-style renders. Poor text handling for web. Designed for scientific plots, not web dashboards. Heavy dependency (numpy). |
| Charting | pygal | Chart.js | Client-side JS. Acceptable fallback per PRD but violates the SVG-preferred directive. Requires client-side data serialization. Not WCAG-friendly without extra work. |
| Charting | pygal | Plotly | Enormous dependency. Client-side JS rendering. Overkill for two chart types. |
| Form validation | WTForms | Pydantic alone | Pydantic validates data models, not HTML forms. No CSRF, no HTML label generation, no field-level error rendering. Would need to build the form-to-HTML layer from scratch. |
| CSS | Classless/minimal | Tailwind CSS | Requires Node.js build step, a `tailwind.config.js`, and PostCSS. Adds an entire JS toolchain to a Python-only project. Not worth it for a single-page app. |
| CSS | Classless/minimal | Bootstrap | 150KB+ of unused CSS. jQuery dependency in older versions. Custom theming requires Sass. Overkill. |
| WSGI server | Gunicorn | Waitress | Waitress works but Gunicorn is more battle-tested on Linux, has better process management, and is the de facto standard. |
| Data models | Pydantic | dataclasses | dataclasses lack runtime validation. Financial inputs from user forms need coercion and constraint checking. Pydantic does this declaratively. |

## Version Pinning Strategy

Pin exact versions in `pyproject.toml` for reproducibility:

```toml
dependencies = [
    "flask>=3.1.3,<4",
    "gunicorn>=25.1.0,<26",
    "pygal>=3.1.0,<4",
    "wtforms>=3.2.1,<4",
    "flask-wtf>=1.2.2,<2",
    "pydantic>=2.12.5,<3",
]
```

Use compatible release specifiers (`>=X.Y.Z,<NEXT_MAJOR`) to allow patch updates while preventing breaking changes. `uv.lock` handles exact pinning.

## Installation

```bash
# Core dependencies
uv add flask gunicorn pygal wtforms flask-wtf pydantic

# Dev dependencies (already in pyproject.toml)
uv add --dev pytest pytest-cov
```

## HTMX Integration Notes

HTMX does not require a Python package. Serve `htmx.min.js` either:
1. From CDN: `<script src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.8/dist/htmx.min.js"></script>`
2. Vendored in `src/fathom/static/vendor/htmx.min.js` (preferred for self-hosting reliability)

Flask routes return HTML fragments for HTMX requests. Detect HTMX requests via the `HX-Request` header to return a partial template instead of a full page.

## Key Architecture Decisions Driven by Stack

1. **WSGI not ASGI** -- Flask is WSGI. No async needed (calculations are CPU-bound, not I/O-bound). Gunicorn is the server.
2. **No JavaScript build step** -- HTMX from CDN/vendor, CSS from CDN/vendor, no webpack/vite/esbuild.
3. **Two validation layers** -- WTForms validates HTTP form input (strings, CSRF). Pydantic validates internal calculation models (typed, constrained). This separation keeps the form layer and calculation engine independently testable.
4. **pygal SVGs embedded inline** -- `pygal.render()` returns an SVG string. Embed directly in Jinja2 templates with `| safe` filter. No separate image requests, no JS rendering.

## What NOT to Use

| Technology | Why Not |
|------------|---------|
| mypy / pyright | PRD mandates ty and pyrefly only |
| pip / poetry / conda | PRD mandates uv only |
| pre-commit | PRD mandates prek |
| SQLite / PostgreSQL / any DB | Stateless app, no persistence |
| Redis / Memcached | No caching layer needed for stateless calculator |
| Celery / task queues | Calculations complete in <300ms, no background jobs |
| React / Vue / Svelte | SSR with HTMX replaces SPA frameworks entirely |
| Node.js / npm | Pure Python stack, no JS toolchain |
| Docker Compose | Single process, no orchestration needed |

## Sources

- Flask 3.1.3: https://pypi.org/project/flask/ (verified 2026-03-10)
- Jinja2 3.1.6: https://pypi.org/project/jinja2/ (verified 2026-03-10)
- Gunicorn 25.1.0: https://pypi.org/project/gunicorn/ (verified 2026-03-10)
- HTMX 2.0.8: https://htmx.org (verified 2026-03-10)
- pygal 3.1.0: https://pypi.org/project/pygal/ (verified 2026-03-10)
- pygal chart types: https://www.pygal.org/en/stable/documentation/types/index.html
- WTForms 3.2.1: https://pypi.org/project/wtforms/ (verified 2026-03-10)
- Flask-WTF 1.2.2: https://pypi.org/project/flask-wtf/ (verified 2026-03-10)
- Pydantic 2.12.5: https://pypi.org/project/pydantic/ (verified 2026-03-10)
- pytest 9.0.2: https://pypi.org/project/pytest/ (verified 2026-03-10)
- pytest-cov 7.0.0: https://pypi.org/project/pytest-cov/ (verified 2026-03-10)
