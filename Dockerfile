# syntax=docker/dockerfile:1

# ---- Stage 1: builder ----
# Installs dependencies into a virtualenv. Build tools/caches stay in this stage.
FROM python:3.12-slim AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY src/requirements.txt .
RUN pip install -r requirements.txt

# ---- Stage 2: runtime ----
FROM python:3.12-slim AS runtime
ARG APP_VERSION=dev
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_VERSION=${APP_VERSION} \
    DB_PATH=/app/data/urls.db

# Non-root user: if the app is ever compromised, it can't write to system paths.

RUN groupadd --system --gid 10001 appuser \
 && useradd  --system --uid 10001 --gid appuser --no-create-home --shell /usr/sbin/nologin appuser

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=appuser:appuser src/ /app/
RUN mkdir -p /app/data && chown appuser:appuser /app/data

USER appuser
EXPOSE 8000

# Used by `docker run`/compose. NOTE: ECS ignores this; it uses the task definition's healthCheck.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "wsgi:app"]
