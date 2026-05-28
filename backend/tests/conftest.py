"""Shared pytest fixtures for the Minutely backend test suite.

Every fixture in this module is import-safe — none of them perform real network
I/O against Anthropic. The ``ANTHROPIC_API_KEY`` env var is set to a sentinel
value before any application module is imported so the ``AsyncAnthropic``
client singleton in :mod:`app.report.extractor` can be constructed without a
real key.
"""

from __future__ import annotations

import os
from typing import Iterator
from unittest.mock import AsyncMock

# Set a sentinel API key before any application module is imported so that the
# module-level ``AsyncAnthropic`` client in ``app.report.extractor`` can be
# instantiated. The tests never make a real network call — every test that
# touches the extractor patches ``_client.messages.create``.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.report.schemas import (
    ActionItem,
    DiscussionPoint,
    KeyDate,
    MeetingReport,
    Outcome,
    ParticipantSummary,
)


# ---------------------------------------------------------------------------
# Sample report fixture — used by extractor and API tests alike.
# ---------------------------------------------------------------------------


def _build_sample_report() -> MeetingReport:
    """Construct a fully-populated :class:`MeetingReport` for use in tests.

    Kept as a free function (not a fixture) so it can also be called from
    helper code that needs the raw object outside the pytest dependency graph.
    """
    return MeetingReport(
        meeting_title="Quarterly Planning Sync",
        meeting_date="2026-05-20",
        duration_estimate="~45 min",
        executive_summary=(
            "I walked away with a clear set of commitments for Q3 planning. "
            "We agreed to lock the roadmap by Friday and Alice will own the "
            "follow-up doc. Main risk is the API timeline slipping into July."
        ),
        outcomes=[
            Outcome(
                title="Lock Q3 roadmap",
                description="Team agreed to finalise the Q3 roadmap by end of week.",
                owner="Alice",
                status="decided",
            ),
        ],
        action_items=[
            ActionItem(
                task="Publish roadmap doc",
                assignee="Alice",
                due_date="2026-05-23",
                priority="high",
                context="Action assigned after the roadmap discussion.",
            ),
        ],
        key_dates=[
            KeyDate(
                date="2026-05-23",
                description="Roadmap finalisation deadline",
                type="deadline",
            ),
        ],
        discussion_points=[
            DiscussionPoint(
                topic="API timeline",
                summary="Discussed risk of the API delivery slipping into July.",
                participants_involved=["Alice", "Bob"],
                resolution="Bob to share a revised estimate by Monday.",
            ),
        ],
        participant_summary={
            "Alice": ParticipantSummary(
                role="Product Lead",
                tasks=["Publish roadmap doc"],
                contributions="Drove the roadmap conversation and accepted the deliverable.",
            ),
            "Bob": ParticipantSummary(
                role="Engineering Lead",
                tasks=[],
                contributions="Raised the API timeline risk and committed to a revised estimate.",
            ),
        },
        risks_and_blockers=["API timeline may slip into July."],
        follow_up_meetings=["Roadmap review next Monday."],
    )


@pytest.fixture
def sample_report() -> MeetingReport:
    """Provide a ready-to-use :class:`MeetingReport` instance."""
    return _build_sample_report()


# ---------------------------------------------------------------------------
# TestClient fixture.
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Yield a FastAPI ``TestClient`` bound to the real ``app`` instance.

    The lifespan handler is exercised on enter/exit so the same startup /
    shutdown log lines fire as in production.
    """
    with TestClient(app) as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# Mock extractor fixture.
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_extract_report(
    monkeypatch: pytest.MonkeyPatch,
    sample_report: MeetingReport,
) -> AsyncMock:
    """Patch ``app.api.routes.extract_report`` with an ``AsyncMock``.

    Returns the mock so tests can assert call counts and inspect arguments.
    The mock resolves to :data:`sample_report` by default.
    """
    mock = AsyncMock(return_value=sample_report)
    monkeypatch.setattr("app.api.routes.extract_report", mock)
    return mock
