# Phase 4: Deployment and Polish - Research

**Researched:** 2026-03-10
**Domain:** Containerization, configuration management, production deployment, visual polish
**Confidence:** HIGH

## Summary

Phase 4 transforms a working Flask application into a production-ready, self-hostable package. The core work involves: (1) adding Gunicorn as a production WSGI server with a multi-stage Dockerfile, (2) replacing CDN links with bundled static assets for air-gapped operation, (3) implementing typed environment configuration via pydantic-settings, (4) writing comprehensive README and MIT license, and (5) performing visual polish and code quality review.

The application already performs well under the 300ms requirement (measured at ~4ms average for form submission via test client), so PERF-01 is essentially met -- verification is the main task rather than optimization. The existing codebase has 107 tests, a clean app factory pattern, and well-organized templates, making the deployment wrapping straightforward.

**Primary recommendation:** Structure work as infrastructure-first (Dockerfile + config + static bundling), then documentation (README + LICENSE), then polish (visual audit + code review + test gaps).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Gunicorn as WSGI server (add as dependency)
- Multi-stage Docker build: build stage installs uv + dependencies, final stage copies only the application
- Bundle Pico CSS and HTMX JS locally in static/ instead of CDN links -- fully self-contained, works air-gapped
- No docker-compose.yml -- just Dockerfile with `docker build` + `docker run` instructions
- .dockerignore to exclude .planning/, tests/, .git/, etc.
- All env vars prefixed with `FATHOM_` (e.g., FATHOM_SECRET_KEY, FATHOM_PORT)
- Use pydantic-settings for typed configuration with .env file support (add pydantic-settings as dependency)
- Configurable variables: SECRET_KEY, HOST, PORT, DEBUG, WORKERS, DEFAULT_RETURN_RATE, DEFAULT_INFLATION_RATE, DEFAULT_TAX_RATE
- Invalid env var values crash on startup with clear validation error (pydantic validation, fail fast)
- Sensible defaults for all values so app runs with zero configuration
- MIT license
- CSS refinement within existing Pico CSS framework -- not a full redesign
- Claude performs a visual audit via Playwright: spacing, alignment, typography, color consistency, card styling
- Fix rough edges from Phase 2/3 implementation
- No dark mode (v2 ENH-02), no print-friendly CSS (v2 ENH-01)
- Full quality sweep: security, correctness, code organization, naming, duplication
- Fill test coverage gaps -- identify untested paths and add missing tests
- Update pyproject.toml metadata: description, classifiers (skip homepage/repo URLs for now)
- Comprehensive README: what it is, quick start (Docker + bare-metal via uv), env var reference, architecture overview, development setup, contributing guidelines
- Technical and concise tone -- assumes developer audience
- No screenshots or visual media

### Claude's Discretion
- Exact Gunicorn worker count default and configuration
- Docker base image choice (python:3.14-slim or similar)
- .dockerignore contents
- Specific CSS fixes identified during visual audit
- Code review priority order and which issues to fix vs flag
- Test structure for new coverage tests

### Deferred Ideas (OUT OF SCOPE)
- Dark mode / prefers-color-scheme support -- v2 ENH-02
- Print-friendly CSS for results page -- v2 ENH-01
- GitHub repo URLs in pyproject.toml -- add when repo is public
- docker-compose.yml -- consider for future if users request it
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TECH-05 | Dockerfile provided for containerized self-hosting | Multi-stage build with python:3.14-slim, gunicorn entrypoint, bundled static assets |
| TECH-06 | Configuration overridable via environment variables (default rates, branding) | pydantic-settings BaseSettings with FATHOM_ prefix, typed validation, .env support |
| TECH-07 | README with clear self-hosting instructions | Docker + uv bare-metal instructions, env var reference table, architecture overview |
| TECH-08 | Open-source license (MIT or Apache 2.0) | MIT license (user decision) |
| PERF-01 | Results page rendered within 300ms of form submission | Already met (~4ms avg). Verify with Playwright timing measurement |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| gunicorn | latest (23.x) | Production WSGI server | Flask's recommended production server; handles worker management, graceful restarts |
| pydantic-settings | latest (2.x) | Typed environment configuration | Validates env vars at startup, supports .env files, provides FATHOM_ prefix natively |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-dotenv | latest | .env file parsing for pydantic-settings | Required by pydantic-settings for .env file support; install as extra |

