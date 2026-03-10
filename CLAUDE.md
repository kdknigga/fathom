# CLAUDE.md — Fathom

## Project Overview

Fathom is a financing options analyzer that helps consumers compare the true total cost of different financing options for large purchases. It accounts for opportunity costs, inflation, and tax implications.

## Tech Stack

- **Language:** Python 3.14
- **Rendering:** Server-side rendering (SSR) with minimal client-side JS
- **Interactivity:** HTMX or equivalent for partial page updates
- **Charts:** Server-rendered SVG preferred; lightweight JS charting (e.g., Chart.js) acceptable
- **Package/env management:** `uv` (not pip, not poetry, not conda)
- **Pre-commit hooks:** `prek` (a `pre-commit` drop-in replacement)

## Project Structure

```
src/fathom/          # Main application package
docs/                # Documentation (PRD, etc.)
pyproject.toml       # Project config, dependencies, ruff config
uv.lock              # Locked dependencies
```

Entry point: `src/fathom/__init__.py:main()`

## Commands

```bash
uv run fathom              # Run the application
uv run ruff check .        # Lint
uv run ruff check --fix .  # Lint with auto-fix
uv run ruff format .       # Format code
uv run ty check            # Type check (ty)
uv run pyrefly check       # Type check (pyrefly)
uv run prek run                   # Run all pre-commit hooks
uv sync                    # Sync dependencies from uv.lock
uv add <package>           # Add a dependency
uv add --dev <package>     # Add a dev dependency
```

## Code Quality Standards

All code must pass these checks with zero errors or warnings:

1. **Ruff linting** — extensive rule set configured in `pyproject.toml`
2. **Ruff formatting** — Black-compatible, double quotes, 88 char line length, spaces
3. **ty type checking** — all issues must be fixed, not ignored
4. **pyrefly type checking** — all issues must be fixed, not ignored
5. **No mypy or pyright** — only ty and pyrefly are used

Fix reported issues properly. Do not suppress errors with `# type: ignore`, `# noqa`, or by disabling rules.

## Architecture Principles

- All financial calculations must be server-side Python — never duplicate logic in client-side JS
- No persistent storage or user accounts — stateless request/response only
- Must deploy as a single process with no external database
- WCAG 2.1 AA required - visible labels, chart text alternatives, not color-only

## Dependencies

Prefer external packages over reimplementing solved problems. Favor libraries available in Context7.

## MCP Servers Available

Use these tools during development:

- **Serena** — Semantic code analysis and editing. Use for token-efficient code navigation via symbols and references instead of reading entire files.
- **Context7** — Fetch current library/framework documentation. Always use this instead of relying on training data when working with external packages.
- **Tavily** — Web search, crawling, and content extraction for research.
- **Playwright** — Browser automation for testing the web application.

## Skills available

Consider the use of the following skills that are available to you:
- claude-automation-recommender
- claude-md-improver
- frontend-design
- astral:ty
- astral:uv
- astral:ruff

## Gotchas

- `ty` and `pyrefly` may report different issues for the same code — both must pass clean
- Ruff's `D` rules require docstrings on all public modules, classes, and functions
- Ruff ignores `D203`/`D212`: use no-blank-line-before-class and multi-line-summary-second-line style
- `prek` is a drop-in replacement for `pre-commit` — use `uv run prek run` not `pre-commit run`
