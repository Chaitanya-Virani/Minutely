"""Claude-powered report extractor.

Owns the single `AsyncAnthropic` client instance for the process and exposes
one async entry point, `extract_report`, that turns the three input documents
into a validated `MeetingReport`. All structured output is obtained via the
forced `generate_report` tool call defined in `app.report.tool_schema`.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import anthropic
from anthropic import AsyncAnthropic

from app.config import settings
from app.report.prompt_builder import build_system, build_user_messages
from app.report.schemas import MeetingReport
from app.report.tool_schema import TOOL_NAME, get_tool_choice, get_tool_definition

__all__ = ["extract_report"]


logger = logging.getLogger(__name__)


# Module-level singleton — instantiated exactly once per process. Re-creating
# the client per request would defeat HTTP connection pooling and add latency.
_client: AsyncAnthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)


_MAX_RETRIES: int = 3
# A full report (outcomes, action items, key dates, discussion points,
# per-participant summaries, risks, follow-ups) exceeds 4096 output tokens on
# substantial meetings. At 4096 the tool_use JSON was truncated before the
# trailing schema fields, which then silently defaulted to empty arrays
# (notably risks_and_blockers and follow_up_meetings). 16000 leaves comfortable
# headroom while staying well under the model's max output.
_MAX_TOKENS: int = 16000


async def _create_with_retry(
    *,
    model: str,
    system: list[dict[str, Any]],
    messages: list[dict[str, Any]],
    tool_def: dict[str, Any],
    tool_choice: dict[str, str],
) -> Any:
    """Call `messages.create` with exponential-backoff retry on rate limits.

    Retries: up to `_MAX_RETRIES` attempts total. Backoff: `2 ** attempt`
    seconds (1s, 2s, 4s). Final failure re-raises the underlying
    `RateLimitError`. Other Anthropic errors are not retried.
    """
    last_exc: anthropic.RateLimitError | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            return await _client.messages.create(
                model=model,
                max_tokens=_MAX_TOKENS,
                system=system,
                messages=messages,
                tools=[tool_def],
                tool_choice=tool_choice,
            )
        except anthropic.RateLimitError as exc:
            last_exc = exc
            if attempt == _MAX_RETRIES - 1:
                logger.error(
                    "Anthropic rate limit hit on final retry attempt %d/%d; giving up",
                    attempt + 1,
                    _MAX_RETRIES,
                )
                raise
            backoff_seconds = 2 ** attempt
            logger.warning(
                "Anthropic rate limit hit (attempt %d/%d); backing off %ds",
                attempt + 1,
                _MAX_RETRIES,
                backoff_seconds,
            )
            await asyncio.sleep(backoff_seconds)
    # Unreachable: loop either returns or raises, but mypy/pylance want it.
    assert last_exc is not None
    raise last_exc


def _log_usage(response: Any) -> None:
    """Emit a single info-level line summarising token usage and cache hits."""
    usage = getattr(response, "usage", None)
    if usage is None:
        logger.info("Anthropic response received with no usage payload")
        return
    logger.info(
        "Anthropic usage: input_tokens=%s output_tokens=%s "
        "cache_creation_input_tokens=%s cache_read_input_tokens=%s",
        getattr(usage, "input_tokens", None),
        getattr(usage, "output_tokens", None),
        getattr(usage, "cache_creation_input_tokens", None),
        getattr(usage, "cache_read_input_tokens", None),
    )


def _extract_tool_input(response: Any) -> dict[str, Any]:
    """Locate the forced tool_use block and return its `input` payload."""
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == TOOL_NAME:
            tool_input = getattr(block, "input", None)
            if not isinstance(tool_input, dict):
                raise RuntimeError(
                    f"Claude tool_use block for '{TOOL_NAME}' had non-dict input: "
                    f"{type(tool_input).__name__}"
                )
            return tool_input
    raise RuntimeError("Claude did not call generate_report tool")


async def extract_report(
    my_context: str,
    client_context: str,
    transcript: str,
    speakers: list[str],
    *,
    model: str | None = None,
    system_instructions: str | None = None,
) -> MeetingReport:
    """Run a single Claude extraction and return a validated `MeetingReport`.

    Parameters
    ----------
    model:
        Anthropic model identifier to use for this call. Falls back to
        ``settings.CLAUDE_MODEL`` when ``None``.
    system_instructions:
        Optional override for the default system instructions. When ``None`` or
        blank, the built-in :data:`SYSTEM_INSTRUCTIONS` are used.

    Raises
    ------
    anthropic.RateLimitError
        If all retry attempts are exhausted.
    anthropic.APIStatusError, anthropic.APIError
        Propagated from the Anthropic SDK; the API layer maps to HTTP codes.
    pydantic.ValidationError
        If Claude returned a tool input that does not match `MeetingReport`.
    RuntimeError
        If Claude returned no `generate_report` tool_use block.
    """
    resolved_model = model or settings.CLAUDE_MODEL
    system = build_system(
        my_context=my_context,
        system_instructions=system_instructions,
    )
    messages = build_user_messages(
        client_context=client_context,
        transcript=transcript,
        speakers=speakers,
    )
    tool_def = get_tool_definition()
    tool_choice = get_tool_choice()

    response = await _create_with_retry(
        model=resolved_model,
        system=system,
        messages=messages,
        tool_def=tool_def,
        tool_choice=tool_choice,
    )

    _log_usage(response)
    tool_input = _extract_tool_input(response)
    return MeetingReport.model_validate(tool_input)
