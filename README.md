# Fathom

A financing options analyzer that compares the true total cost of different financing options, accounting for opportunity costs, inflation, and tax implications.

## Features

- Compare up to 4 financing options side-by-side
- 6 option types: Cash, Traditional Loan, 0% Promo, Cash-Back, Price Reduction, Custom
- True Total Cost calculation including opportunity cost, inflation, and tax savings
- Interactive SVG charts with accessible data tables
- Server-side rendering with HTMX for dynamic updates
- Fully self-contained (no CDN dependencies, no database)

## Quick Start

### Docker (recommended)

```bash
docker build -t fathom .
docker run -p 5000:5000 fathom
```

Then visit <http://localhost:5000>.

### Bare metal (uv)

```bash
uv sync
uv run fathom
```

Then visit <http://localhost:5000>.

## Configuration

All configuration is via `FATHOM_`-prefixed environment variables. Every variable has a sensible default so Fathom runs out of the box.

| Variable | Default | Description |
|---|---|---|
| `FATHOM_SECRET_KEY` | `fathom-dev-key` | Flask session secret key |
| `FATHOM_HOST` | `0.0.0.0` | Server bind address |
| `FATHOM_PORT` | `5000` | Server port |
| `FATHOM_DEBUG` | `false` | Enable Flask debug mode |
| `FATHOM_WORKERS` | `2` | Gunicorn worker processes |
| `FATHOM_DEFAULT_RETURN_RATE` | `0.07` | Default investment return rate (7%) |
| `FATHOM_DEFAULT_INFLATION_RATE` | `0.03` | Default inflation rate (3%) |
| `FATHOM_DEFAULT_TAX_RATE` | `0.22` | Default marginal tax rate (22%) |

You can also use a `.env` file in the project root.

## Architecture

Fathom is a Flask application that renders all pages server-side using Jinja2 templates styled with Pico CSS. HTMX handles partial page updates so the UI feels responsive without full reloads. Charts are rendered as SVG on the server. The application is stateless with no database -- all financial math runs in Python using Decimal arithmetic for precision.

```
src/fathom/
  __init__.py      # Entry point
  app.py           # Flask app factory
  config.py        # Application configuration (pydantic-settings)
  routes.py        # HTTP route handlers
  engine.py        # Calculation engine orchestrator
  models.py        # Domain models (FinancingOption, etc.)
  forms.py         # Form parsing and validation
  results.py       # Results analysis for display
  charts.py        # SVG chart data preparation
  amortization.py  # Loan amortization calculations
  opportunity.py   # Opportunity cost calculations
  inflation.py     # Inflation adjustment
  tax.py           # Tax savings calculations
  caveats.py       # Warning/caveat generation
  templates/       # Jinja2 HTML templates
  static/          # CSS and vendor assets
```

## Development

```bash
uv sync                    # Install dependencies
uv run fathom              # Run dev server
uv run pytest              # Run tests
uv run ruff check .        # Lint
uv run ruff format .       # Format
uv run ty check            # Type check (ty)
uv run pyrefly check       # Type check (pyrefly)
uv run prek run            # Pre-commit hooks
```

## Contributing

1. Fork the repository and create a feature branch.
2. Ensure all quality checks pass before submitting:
   ```bash
   uv run ruff check .
   uv run ruff format --check .
   uv run ty check
   uv run pyrefly check
   uv run pytest
   ```
3. Run `uv run prek run` to validate pre-commit hooks.
4. Submit a pull request with a clear description of the change.
5. All financial calculations must remain server-side Python (no client-side JS duplication).

## License

MIT -- see [LICENSE](LICENSE).
