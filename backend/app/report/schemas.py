"""Pydantic v2 models powering both the Anthropic tool_use input schema and the ReportLab PDF builder input — rename a field here and both downstream consumers must follow."""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator

__all__ = [
    "ActionItem",
    "KeyDate",
    "Outcome",
    "DiscussionPoint",
    "ParticipantSummary",
    "MeetingReport",
]


class ActionItem(BaseModel):
    task: str = Field(..., description="The concrete action to take, phrased as an imperative.")
    assignee: str = Field(..., description="Name of the person responsible for completing this action.")
    due_date: Optional[str] = Field(
        default=None,
        description="ISO 8601 date (YYYY-MM-DD) if explicit, otherwise a human phrase like 'next Friday' or 'end of Q2'. Null if no due date was mentioned.",
    )
    priority: Literal["high", "medium", "low"] = Field(
        ...,
        description="Priority level inferred from urgency cues in the discussion: 'high' for blockers or time-critical items, 'medium' for normal work, 'low' for nice-to-haves.",
    )
    context: str = Field(
        ...,
        description="One-sentence explanation of why this action was assigned and which part of the meeting it came from.",
    )


class KeyDate(BaseModel):
    date: str = Field(
        ...,
        description="ISO 8601 date (YYYY-MM-DD) when inferable, otherwise a human phrase such as 'next sprint' or 'mid-July'.",
    )
    description: str = Field(..., description="What is happening on this date — short, specific, and self-contained.")
    type: Literal["deadline", "milestone", "meeting", "event"] = Field(
        ...,
        description="Category of date: 'deadline' for due dates, 'milestone' for project markers, 'meeting' for scheduled syncs, 'event' for launches/demos/external happenings.",
    )


class Outcome(BaseModel):
    title: str = Field(..., description="Short title for the decision or outcome (under 10 words).")
    description: str = Field(..., description="Full description of what was decided or concluded, including any relevant rationale.")
    owner: Optional[str] = Field(
        default=None,
        description="Person accountable for the outcome's execution or follow-through, if one was identified. Null if not assigned.",
    )
    status: Literal["decided", "pending", "tabled"] = Field(
        ...,
        description="Resolution state: 'decided' for firm decisions, 'pending' for items still under discussion, 'tabled' for items explicitly deferred.",
    )


class DiscussionPoint(BaseModel):
    topic: str = Field(..., description="Short label for the topic discussed (under 10 words).")
    summary: str = Field(..., description="Concise summary of what was discussed about this topic and the key viewpoints raised.")
    participants_involved: list[str] = Field(
        default_factory=list,
        description="Names of the meeting participants who contributed to this specific discussion point.",
    )
    resolution: Optional[str] = Field(
        default=None,
        description="How the topic was resolved, if at all — e.g. a decision, a deferral, or a next step. Null if discussed without resolution.",
    )


class ParticipantSummary(BaseModel):
    role: str = Field(
        ...,
        description="Role or title inferred from context (e.g. 'CTO', 'PM', 'Engineering Lead'). Use 'Unknown' if no role signal is present.",
    )
    tasks: list[str] = Field(
        default_factory=list,
        description="Tasks or action items assigned to this person during the meeting, each as a short phrase.",
    )
    contributions: str = Field(
        ...,
        description="Brief one-to-two-sentence summary of what this participant brought to the meeting — their main points, questions, or commitments.",
    )


class MeetingReport(BaseModel):
    meeting_title: str = Field(..., description="Concise descriptive title for the meeting (under 12 words).")
    meeting_date: str = Field(
        ...,
        description="ISO 8601 date (YYYY-MM-DD) if a date is inferable from the transcript, otherwise the best human-phrase guess such as 'unspecified — likely early May 2026'.",
    )
    duration_estimate: str = Field(
        ...,
        description="Rough duration estimate based on transcript length and pacing (e.g. '~45 min', '~1h 15min').",
    )
    executive_summary: str = Field(
        ...,
        description="Three-to-four sentence overview of the meeting, framed from the first-person 'my' perspective per the client context document — what I came away with and why it matters.",
    )
    outcomes: list[Outcome] = Field(
        default_factory=list,
        description="Discrete decisions or conclusions reached during the meeting, ordered by importance.",
    )
    action_items: list[ActionItem] = Field(
        default_factory=list,
        description="Concrete action items assigned during the meeting, ordered by priority then chronologically.",
    )
    key_dates: list[KeyDate] = Field(
        default_factory=list,
        description="Important dates mentioned in the meeting — deadlines, milestones, scheduled meetings, or events.",
    )
    discussion_points: list[DiscussionPoint] = Field(
        default_factory=list,
        description="Major topics discussed during the meeting, each with its own summary and resolution status.",
    )
    participant_summary: dict[str, ParticipantSummary] = Field(
        default_factory=dict,
        description="Per-participant summary keyed by the participant's name as it appears in the transcript.",
    )
    risks_and_blockers: list[str] = Field(
        default_factory=list,
        description="Risks, blockers, open concerns, or unresolved dependencies raised during the meeting, each as a short sentence.",
    )

    @field_validator("risks_and_blockers", mode="before")
    @classmethod
    def _coerce_risks(cls, value: Any) -> Any:
        if not isinstance(value, list):
            return value
        coerced: list[Any] = []
        for item in value:
            if isinstance(item, dict) and item:
                coerced.append(next(iter(item.values())))
            else:
                coerced.append(item)
        return coerced

    follow_up_meetings: list[str] = Field(
        default_factory=list,
        description="Follow-up meetings or syncs that were proposed or scheduled, each as a short descriptive phrase including timing if known.",
    )
