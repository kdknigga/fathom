# Phase 4: Deployment and Polish - Context

**Gathered:** 2026-03-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Application ready for self-hosting with containerization, environment configuration, comprehensive documentation, open-source license, visual polish, and code quality review. No new features or capabilities — this phase ships what Phases 1-3 built.

</domain>

<decisions>
## Implementation Decisions

### Production server & Dockerfile
- Gunicorn as WSGI server (add as dependency)
- Multi-stage Docker build: build stage installs uv + dependencies, final stage copies only the application
- Bundle Pico CSS and HTMX JS locally in static/ instead of CDN links — fully self-contained, works air-gapped
- No docker-compose.yml — just Dockerfile with `docker build` + `docker run` instructions
- .dockerignore to exclude .planning/, tests/, .git/, etc.

### Environment variable design
- All env vars prefixed with `FATHOM_` (e.g., FATHOM_SECRET_KEY, FATHOM_PORT)
- Use pydantic-settings for typed configuration with .env file support (add pydantic-settings as dependency)
- Configurable variables: SECRET_KEY, HOST, PORT, DEBUG, WORKERS, DEFAULT_RETURN_RATE, DEFAULT_INFLATION_RATE, DEFAULT_TAX_RATE
- Invalid env var values crash on startup with clear validation error (pydantic validation, fail fast)
- Sensible defaults for all values so app runs with zero configuration

### README
- Comprehensive documentation: what it is, quick start (Docker + bare-metal via uv), env var reference, architecture overview, development setup, contributing guidelines
- Both Docker and `uv run fathom` installation methods documented
- Technical and concise tone — assumes developer audience
- No screenshots or visual media

### License
- MIT license

### Visual enhancement
- CSS refinement within existing Pico CSS framework — not a full redesign
- Claude performs a visual audit via Playwright: spacing, alignment, typography, color consistency, card styling
- Fix any rough edges from Phase 2/3 implementation
- No dark mode (v2 ENH-02), no print-friendly CSS (v2 ENH-01)

### Code review
- Full quality sweep: security, correctness, code organization, naming, duplication
- Fill test coverage gaps — identify untested paths and add missing tests
- Update pyproject.toml metadata: description, classifiers (skip homepage/repo URLs for now)

### Claude's Discretion
- Exact Gunicorn worker count default and configuration
- Docker base image choice (python:3.14-slim or similar)
- .dockerignore contents
- Specific CSS fixes identified during visual audit
- Code review priority order and which issues to fix vs flag
- Test structure for new coverage tests

</decisions>

<specifics>
## Specific Ideas

- pydantic-settings chosen explicitly over python-dotenv — provides typed validation, env var parsing, and .env support in one package
- Bundling static assets locally aligns with the "single process, no external dependencies" philosophy from PROJECT.md
- Crash-on-bad-config is the right UX for a self-hosted tool — silent misconfiguration is worse than a startup error
- Code review should result in actual fixes, not just a report — ship clean

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `create_app()` factory in app.py — already accepts SECRET_KEY from env var, needs expansion for other config
- `fathom:main` entry point in __init__.py — currently runs `app.run(debug=True)`, needs production mode
- Pico CSS loaded from CDN in base.html — needs replacement with local copy
- HTMX 2.0.8 loaded from CDN in base.html — needs replacement with local copy

### Established Patterns
- Flask app factory pattern (app.py) — pydantic-settings config integrates here
- Jinja2 templates with partials (templates/partials/) — well-organized
- Pico CSS with custom style.css overrides — refinements go in style.css
- Full test suite in tests/ — new coverage tests follow existing patterns

### Integration Points
- __init__.py:main() — needs to use gunicorn in production, app.run() in development
- app.py:create_app() — config loading changes from os.environ.get to pydantic-settings model
- base.html — CDN links replaced with local static file references
- pyproject.toml — add gunicorn, pydantic-settings dependencies; update metadata

</code_context>

<deferred>
## Deferred Ideas

- Dark mode / prefers-color-scheme support — v2 ENH-02
- Print-friendly CSS for results page — v2 ENH-01
- GitHub repo URLs in pyproject.toml — add when repo is public
- docker-compose.yml — consider for future if users request it

</deferred>

---

*Phase: 04-deployment-and-polish*
*Context gathered: 2026-03-10*
