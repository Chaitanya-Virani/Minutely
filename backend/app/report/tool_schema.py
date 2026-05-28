"""Anthropic tool definition for the report extractor.

The input schema is generated directly from `app.report.schemas.MeetingReport`
(the single source of truth). Any field change in `schemas.py` is automatically
reflected in the tool definition Claude sees — no hand-maintained duplicate.
"""

from __future__ import annotations

from typing import Any

from app.report.schemas import MeetingReport

__all__ = [
    "TOOL_NAME",
    "TOOL_DESCRIPTION",
    "get_tool_definition",
    "get_tool_choice",
]


TOOL_NAME: str = "generate_report"

TOOL_DESCRIPTION: str = (
    "Extract a comprehensive, structured meeting report from the supplied "
    "transcript, my personal context, and the client context. Produce a single "
    "MeetingReport object containing the meeting metadata (title, date, "
    "duration estimate), an executive summary written from the first-person "
    "'my' perspective, all concrete outcomes/decisions, every action item with "
    "an assignee and inferred priority, key dates (deadlines, milestones, "
    "scheduled meetings, events), the major discussion points with the "
    "participants involved, a per-participant summary keyed by speaker name, "
    "and any risks, blockers, or proposed follow-up meetings. Always call this "
    "tool exactly once; never respond in prose."
)


def _normalize_input_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Make the Pydantic JSON Schema safe to send as Anthropic `input_schema`.

    - Ensures the top level declares `"type": "object"` (required by Anthropic).
    - Strips Pydantic-only `title` keys from the root and every nested `$defs`
      definition / property, because they are noise to the model but the schema
      remains valid JSON Schema (Anthropic accepts `$defs` / `$ref`).
    """

    def _strip_titles(node: Any) -> None:
        if isinstance(node, dict):
            node.pop("title", None)
            for value in node.values():
                _strip_titles(value)
        elif isinstance(node, list):
            for item in node:
                _strip_titles(item)

    normalized = dict(schema)
    if normalized.get("type") != "object":
        normalized["type"] = "object"
    _strip_titles(normalized)
    return normalized


def get_tool_definition() -> dict[str, Any]:
    """Return the full Anthropic tool definition dict for `generate_report`."""
    input_schema = _normalize_input_schema(MeetingReport.model_json_schema())
    return {
        "name": TOOL_NAME,
        "description": TOOL_DESCRIPTION,
        "input_schema": input_schema,
    }


def get_tool_choice() -> dict[str, str]:
    """Return the `tool_choice` payload that forces Claude to call our tool."""
    return {"type": "tool", "name": TOOL_NAME}
