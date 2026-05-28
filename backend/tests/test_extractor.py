"""Unit tests for :mod:`app.report.extractor`.

The Anthropic client singleton is patched at the attribute boundary —
``app.report.extractor._client.messages.create`` is swapped for an
``AsyncMock`` so no real HTTP request is ever issued. Sleep calls in the
retry helper are stubbed to keep the suite fast.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import anthropic
import httpx
import pytest

from app.report import extractor
from app.report.extractor import extract_report
from app.report.schemas import MeetingReport
from app.report.tool_schema import TOOL_NAME


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sample_report_dict() -> dict[str, Any]:
    """Return a minimum-viable :class:`MeetingReport` dict suitable for tool input."""
    return {
        "meeting_title": "Roadmap Sync",
        "meeting_date": "2026-05-15",
        "duration_estimate": "~30 min",
        "executive_summary": (
            "I agreed to publish the roadmap on Friday and Bob will own the "
            "API estimate. The biggest risk is the timeline slipping."
        ),
        "outcomes": [
            {
                "title": "Publish roadmap",
                "description": "Roadmap to be published by EOW.",
                "owner": "Alice",
                "status": "decided",
            }
        ],
        "action_items": [
            {
                "task": "Publish roadmap",
                "assignee": "Alice",
                "due_date": "2026-05-23",
                "priority": "high",
                "context": "From the roadmap discussion.",
            }
        ],
        "key_dates": [
            {
                "date": "2026-05-23",
                "description": "Roadmap publication",
                "type": "deadline",
            }
        ],
        "discussion_points": [
            {
                "topic": "API timeline",
                "summary": "Discussed possible slippage.",
                "participants_involved": ["Alice", "Bob"],
                "resolution": "Bob to provide revised estimate.",
            }
        ],
        "participant_summary": {
            "Alice": {
                "role": "Product Lead",
                "tasks": ["Publish roadmap"],
                "contributions": "Drove the roadmap discussion.",
            }
        },
        "risks_and_blockers": ["API timeline may slip."],
        "follow_up_meetings": ["Roadmap review next Monday."],
    }


def _make_tool_use_response(tool_input: dict[str, Any]) -> SimpleNamespace:
    """Build a duck-typed Anthropic response with a single ``tool_use`` block."""
    block = SimpleNamespace(type="tool_use", name=TOOL_NAME, input=tool_input)
    usage = SimpleNamespace(
        input_tokens=10,
        output_tokens=20,
        cache_creation_input_tokens=0,
        cache_read_input_tokens=0,
    )
    return SimpleNamespace(content=[block], usage=usage)


def _make_text_only_response() -> SimpleNamespace:
    """Build a response that contains only a ``text`` block — no tool_use."""
    block = SimpleNamespace(type="text", text="hello there, no tool call")
    usage = SimpleNamespace(
        input_tokens=5,
        output_tokens=5,
        cache_creation_input_tokens=0,
        cache_read_input_tokens=0,
    )
    return SimpleNamespace(content=[block], usage=usage)


def _make_rate_limit_error() -> anthropic.RateLimitError:
    """Construct a ``RateLimitError`` without hitting the network."""
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx.Response(status_code=429, request=request)
    return anthropic.RateLimitError(
        "rate limited",
        response=response,
        body=None,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_extract_report_returns_meeting_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Happy path: tool_use input is validated into a :class:`MeetingReport`."""
    payload = _sample_report_dict()
    mock_create = AsyncMock(return_value=_make_tool_use_response(payload))
    monkeypatch.setattr(extractor._client.messages, "create", mock_create)

    report = await extract_report(
        my_context="my ctx",
        client_context="client ctx",
        transcript="Alice: hi\nBob: yo",
        speakers=["Alice", "Bob"],
    )

    assert isinstance(report, MeetingReport)
    assert report.meeting_title == payload["meeting_title"]
    assert report.action_items[0].assignee == "Alice"
    assert report.participant_summary["Alice"].role == "Product Lead"
    assert mock_create.await_count == 1


async def test_extract_report_raises_when_no_tool_use(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Responses without a ``tool_use`` block bubble up as ``RuntimeError``."""
    mock_create = AsyncMock(return_value=_make_text_only_response())
    monkeypatch.setattr(extractor._client.messages, "create", mock_create)

    with pytest.raises(RuntimeError, match="generate_report"):
        await extract_report(
            my_context="my ctx",
            client_context="client ctx",
            transcript="transcript body",
            speakers=[],
        )

    assert mock_create.await_count == 1


async def test_extract_report_retries_on_rate_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two transient 429s followed by a success → three total awaits, valid result."""
    payload = _sample_report_dict()
    side_effects: list[Any] = [
        _make_rate_limit_error(),
        _make_rate_limit_error(),
        _make_tool_use_response(payload),
    ]
    mock_create = AsyncMock(side_effect=side_effects)
    monkeypatch.setattr(extractor._client.messages, "create", mock_create)

    # Stub the back-off sleep to keep the test fast.
    async def _noop_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(extractor.asyncio, "sleep", _noop_sleep)

    report = await extract_report(
        my_context="my ctx",
        client_context="client ctx",
        transcript="t",
        speakers=[],
    )

    assert isinstance(report, MeetingReport)
    assert report.meeting_title == payload["meeting_title"]
    assert mock_create.await_count == 3


async def test_extract_report_gives_up_after_max_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Persistent rate-limiting re-raises after ``_MAX_RETRIES`` attempts."""
    side_effects: list[Any] = [
        _make_rate_limit_error(),
        _make_rate_limit_error(),
        _make_rate_limit_error(),
    ]
    mock_create = AsyncMock(side_effect=side_effects)
    monkeypatch.setattr(extractor._client.messages, "create", mock_create)

    async def _noop_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(extractor.asyncio, "sleep", _noop_sleep)

    with pytest.raises(anthropic.RateLimitError):
        await extract_report(
            my_context="my ctx",
            client_context="client ctx",
            transcript="t",
            speakers=[],
        )

    assert mock_create.await_count == extractor._MAX_RETRIES
