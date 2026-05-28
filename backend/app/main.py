"""FastAPI application entry point for the Minutely backend.

Wires together:

* Lifespan logging (no DB / connection pools to manage — pipeline is stateless).
* CORS middleware sourced from :class:`app.config.Settings`.
* The versioned ``/api/v1`` router from :mod:`app.api.routes`.
* A root convenience handler that points at the docs + health endpoints.
* A global exception handler that logs unexpected errors with a traceback and
  returns a generic 500 JSON response without leaking internals. ``HTTPException``
  is intentionally **not** intercepted so FastAPI's default handler continues to
  return the correct status code and ``detail`` payload.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router as api_router
from app.config import settings

__all__ = ["app"]


# Configure a sensible default if the host process hasn't already set one up.
# `force=False` (the default) means this is a no-op when Railway / uvicorn / a
# test harness has already configured logging.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)
logger = logging.getLogger("minutely")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan hook for startup / shutdown logging.

    The pipeline is fully stateless (no DB pool, no warm caches, the Anthropic
    client is a module-level singleton in :mod:`app.report.extractor`), so this
    handler only emits structured log lines that make Railway boot diagnostics
    easier to read.
    """
    logger.info(
        "Minutely starting :: model=%s max_file_mb=%s cors_origins=%s",
        settings.CLAUDE_MODEL,
        settings.MAX_FILE_SIZE_MB,
        settings.CORS_ORIGINS,
    )
    try:
        yield
    finally:
        logger.info("Minutely shutting down")


app: FastAPI = FastAPI(
    title="Minutely",
    version="0.1.0",
    description=(
        "Meeting Intelligence backend: three documents in (my context, "
        "client context, transcript) → one Claude call → PDF report out."
    ),
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

_allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
_cors_origins = (
    [o.strip() for o in _allowed_origins_env.split(",") if o.strip()]
    if _allowed_origins_env
    else settings.CORS_ORIGINS
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Top-level health probe used by Railway's healthcheck."""
    return {"status": "ok", "service": "minutely-backend"}


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    """Return a tiny pointer payload for humans hitting the bare host."""
    return {
        "name": "Minutely",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------


@app.exception_handler(Exception)
async def _unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Catch-all handler for truly unexpected errors.

    Logs the full traceback for operators and returns an opaque 500 to the
    caller. FastAPI registers its own handler for ``HTTPException`` ahead of
    this one, so domain-level 4xx/5xx responses raised by route code continue
    to propagate with their original status and ``detail`` payload.
    """
    logger.exception(
        "Unhandled exception while serving %s %s",
        request.method,
        request.url.path,
        exc_info=exc,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
