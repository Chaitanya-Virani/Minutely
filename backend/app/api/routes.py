"""HTTP route definitions for the Minutely backend.

Exposes an ``APIRouter`` containing:

* ``GET  /health``           — lightweight liveness probe used by Railway.
* ``POST /generate-report``  — multipart endpoint that accepts the three input
  documents (my context, client context, transcript), runs the single Claude
  extraction call, builds the PDF, and streams it back to the caller.

The router is mounted at ``/api/v1`` from :mod:`app.main`.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from io import BytesIO
from pathlib import Path
from typing import Final

import anthropic
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.parsers import parse_file
from app.report.extractor import extract_report
from app.report.pdf_builder import generate_pdf
from app.report.schemas import MeetingReport

__all__ = ["router"]


logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Validation constants
# ---------------------------------------------------------------------------

# Context documents are tightly constrained to Markdown — the prompt templates
# downstream assume Markdown-flavoured prose, not arbitrary file shapes.
_CONTEXT_EXTENSIONS: Final[frozenset[str]] = frozenset({".md"})

# Transcripts may arrive from a variety of meeting tools, so the dispatcher in
# ``app.parsers.router`` accepts a wider set.
_TRANSCRIPT_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {".csv", ".txt", ".pdf", ".docx", ".md"}
)

# Maximum length of the slug used in the ``Content-Disposition`` filename.
_MAX_SLUG_LENGTH: Final[int] = 60

# Fallback filename stem when slugification leaves nothing usable.
_FALLBACK_SLUG: Final[str] = "meeting-report"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extension(filename: str | None) -> str:
    """Return the lowercase suffix (including the leading dot) of ``filename``.

    Returns an empty string when ``filename`` is ``None`` or has no suffix.
    """
    if not filename:
        return ""
    return Path(filename).suffix.lower()


def _slugify(title: str) -> str:
    """Convert a meeting title into an ASCII-safe filename stem.

    - Lowercase.
    - Strip accents (NFKD normalisation, drop combining marks).
    - Replace whitespace runs with single hyphens.
    - Drop any character outside ``[a-z0-9-_]``.
    - Collapse repeated hyphens and trim leading/trailing separators.
    - Truncate to :data:`_MAX_SLUG_LENGTH` characters.
    - Fall back to :data:`_FALLBACK_SLUG` if nothing survives.
    """
    normalised = unicodedata.normalize("NFKD", title)
    ascii_only = normalised.encode("ascii", "ignore").decode("ascii")
    ascii_only = ascii_only.lower()
    # Whitespace → hyphen first so word boundaries survive the strip step.
    ascii_only = re.sub(r"\s+", "-", ascii_only)
    # Keep only the allowed character class.
    ascii_only = re.sub(r"[^a-z0-9\-_]", "", ascii_only)
    # Collapse runs of hyphens that the previous steps may have produced.
    ascii_only = re.sub(r"-{2,}", "-", ascii_only)
    ascii_only = ascii_only.strip("-_")
    if not ascii_only:
        return _FALLBACK_SLUG
    return ascii_only[:_MAX_SLUG_LENGTH].rstrip("-_") or _FALLBACK_SLUG


async def _read_and_validate(
    file: UploadFile,
    *,
    field: str,
    allowed_extensions: frozenset[str],
    max_bytes: int,
) -> tuple[bytes, str]:
    """Read an ``UploadFile`` fully, enforcing size and extension rules.

    Returns the raw bytes and the original filename. Raises ``HTTPException``
    with HTTP 400 for missing filenames / bad extensions and HTTP 413 for
    oversize payloads.
    """
    filename = file.filename or ""
    ext = _extension(filename)
    if ext not in allowed_extensions:
        allowed = ", ".join(sorted(allowed_extensions))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported file type for '{field}': '{ext or 'unknown'}'. "
                f"Allowed: {allowed}."
            ),
        )

    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File '{field}' exceeds the maximum allowed size of "
                f"{max_bytes // (1024 * 1024)} MB."
            ),
        )
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File '{field}' is empty.",
        )
    return content, filename


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    """Return a static liveness payload.

    Railway polls this endpoint to determine service readiness. Kept dependency
    free so it never fails for reasons unrelated to the process being up.
    """
    return {"status": "ok"}


@router.post(
    "/generate-report",
    tags=["report"],
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF meeting report generated from the three inputs.",
        },
        400: {"description": "Invalid input (bad extension, empty file, parse error)."},
        413: {"description": "One of the uploaded files exceeds the size limit."},
        502: {"description": "Upstream Claude API returned an unusable response."},
        503: {"description": "Upstream Claude API is rate limiting after retries."},
    },
)
async def generate_report(
    my_context: UploadFile = File(
        ...,
        description="Markdown file describing the user's perspective and goals.",
    ),
    client_context: UploadFile = File(
        ...,
        description="Markdown file describing the client / counterparty context.",
    ),
    transcript: UploadFile = File(
        ...,
        description="Meeting transcript: .csv, .txt, .pdf, .docx, or .md.",
    ),
    settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    """Generate a PDF meeting report from three uploaded documents.

    Pipeline (all in-process, stateless):

    1. Validate extension + size for each upload.
    2. Parse my_context and client_context as Markdown via ``parse_file``.
    3. Parse transcript into ``(text, speakers)`` via ``parse_file``.
    4. Call ``extract_report`` → validated :class:`MeetingReport`.
    5. Render PDF bytes via ``generate_pdf``.
    6. Stream the PDF back with a ``Content-Disposition`` attachment header.
    """
    max_bytes = settings.max_file_size_bytes

    my_context_bytes, my_context_name = await _read_and_validate(
        my_context,
        field="my_context",
        allowed_extensions=_CONTEXT_EXTENSIONS,
        max_bytes=max_bytes,
    )
    client_context_bytes, client_context_name = await _read_and_validate(
        client_context,
        field="client_context",
        allowed_extensions=_CONTEXT_EXTENSIONS,
        max_bytes=max_bytes,
    )
    transcript_bytes, transcript_name = await _read_and_validate(
        transcript,
        field="transcript",
        allowed_extensions=_TRANSCRIPT_EXTENSIONS,
        max_bytes=max_bytes,
    )

    # Parse — any ValueError from a parser is a client-input problem.
    try:
        my_context_text, _ = parse_file(my_context_bytes, my_context_name)
        client_context_text, _ = parse_file(client_context_bytes, client_context_name)
        transcript_text, speakers = parse_file(transcript_bytes, transcript_name)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # Extract — funnel SDK errors to deterministic HTTP statuses.
    try:
        report: MeetingReport = await extract_report(
            my_context_text,
            client_context_text,
            transcript_text,
            speakers,
        )
    except ValueError as exc:
        # extractor's prompt builder may raise ValueError on bad inputs.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ValidationError as exc:
        logger.exception("Claude returned a payload that failed Pydantic validation")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Claude returned invalid structure",
        ) from exc
    except anthropic.RateLimitError as exc:
        logger.error("Anthropic rate limit reached after retries: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Claude API is rate limiting; please retry shortly.",
        ) from exc
    except anthropic.APIStatusError as exc:
        logger.error(
            "Anthropic API status error %s: %s",
            getattr(exc, "status_code", "?"),
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Claude API error: {exc}",
        ) from exc

    # Render PDF — any failure here is a server bug, let the global handler log it.
    pdf_bytes = generate_pdf(report)

    filename = f"{_slugify(report.meeting_title)}.pdf"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers=headers,
    )
