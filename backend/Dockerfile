# syntax=docker/dockerfile:1.7
# Minutely backend image — FastAPI on uvicorn, Python 3.11 slim.
# Layer order matches the project's caching rule: copy the dependency manifest
# first, install, then copy application code so source edits don't bust the
# pip layer. Railway injects PORT at runtime; we default to 8000 for local
# `docker compose up` and `docker run` parity.
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependency layer — only the manifest, so source edits don't invalidate it.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application code layer.
COPY app ./app

# Drop privileges. UID 1000 matches the convention used by Railway's runtime.
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Railway sets $PORT; fall back to 8000 for local use.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