### Static Assets to Bundle
| Asset | Version | Source URL | Target Path |
|-------|---------|------------|-------------|
| Pico CSS | 2.x | `https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css` | `src/fathom/static/vendor/pico.min.css` |
| HTMX | 2.0.8 | `https://cdn.jsdelivr.net/npm/htmx.org@2.0.8/dist/htmx.min.js` | `src/fathom/static/vendor/htmx.min.js` |

**Installation:**
```bash
uv add gunicorn pydantic-settings
# python-dotenv is pulled in by pydantic-settings[dotenv] or installed separately
uv add python-dotenv
```

**Static asset download:**
```bash
mkdir -p src/fathom/static/vendor
curl -o src/fathom/static/vendor/pico.min.css "https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"
curl -o src/fathom/static/vendor/htmx.min.js "https://cdn.jsdelivr.net/npm/htmx.org@2.0.8/dist/htmx.min.js"
```

## Architecture Patterns

### Recommended New Files
```
src/fathom/
  config.py          # pydantic-settings Settings class
  static/
    vendor/
      pico.min.css   # Bundled Pico CSS
      htmx.min.js    # Bundled HTMX
Dockerfile           # Multi-stage build
.dockerignore        # Exclude non-production files
LICENSE              # MIT license text
README.md            # Comprehensive documentation (rewrite existing empty file)
```

### Pattern 1: pydantic-settings Configuration
**What:** Typed Settings class with env var prefix and defaults
**When to use:** App startup configuration loading
**Example:**
```python
# Source: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FATHOM_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    secret_key: str = "fathom-dev-key"
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    workers: int = 2
    default_return_rate: float = 0.07
    default_inflation_rate: float = 0.03
    default_tax_rate: float = 0.22
```

Fields map to env vars like `FATHOM_SECRET_KEY`, `FATHOM_PORT`, etc. Invalid values (e.g., `FATHOM_PORT=abc`) cause a ValidationError at startup with clear error messages.

### Pattern 2: App Factory Integration
**What:** Pass Settings into create_app, wire config values to Flask and defaults
**Example:**
```python
from fathom.config import Settings

def create_app(settings: Settings | None = None) -> Flask:
    if settings is None:
        settings = Settings()
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = settings.secret_key
    # Store settings for access in routes
    app.config["FATHOM_SETTINGS"] = settings
    # ... register blueprints
    return app
```

### Pattern 3: Gunicorn Entry Point
**What:** Main entry point switches between dev (app.run) and production (gunicorn)
**Example:**
```python
def main() -> None:
    from fathom.config import Settings
    settings = Settings()
    if settings.debug:
        from fathom.app import create_app
        app = create_app(settings)
        app.run(host=settings.host, port=settings.port, debug=True)
    else:
        import subprocess
        subprocess.run([
            "gunicorn",
            "--bind", f"{settings.host}:{settings.port}",
            "--workers", str(settings.workers),
            "fathom.app:create_app()",
        ], check=True)
```

Alternative (simpler, recommended): Just document the gunicorn command. The `main()` function stays as dev server; production uses gunicorn directly:
```bash
# Production
gunicorn -w 4 -b 0.0.0.0:5000 'fathom.app:create_app()'
```

### Pattern 4: Multi-Stage Dockerfile
**What:** Two-stage build -- builder installs deps, runner copies only what's needed
**Example:**
```dockerfile
# Stage 1: Build
FROM python:3.14-slim AS builder
RUN pip install uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY src/ src/

# Stage 2: Run
FROM python:3.14-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 5000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "fathom.app:create_app()"]
```

