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
CONFIG_URL = "/api/v1/config"
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
# /config
# ---------------------------------------------------------------------------


def test_config(client: TestClient) -> None:
    """``GET /config`` returns 3 models, the default, and a non-empty prompt."""
    response = client.get(CONFIG_URL)
    assert response.status_code == 200
    body = response.json()
    assert len(body["models"]) == 3
    assert body["default_model"] == "claude-sonnet-4-6"
    assert isinstance(body["default_system_prompt"], str)
    assert body["default_system_prompt"].strip()
    # Each model entry has the frozen contract shape.
    for option in body["models"]:
        assert set(option) == {"id", "label", "description"}


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
# /generate-report — model + system_prompt form fields
# ---------------------------------------------------------------------------


def _valid_files() -> dict[str, tuple[str, bytes, str]]:
    """Return a valid three-file payload for the multipart POST."""
    return {
        "my_context": ("my.md", b"# My context\n\nI am the host.", "text/markdown"),
        "client_context": (
            "client.md",
            b"# Client context\n\nClient is Acme Corp.",
            "text/markdown",
        ),
        "transcript": ("chat.txt", b"Alice: hi\nBob: yo\n", "text/plain"),
    }


def test_generate_report_bad_model(
    client: TestClient,
    mock_extract_report: AsyncMock,
) -> None:
    """An unknown model is rejected with 400 and never reaches the extractor."""
    response = client.post(
        GENERATE_URL,
        files=_valid_files(),
        data={"model": "bogus-model"},
    )

    assert response.status_code == 400
    assert "bogus-model" in response.json().get("detail", "")
    assert mock_extract_report.await_count == 0


def test_generate_report_whitespace_prompt_becomes_none(
    client: TestClient,
    mock_extract_report: AsyncMock,
) -> None:
    """A whitespace-only system_prompt is passed to the extractor as None."""
    response = client.post(
        GENERATE_URL,
        files=_valid_files(),
        data={"system_prompt": "   "},
    )

    assert response.status_code == 200
    assert mock_extract_report.await_count == 1
    assert mock_extract_report.await_args.kwargs["system_instructions"] is None


def test_generate_report_passes_model_and_prompt(
    client: TestClient,
    mock_extract_report: AsyncMock,
) -> None:
    """A valid model + custom prompt are forwarded as extractor kwargs."""
    response = client.post(
        GENERATE_URL,
        files=_valid_files(),
        data={
            "model": "claude-haiku-4-5-20251001",
            "system_prompt": "Custom instructions",
        },
    )

    assert response.status_code == 200
    assert mock_extract_report.await_count == 1
    kwargs = mock_extract_report.await_args.kwargs
    assert kwargs["model"] == "claude-haiku-4-5-20251001"
    assert kwargs["system_instructions"] == "Custom instructions"


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
