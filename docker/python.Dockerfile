FROM python:3.12-slim AS base
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gcc g++ && rm -rf /var/lib/apt/lists/*
COPY .tool-versions /app/
COPY pkg/python/ /app/pkg/python/
COPY proto/ /app/proto/
COPY pyproject.toml /app/

FROM base AS builder
RUN pip install --no-cache-dir uv
COPY services/ /app/services/
RUN uv sync --frozen --no-dev

FROM python:3.12-slim AS production
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY services/ /app/services/
COPY pkg/python/ /app/pkg/python/
EXPOSE 8000 50051
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8000/health
ENTRYPOINT ["python", "-m", "uvicorn"]
