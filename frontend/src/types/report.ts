/**
 * TypeScript mirrors of the Pydantic models in `backend/app/report/schemas.py`.
 *
 * The MVP returns a rendered PDF blob, but these types live here so any future
 * JSON-aware view (preview pane, in-page editor, history list) can consume the
 * structured report without re-deriving the shape.
 */

export type Priority = "high" | "medium" | "low";

export type KeyDateType = "deadline" | "milestone" | "meeting" | "event";

export type OutcomeStatus = "decided" | "pending" | "tabled";

export interface ActionItem {
  task: string;
  assignee: string;
  due_date: string | null;
  priority: Priority;
  context: string;
}

export interface KeyDate {
  date: string;
  description: string;
  type: KeyDateType;
}

export interface Outcome {
  title: string;
  description: string;
  owner: string | null;
  status: OutcomeStatus;
}

export interface DiscussionPoint {
  topic: string;
  summary: string;
  participants_involved: string[];
  resolution: string | null;
}

export interface ParticipantSummary {
  role: string;
  tasks: string[];
  contributions: string;
}

export interface MeetingReport {
  meeting_title: string;
  meeting_date: string;
  duration_estimate: string;
  executive_summary: string;
  outcomes: Outcome[];
  action_items: ActionItem[];
  key_dates: KeyDate[];
  discussion_points: DiscussionPoint[];
  participant_summary: Record<string, ParticipantSummary>;
  risks_and_blockers: string[];
  follow_up_meetings: string[];
}