### Pattern 5: Template CDN-to-Local Migration
**What:** Replace CDN links in base.html with local static file references
**Current:**
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
<script src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.8/dist/htmx.min.js"></script>
```
**Target:**
```html
<link rel="stylesheet" href="{{ url_for('static', filename='vendor/pico.min.css') }}">
<script src="{{ url_for('static', filename='vendor/htmx.min.js') }}"></script>
```

### Anti-Patterns to Avoid
- **Subprocess gunicorn from main():** Adds unnecessary complexity. Use gunicorn directly in Dockerfile CMD or document the command. Keep main() as dev-only entry point.
- **Hardcoded config in multiple places:** All configurable values must flow through the Settings class -- no stray os.environ.get calls.
- **Alpine Docker images for Python:** Slower builds due to musl compilation of C extensions. Use python:3.14-slim (Debian-based).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Env var parsing with types | Custom os.environ parsers | pydantic-settings | Type coercion, validation errors, .env support, prefix handling |
| WSGI process management | Custom process spawning | gunicorn | Worker lifecycle, graceful restarts, signal handling |
| CSS framework | Custom styles from scratch | Pico CSS (bundled) | Already in use; just bundle locally |

## Common Pitfalls

### Pitfall 1: Forgetting to Copy uv.lock into Docker Build
**What goes wrong:** Dependencies not locked, builds may differ
**Why it happens:** uv.lock is easy to forget alongside pyproject.toml
**How to avoid:** Always COPY both pyproject.toml and uv.lock before `uv sync --frozen`
**Warning signs:** `uv sync` fails with "no lock file found" or resolves different versions

### Pitfall 2: pydantic-settings v2 Import Path
**What goes wrong:** ImportError if importing from pydantic instead of pydantic_settings
**Why it happens:** v1 had BaseSettings in pydantic; v2 moved it to separate package
**How to avoid:** Always `from pydantic_settings import BaseSettings, SettingsConfigDict`
**Warning signs:** ImportError on startup

### Pitfall 3: env_prefix Case Sensitivity
**What goes wrong:** Env vars not picked up
**Why it happens:** pydantic-settings is case-insensitive by default, but the prefix must match the SettingsConfigDict setting
**How to avoid:** Use lowercase field names with uppercase prefix `FATHOM_` -- env vars like `FATHOM_SECRET_KEY` map to field `secret_key`

### Pitfall 4: Static Files Not Included in Docker Image
**What goes wrong:** 404 errors for CSS/JS in container
**Why it happens:** COPY only copies src/ code but misses static assets if they're not under src/
**How to avoid:** Vendor files are under `src/fathom/static/vendor/` so they're included with `COPY src/ src/`

### Pitfall 5: Gunicorn Worker Count Too High for Single Container
**What goes wrong:** OOM kills in resource-constrained environments
**Why it happens:** Default formula (2*CPU+1) assumes dedicated server
**How to avoid:** Default to 2 workers for a self-hosted tool; make configurable via FATHOM_WORKERS

### Pitfall 6: Missing python-dotenv for .env File Support
**What goes wrong:** .env files silently ignored
**Why it happens:** pydantic-settings requires python-dotenv to be installed for env_file to work
**How to avoid:** Add python-dotenv as explicit dependency alongside pydantic-settings

## Code Examples

### Settings Class (config.py)
```python
# Source: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="FATHOM_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    secret_key: str = "fathom-dev-key"
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    workers: int = 2
    default_return_rate: float = 0.07
    default_inflation_rate: float = 0.03
    default_tax_rate: float = 0.22
```

### Updated create_app
```python
from fathom.config import Settings

def create_app(settings: Settings | None = None) -> Flask:
    if settings is None:
        settings = Settings()
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["FATHOM_SETTINGS"] = settings
    from fathom.routes import bp
    app.register_blueprint(bp)
    return app
```

### Gunicorn in Dockerfile CMD
```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "fathom.app:create_app()"]
```

For configurable workers, use shell form:
```dockerfile
CMD gunicorn --bind 0.0.0.0:${FATHOM_PORT:-5000} --workers ${FATHOM_WORKERS:-2} 'fathom.app:create_app()'
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pydantic v1 BaseSettings (built-in) | pydantic-settings v2 (separate package) | Pydantic v2 (2023) | Must install pydantic-settings separately |
| Flask dev server in production | Gunicorn WSGI | Always best practice | Required for concurrent request handling |
| CDN-hosted assets | Local bundling | Trend toward self-contained deployments | Works air-gapped, no external dependency at runtime |

