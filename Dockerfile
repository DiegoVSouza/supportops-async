FROM ghcr.io/astral-sh/uv:0.12.7 AS uv-bin
FROM python:3.13.12-slim AS builder
COPY --from=uv-bin /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY supportops_async ./supportops_async
RUN uv sync --locked --no-dev

FROM python:3.13.12-slim AS runtime
ENV PATH="/app/.venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 LLM_MODE=fake
WORKDIR /app
RUN groupadd --system --gid 10001 app && useradd --system --uid 10001 --gid app --home-dir /app app
COPY --from=builder --chown=app:app /app /app
USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "supportops_async.api.runtime:app", "--host", "0.0.0.0", "--port", "8000"]
