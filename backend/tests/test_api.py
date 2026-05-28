"""Integration tests for the FastAPI HTTP surface.

The Anthropic call is mocked via the ``mock_extract_report`` fixture in
``conftest.py``; the PDF builder is left real so the happy-path assertion
verifies an actual PDF byte stream comes back through ``StreamingResponse``.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient


HEALTH_URL = "/api/v1/health"
GENERATE_URL = "/api/v1/generate-report"


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


def test_health(client: TestClient) -> None:
    """Liveness probe returns 200 + ``{"status": "ok"}``."""
    response = client.get(HEALTH_URL)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# /generate-report — happy path
# ---------------------------------------------------------------------------


def test_generate_report_happy_path(
    client: TestClient,
    mock_extract_report: AsyncMock,
) -> None:
    """A valid three-file POST yields a PDF response with the expected headers."""
    files = {
        "my_context": ("my.md", b"# My context\n\nI am the host.", "text/markdown"),
        "client_context": (
            "client.md",
            b"# Client context\n\nClient is Acme Corp.",
            "text/markdown",
        ),
        "transcript": (
            "chat.txt",
            b"Alice: hi\nBob: yo\n",
            "text/plain",
        ),
    }

    response = client.post(GENERATE_URL, files=files)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"

    # Content-Disposition header carries a slug-derived .pdf filename.
    disposition = response.headers.get("content-disposition", "")
    assert "attachment" in disposition
    assert ".pdf" in disposition

    # Body is a real PDF byte stream (starts with the PDF magic number).
    body = response.content
    assert body[:4] == b"%PDF", f"unexpected response prefix: {body[:8]!r}"
    assert len(body) > 1000  # any real PDF is at least a few hundred bytes

    # Extractor was called exactly once with the parsed inputs.
    assert mock_extract_report.await_count == 1
    call_kwargs = mock_extract_report.await_args
    # extract_report is invoked positionally in routes.py
    positional = call_kwargs.args
    assert len(positional) == 4
    # speakers list should reflect the txt parser output.
    assert positional[3] == ["Alice", "Bob"]


# ---------------------------------------------------------------------------
# /generate-report — validation errors
# ---------------------------------------------------------------------------


def test_generate_report_bad_extension(
    client: TestClient,
    mock_extract_report: AsyncMock,
) -> None:
    """``.txt`` is not allowed for ``my_context`` → HTTP 400."""
    files = {
        "my_context": ("my.txt", b"plain text not markdown", "text/plain"),
        "client_context": ("client.md", b"# Client", "text/markdown"),
        "transcript": ("chat.txt", b"hello", "text/plain"),
    }

    response = client.post(GENERATE_URL, files=files)

    assert response.status_code == 400
    detail = response.json().get("detail", "")
    assert "my_context" in detail
    # Extractor must not have been reached.
    assert mock_extract_report.await_count == 0


def test_generate_report_transcript_bad_extension(
    client: TestClient,
    mock_extract_report: AsyncMock,
) -> None:
    """Unsupported transcript extension (``.xyz``) is rejected with HTTP 400."""
    files = {
        "my_context": ("my.md", b"# My", "text/markdown"),
        "client_context": ("client.md", b"# Client", "text/markdown"),
        "transcript": ("chat.xyz", b"some bytes", "application/octet-stream"),
    }

    response = client.post(GENERATE_URL, files=files)

    assert response.status_code == 400
    assert "transcript" in response.json().get("detail", "")
    assert mock_extract_report.await_count == 0


def test_generate_report_oversize(
    client: TestClient,
    mock_extract_report: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Files exceeding ``MAX_FILE_SIZE_MB`` are rejected with HTTP 413.

    Drives the limit down to 1 MB via a settings override and ships a 2 MB
    transcript payload, which is well under the test runner's memory ceiling
    yet unambiguously over the limit.
    """
    from app.config import Settings, get_settings
    from app.main import app

    # Override the FastAPI settings dependency so the route sees a 1 MB cap.
    def _tiny_settings() -> Settings:
        return Settings(
            ANTHROPIC_API_KEY="test-key",
            MAX_FILE_SIZE_MB=1,
        )

    app.dependency_overrides[get_settings] = _tiny_settings
    try:
        oversize = b"A" * (2 * 1024 * 1024)  # 2 MB > 1 MB limit
        files = {
            "my_context": ("my.md", b"# My", "text/markdown"),
            "client_context": ("client.md", b"# Client", "text/markdown"),
            "transcript": ("chat.txt", oversize, "text/plain"),
        }

        response = client.post(GENERATE_URL, files=files)

        assert response.status_code == 413
        detail = response.json().get("detail", "")
        assert "transcript" in detail
        assert mock_extract_report.await_count == 0
    finally:
        app.dependency_overrides.pop(get_settings, None)