## Performance Analysis

**Current baseline (measured 2026-03-10):**
- Form submission + calculation + rendering: ~4ms average via test client
- Min: 1.7ms, Max: 21.2ms across 10 runs
- Status: PERF-01 (300ms) is already met by approximately 75x margin

**Gunicorn overhead:** Adds minimal latency (~1-2ms for worker dispatch). Production performance will remain well under 300ms.

**Verification approach:** Use Playwright MCP to measure end-to-end time from form submission to results display in a real browser, including network roundtrip and DOM rendering.

## Open Questions

1. **Gunicorn worker default**
   - What we know: Formula is (2*CPU+1), but self-hosted tools run on varied hardware
   - Recommendation: Default to 2 workers; document the formula for users who want to tune

2. **Default rates wiring**
   - What we know: Settings has DEFAULT_RETURN_RATE etc., routes.py currently hardcodes defaults (0.07, 3, 22)
   - Recommendation: Routes should read defaults from app.config["FATHOM_SETTINGS"] so env vars actually take effect

3. **Base template changes for vendor assets**
   - What we know: base.html has CDN links on lines 8 and 13
   - Recommendation: Simple find-replace; no structural template changes needed

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.x |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `uv run pytest -x -q` |
| Full suite command | `uv run pytest` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TECH-05 | Dockerfile builds and runs | integration | `docker build -t fathom . && docker run --rm -p 5000:5000 -d fathom` + curl test | No -- Wave 0 |
| TECH-06 | Env vars override config | unit | `uv run pytest tests/test_config.py -x` | No -- Wave 0 |
| TECH-06 | Invalid env var crashes on startup | unit | `uv run pytest tests/test_config.py -x` | No -- Wave 0 |
| TECH-07 | README exists with required sections | smoke | `test -s README.md` | No |
| TECH-08 | LICENSE file exists | smoke | `test -s LICENSE` | No |
| PERF-01 | Response within 300ms | integration | `uv run pytest tests/test_performance.py -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest -x -q`
- **Per wave merge:** `uv run pytest && uv run ruff check . && uv run ruff format --check .`
- **Phase gate:** Full suite + Playwright visual/functional verification

### Wave 0 Gaps
- [ ] `tests/test_config.py` -- covers TECH-06 (Settings validation, defaults, env prefix, invalid values)
- [ ] `tests/test_performance.py` -- covers PERF-01 (response time assertion under 300ms via test client)
- [ ] Docker build verification -- manual or CI (Playwright cannot test Docker build)

## Sources

### Primary (HIGH confidence)
- [Flask Gunicorn deployment docs](https://flask.palletsprojects.com/en/stable/deploying/gunicorn/) -- gunicorn command syntax, app factory pattern support
- [pydantic-settings docs](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) -- BaseSettings, env_prefix, SettingsConfigDict, .env support
- [Python 3.14-slim Docker image](https://hub.docker.com/layers/library/python/3.14-slim/) -- confirmed available on Docker Hub

### Secondary (MEDIUM confidence)
- [PythonSpeed Docker base image guide (Feb 2026)](https://pythonspeed.com/articles/base-image-python-docker-images/) -- recommends slim over Alpine for Python
- [Pico CSS GitHub](https://github.com/picocss/pico) -- v2 self-hosting via download
- [HTMX docs](https://htmx.org/docs/) -- self-hosting via direct download

### Tertiary (LOW confidence)
- None -- all findings verified against official sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- gunicorn and pydantic-settings are well-documented, stable libraries
- Architecture: HIGH -- patterns are standard Flask deployment practices
- Pitfalls: HIGH -- verified against official docs and common deployment issues
- Performance: HIGH -- measured directly against running application

**Research date:** 2026-03-10
**Valid until:** 2026-04-10 (stable domain, no fast-moving concerns)
