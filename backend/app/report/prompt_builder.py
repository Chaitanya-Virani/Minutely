"""Pure prompt construction for the report extractor.

No I/O, no Anthropic SDK imports, no logging — every function in this module is
deterministic and trivially unit-testable. Cache placement matches the
project's prompt-caching strategy: the system instructions and `my_context`
share one cached block, the per-call `client_context` is its own cached block,
and the transcript (which changes every call) is never cached.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "SYSTEM_INSTRUCTIONS",
    "build_system",
    "build_user_messages",
]


SYSTEM_INSTRUCTIONS: str = """\
You are Minutely, an expert meeting-intelligence analyst. You read raw meeting
transcripts together with two reference documents and produce a single,
structured meeting report by calling the `generate_report` tool.

PERSPECTIVE
- Write everything from the first-person "my" perspective, where "I"/"me"/"my"
  refer to the person described in the `<my_context>` document supplied with
  the system prompt. The executive summary in particular must read like a
  personal recap: what I came away with, what matters to me, what I now owe
  others. Never narrate as a neutral third party.

CLIENT CONTEXT
- Use the `<client_context>` block to anchor names, project codenames,
  acronyms, deliverables, and organisational relationships. When a transcript
  mentions an ambiguous initial or nickname, resolve it against the client
  context whenever possible.

EXTRACTION REQUIREMENTS
- Meeting metadata: produce a concise `meeting_title` (under 12 words), the
  best `meeting_date` you can infer (ISO 8601 when possible, otherwise a
  human phrase such as "unspecified - likely early May 2026"), and a
  `duration_estimate` based on transcript length and pacing.
- Executive summary: 3-4 sentences, first-person, covering what was decided,
  what I committed to, and the most important risk or follow-up.
- Outcomes: every distinct decision or conclusion, ordered by importance,
  each tagged with status `decided` / `pending` / `tabled` and an `owner`
  when one is identifiable.
- Action items: every concrete task assigned, with `assignee`, `due_date`
  (ISO 8601 if explicit, otherwise the verbatim human phrase, otherwise
  null), inferred `priority` (`high` for blockers and time-critical items,
  `medium` for normal work, `low` for nice-to-haves) and a one-sentence
  `context` explaining where in the meeting it came from. Order high
  priority first, then chronologically.
- Key dates: pull every date mentioned (deadlines, milestones, scheduled
  meetings, launches, demos). Use ISO 8601 when inferable, otherwise the
  human phrase. Classify each one as `deadline` / `milestone` / `meeting`
  / `event`.
- Discussion points: cluster the conversation into major topics. For each
  topic produce a short label, a concise summary of the viewpoints raised,
  the list of participants who spoke to it, and a `resolution` if one was
  reached (otherwise null).
- Participant summary: one entry per distinct speaker, keyed by the name
  exactly as it appears in the transcript. Capture their inferred role
  (use "Unknown" if no signal), the tasks they took on, and a one-to-two
  sentence summary of their contributions.
- Risks and blockers: every concern, dependency, or unresolved issue that
  could derail the work, each phrased as a single short sentence.
- Follow-up meetings: every sync or follow-up that was proposed or
  scheduled, including timing when known.

EXTRACTION COMPLETENESS (CRITICAL)
- The risks array must be populated independently of the executive summary.
  If a risk, competitive threat, external pressure, or unresolved dependency
  is mentioned anywhere in the transcript — including casually, in passing,
  or as background context — it belongs in the risks array as a structured
  entry. The executive summary mentioning a risk does not satisfy this
  requirement. A risk mentioned in prose and not in the array is a missing
  extraction. Specific signals that must always produce a risks entry: a
  named competitor being evaluated, a contract renewal under pressure, a
  ticket SLA breach, a stakeholder expressing dissatisfaction, a deadline
  that has already slipped, and any blocker that is not yet resolved at the
  time of the meeting.
- The follow_up_meetings array must capture every sync, review, or formal
  meeting that was proposed or confirmed during the transcript — including
  standing meetings, QBRs, checkpoint reviews, training sessions, and
  executive alignment sessions. A meeting that appears in the key_dates
  array is not exempt — if it was scheduled or proposed during the
  transcript it must also appear in follow_up_meetings. The two arrays
  serve different purposes: key_dates is a chronological timeline,
  follow_up_meetings is the actionable list of things that need to be
  booked or confirmed. Missing a follow-up that was verbally agreed in the
  transcript is an extraction failure.

ATTRIBUTION RULES
- Always attribute statements to the speaker who actually made them; never
  fabricate quotes or assign actions to people who did not accept them.
- If the transcript supplies a `<known_speakers>` hint, treat that as the
  authoritative speaker set when disambiguating turns.
- If an action item has no clear assignee, choose the participant whose
  responsibilities (per client context) most plausibly cover it; do not
  invent new names.

TOOL CONTRACT
- You MUST call the `generate_report` tool exactly once. Do not emit any
  prose, commentary, or reasoning outside the tool call.
- Populate every required field in the schema. Use empty arrays for
  optional list fields if no content applies; do not omit them.
"""


def build_system(
    my_context: str, *, system_instructions: str | None = None
) -> list[dict[str, Any]]:
    """Build the `system` payload as a list of cached text content blocks.

    Two blocks rather than one so the cache survives changes to `my_context`
    being toggled separately from the static instructions, and so the block
    boundaries are easy to inspect during debugging. Both blocks are marked
    `ephemeral` because the (instructions + my_context) pair is the most
    expensive and most frequently reused prefix across calls.

    When `system_instructions` is provided and non-blank, it replaces the
    default :data:`SYSTEM_INSTRUCTIONS` in the first block; otherwise the
    default is used.
    """
    instructions = (
        system_instructions
        if (system_instructions and system_instructions.strip())
        else SYSTEM_INSTRUCTIONS
    )
    return [
        {
            "type": "text",
            "text": instructions,
            "cache_control": {"type": "ephemeral"},
        },
        {
            "type": "text",
            "text": f"<my_context>\n{my_context}\n</my_context>",
            "cache_control": {"type": "ephemeral"},
        },
    ]


def build_user_messages(
    client_context: str,
    transcript: str,
    speakers: list[str],
) -> list[dict[str, Any]]:
    """Build the `messages` payload — a single user turn with multiple blocks.

    Block 1 (cached): client context — stable across re-runs for the same
    client engagement, so it is worth caching independently of the system
    prefix.

    Block 2 (NOT cached): the transcript itself, plus an optional
    `<known_speakers>` hint when the parser identified speaker labels.

    Block 3 (NOT cached): a final short reminder that Claude must call the
    `generate_report` tool exactly once.
    """
    transcript_text = f"<transcript>\n{transcript}\n</transcript>"
    if speakers:
        speaker_list = ", ".join(speakers)
        transcript_text = (
            f"<known_speakers>{speaker_list}</known_speakers>\n{transcript_text}"
        )

    instruction_text = (
        "Now produce the meeting report by calling the `generate_report` tool "
        "exactly once. Do not write any prose response — the tool call is the "
        "only acceptable output. Every required field in the schema must be "
        "populated."
    )

    return [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"<client_context>\n{client_context}\n</client_context>",
                    "cache_control": {"type": "ephemeral"},
                },
                {
                    "type": "text",
                    "text": transcript_text,
                },
                {
                    "type": "text",
                    "text": instruction_text,
                },
            ],
        }
    ]
