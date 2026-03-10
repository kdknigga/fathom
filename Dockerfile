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
CMD gunicorn --bind 0.0.0.0:${FATHOM_PORT:-5000} --workers ${FATHOM_WORKERS:-2} 'fathom.app:create_app()'
