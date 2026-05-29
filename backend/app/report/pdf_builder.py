"""ReportLab PDF builder for Minutely meeting reports.

Exposes a single public function, ``generate_pdf``, that consumes a
:class:`~app.report.schemas.MeetingReport` and returns the rendered PDF as
``bytes`` via an in-memory ``BytesIO`` buffer. Never writes to disk.

Layout uses Platypus flowables only (no raw canvas body text) on an A4
page. The visual identity is a dark, professional theme with high-contrast
indigo/teal accents on a white printable background.
"""

from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.doctemplate import BaseDocTemplate

from app.report.schemas import (
    ActionItem,
    DiscussionPoint,
    KeyDate,
    MeetingReport,
    Outcome,
    ParticipantSummary,
)

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------

ACCENT = HexColor("#6366F1")        # indigo
ACCENT_2 = HexColor("#14B8A6")      # teal
HEADING_DARK = HexColor("#0F172A")  # zinc-900
TEXT_BODY = HexColor("#1F2937")     # gray-800
TEXT_MUTED = HexColor("#6B7280")    # gray-500
DIVIDER = HexColor("#E5E7EB")       # gray-200

STATUS_DECIDED = HexColor("#16A34A")
STATUS_PENDING = HexColor("#D97706")
STATUS_TABLED = HexColor("#52525B")

PRIORITY_HIGH = HexColor("#DC2626")
PRIORITY_MED = HexColor("#D97706")
PRIORITY_LOW = HexColor("#52525B")

TYPE_DEADLINE = HexColor("#DC2626")
TYPE_MILESTONE = HexColor("#6366F1")
TYPE_MEETING = HexColor("#14B8A6")
TYPE_EVENT = HexColor("#52525B")

CARD_BG = HexColor("#F8FAFC")       # slate-50 — subtle card background
TABLE_HEADER_BG = HexColor("#0F172A")
TABLE_ROW_ALT = HexColor("#F1F5F9")
WHITE = colors.white

# Color lookups for the badge helpers
_STATUS_COLORS: dict[str, Any] = {
    "decided": STATUS_DECIDED,
    "pending": STATUS_PENDING,
    "tabled": STATUS_TABLED,
}

_PRIORITY_COLORS: dict[str, Any] = {
    "high": PRIORITY_HIGH,
    "medium": PRIORITY_MED,
    "low": PRIORITY_LOW,
}

_TYPE_COLORS: dict[str, Any] = {
    "deadline": TYPE_DEADLINE,
    "milestone": TYPE_MILESTONE,
    "meeting": TYPE_MEETING,
    "event": TYPE_EVENT,
}

# ---------------------------------------------------------------------------
# Page geometry
# ---------------------------------------------------------------------------

PAGE_MARGIN_LEFT = 18 * mm
PAGE_MARGIN_RIGHT = 18 * mm
PAGE_MARGIN_TOP = 18 * mm
PAGE_MARGIN_BOTTOM = 20 * mm
CONTENT_WIDTH = A4[0] - PAGE_MARGIN_LEFT - PAGE_MARGIN_RIGHT


# ---------------------------------------------------------------------------
# Style registration
# ---------------------------------------------------------------------------


def _register_styles() -> dict[str, ParagraphStyle]:
    """Build and return the complete ParagraphStyle dictionary used everywhere.

    Called once per :func:`generate_pdf` invocation so style state never
    leaks between PDFs.
    """
    base = getSampleStyleSheet()["Normal"]
    base_font = "Helvetica"
    bold_font = "Helvetica-Bold"
    italic_font = "Helvetica-Oblique"

    styles: dict[str, ParagraphStyle] = {}

    styles["title"] = ParagraphStyle(
        name="MinutelyTitle",
        parent=base,
        fontName=bold_font,
        fontSize=24,
        leading=28,
        textColor=HEADING_DARK,
        spaceAfter=4,
        alignment=TA_LEFT,
    )
    styles["subtitle"] = ParagraphStyle(
        name="MinutelySubtitle",
        parent=base,
        fontName=base_font,
        fontSize=11,
        leading=14,
        textColor=TEXT_MUTED,
        spaceAfter=2,
        alignment=TA_LEFT,
    )
    styles["section_heading"] = ParagraphStyle(
        name="MinutelySectionHeading",
        parent=base,
        fontName=bold_font,
        fontSize=14,
        leading=18,
        textColor=HEADING_DARK,
        spaceBefore=8,
        spaceAfter=6,
        alignment=TA_LEFT,
        borderPadding=(0, 0, 4, 0),
    )
    styles["body"] = ParagraphStyle(
        name="MinutelyBody",
        parent=base,
        fontName=base_font,
        fontSize=10,
        leading=14,
        textColor=TEXT_BODY,
        spaceAfter=4,
        alignment=TA_LEFT,
    )
    styles["body_strong"] = ParagraphStyle(
        name="MinutelyBodyStrong",
        parent=base,
        fontName=bold_font,
        fontSize=10,
        leading=14,
        textColor=HEADING_DARK,
        spaceAfter=2,
        alignment=TA_LEFT,
    )
    styles["muted"] = ParagraphStyle(
        name="MinutelyMuted",
        parent=base,
        fontName=italic_font,
        fontSize=9.5,
        leading=13,
        textColor=TEXT_MUTED,
        spaceAfter=4,
        alignment=TA_LEFT,
    )
    styles["meta"] = ParagraphStyle(
        name="MinutelyMeta",
        parent=base,
        fontName=base_font,
        fontSize=9,
        leading=12,
        textColor=TEXT_MUTED,
        spaceAfter=2,
        alignment=TA_LEFT,
    )
    styles["card_title"] = ParagraphStyle(
        name="MinutelyCardTitle",
        parent=base,
        fontName=bold_font,
        fontSize=11.5,
        leading=15,
        textColor=HEADING_DARK,
        spaceAfter=2,
        alignment=TA_LEFT,
    )
    styles["card_subtitle"] = ParagraphStyle(
        name="MinutelyCardSubtitle",
        parent=base,
        fontName=italic_font,
        fontSize=9.5,
        leading=12,
        textColor=TEXT_MUTED,
        spaceAfter=4,
        alignment=TA_LEFT,
    )
    styles["badge"] = ParagraphStyle(
        name="MinutelyBadge",
        parent=base,
        fontName=bold_font,
        fontSize=8,
        leading=10,
        textColor=WHITE,
        alignment=TA_CENTER,
    )
    styles["table_header"] = ParagraphStyle(
        name="MinutelyTableHeader",
        parent=base,
        fontName=bold_font,
        fontSize=9.5,
        leading=12,
        textColor=WHITE,
        alignment=TA_LEFT,
    )
    styles["table_cell"] = ParagraphStyle(
        name="MinutelyTableCell",
        parent=base,
        fontName=base_font,
        fontSize=9.5,
        leading=12,
        textColor=TEXT_BODY,
        alignment=TA_LEFT,
    )
    styles["bullet"] = ParagraphStyle(
        name="MinutelyBullet",
        parent=base,
        fontName=base_font,
        fontSize=10,
        leading=14,
        textColor=TEXT_BODY,
        leftIndent=12,
        bulletIndent=2,
        spaceAfter=2,
        alignment=TA_LEFT,
    )
    styles["footer_left"] = ParagraphStyle(
        name="MinutelyFooterLeft",
        parent=base,
        fontName=base_font,
        fontSize=8,
        leading=10,
        textColor=TEXT_MUTED,
        alignment=TA_LEFT,
    )
    styles["footer_right"] = ParagraphStyle(
        name="MinutelyFooterRight",
        parent=base,
        fontName=base_font,
        fontSize=8,
        leading=10,
        textColor=TEXT_MUTED,
        alignment=TA_RIGHT,
    )
    return styles


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _escape(text: str) -> str:
    """Minimal XML escaping for ReportLab Paragraph mini-language."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _badge(text: str, color: Any, styles: dict[str, ParagraphStyle]) -> Table:
    """A small 1-cell colored badge — color block stands in for rounded corners.

    Returns a fixed-width ``Table`` so it can be embedded as a flowable
    inline next to a heading or inside another table cell.
    """
    para = Paragraph(_escape(text), styles["badge"])
    tbl = Table(
        [[para]],
        colWidths=[max(24 * mm, len(text) * 2.6 * mm)],
        rowHeights=[6.5 * mm],
        hAlign="LEFT",
    )
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), color),
                ("TEXTCOLOR", (0, 0), (-1, -1), WHITE),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("BOX", (0, 0), (-1, -1), 0, color),
            ]
        )
    )
    return tbl


def _section_heading(text: str, styles: dict[str, ParagraphStyle]) -> KeepTogether:
    """Section heading with a short accent underline, kept together as one block."""
    heading = Paragraph(_escape(text), styles["section_heading"])
    underline = HRFlowable(
        width=40 * mm,
        thickness=2,
        color=ACCENT,
        spaceBefore=0,
        spaceAfter=4,
        hAlign="LEFT",
    )
    return KeepTogether([heading, underline])


def _muted_line(text: str, styles: dict[str, ParagraphStyle]) -> Paragraph:
    """Muted italic placeholder line used for the empty-state branches."""
    return Paragraph(_escape(text), styles["muted"])


def _truncate(text: str, limit: int) -> str:
    """Truncate ``text`` to ``limit`` characters, adding an ellipsis when cut."""
    if len(text) <= limit:
        return text
    if limit <= 1:
        return text[:limit]
    return text[: limit - 1].rstrip() + "…"


def _bulleted_list(items: list[str], styles: dict[str, ParagraphStyle]) -> list[Paragraph]:
    """Render a list of strings as ParagraphStyle bullets."""
    return [
        Paragraph(_escape(item), styles["bullet"], bulletText="•")
        for item in items
    ]


def _card_wrap(inner: list[Any], accent: Any) -> Table:
    """Wrap a list of flowables in a single-cell card with a thin left border."""
    tbl = Table(
        [[inner]],
        colWidths=[CONTENT_WIDTH],
        hAlign="LEFT",
    )
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
                ("LINEBEFORE", (0, 0), (0, -1), 2.2, accent),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return tbl


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------


def _build_header(report: MeetingReport, styles: dict[str, ParagraphStyle]) -> list[Any]:
    """Cover/header band on page 1 — title, subtitle line, accent divider."""
    story: list[Any] = []
    story.append(Paragraph(_escape(report.meeting_title), styles["title"]))
    subtitle = f"{_escape(report.meeting_date)} · {_escape(report.duration_estimate)}"
    story.append(Paragraph(subtitle, styles["subtitle"]))
    story.append(Spacer(1, 4))
    story.append(
        HRFlowable(
            width="100%",
            thickness=1.2,
            color=ACCENT,
            spaceBefore=2,
            spaceAfter=8,
        )
    )
    return story


def _build_executive_summary(
    report: MeetingReport, styles: dict[str, ParagraphStyle]
) -> list[Any]:
    story: list[Any] = []
    story.append(_section_heading("Executive Summary", styles))
    story.append(Paragraph(_escape(report.executive_summary), styles["body"]))
    story.append(Spacer(1, 6))
    return story


def _build_outcomes(
    outcomes: list[Outcome], styles: dict[str, ParagraphStyle]
) -> list[Any]:
    story: list[Any] = [_section_heading("Outcomes", styles)]
    if not outcomes:
        story.append(_muted_line("No outcomes captured.", styles))
        story.append(Spacer(1, 6))
        return story

    for outcome in outcomes:
        badge_color = _STATUS_COLORS.get(outcome.status, STATUS_TABLED)
        title_para = Paragraph(_escape(outcome.title), styles["card_title"])
        badge = _badge(outcome.status, badge_color, styles)

        header_row = Table(
            [[title_para, badge]],
            colWidths=[CONTENT_WIDTH - 16 - 30 * mm, 30 * mm],
            hAlign="LEFT",
        )
        header_row.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )

        inner: list[Any] = [
            header_row,
            Spacer(1, 4),
            Paragraph(_escape(outcome.description), styles["body"]),
        ]
        if outcome.owner:
            inner.append(
                Paragraph(
                    f"<b>Owner:</b> {_escape(outcome.owner)}",
                    styles["meta"],
                )
            )

        story.append(KeepTogether(_card_wrap(inner, badge_color)))
        story.append(Spacer(1, 6))

    return story


def _build_action_items(
    items: list[ActionItem], styles: dict[str, ParagraphStyle]
) -> list[Any]:
    story: list[Any] = [_section_heading("Action Items", styles)]
    if not items:
        story.append(_muted_line("No action items captured.", styles))
        story.append(Spacer(1, 6))
        return story

    header = [
        Paragraph("Task", styles["table_header"]),
        Paragraph("Assignee", styles["table_header"]),
        Paragraph("Due", styles["table_header"]),
        Paragraph("Priority", styles["table_header"]),
    ]
    rows: list[list[Any]] = [header]
    for item in items:
        task_html = _escape(item.task)
        if item.context:
            task_html += (
                f"<br/><font color='#6B7280' size='8'>{_escape(item.context)}</font>"
            )
        task_para = Paragraph(task_html, styles["table_cell"])
        assignee_para = Paragraph(_escape(item.assignee), styles["table_cell"])
        due_para = Paragraph(_escape(item.due_date or "—"), styles["table_cell"])
        priority_color = _PRIORITY_COLORS.get(item.priority, PRIORITY_LOW)
        priority_badge = _badge(item.priority, priority_color, styles)
        rows.append([task_para, assignee_para, due_para, priority_badge])

    col_widths = [
        CONTENT_WIDTH * 0.45,
        CONTENT_WIDTH * 0.18,
        CONTENT_WIDTH * 0.15,
        CONTENT_WIDTH * 0.22,
    ]
    tbl = Table(rows, colWidths=col_widths, hAlign="LEFT", repeatRows=1)
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, TABLE_ROW_ALT]),
                ("GRID", (0, 0), (-1, -1), 0.4, DIVIDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(tbl)
    story.append(Spacer(1, 6))
    return story


def _build_key_dates(
    dates: list[KeyDate], styles: dict[str, ParagraphStyle]
) -> list[Any]:
    story: list[Any] = [_section_heading("Key Dates", styles)]
    if not dates:
        story.append(_muted_line("No key dates captured.", styles))
        story.append(Spacer(1, 6))
        return story

    header = [
        Paragraph("Date", styles["table_header"]),
        Paragraph("Description", styles["table_header"]),
        Paragraph("Type", styles["table_header"]),
    ]
    rows: list[list[Any]] = [header]
    for entry in dates:
        type_color = _TYPE_COLORS.get(entry.type, TYPE_EVENT)
        rows.append(
            [
                Paragraph(_escape(entry.date), styles["table_cell"]),
                Paragraph(_escape(entry.description), styles["table_cell"]),
                _badge(entry.type, type_color, styles),
            ]
        )

    col_widths = [
        CONTENT_WIDTH * 0.22,
        CONTENT_WIDTH * 0.53,
        CONTENT_WIDTH * 0.25,
    ]
    tbl = Table(rows, colWidths=col_widths, hAlign="LEFT", repeatRows=1)
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, TABLE_ROW_ALT]),
                ("GRID", (0, 0), (-1, -1), 0.4, DIVIDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(tbl)
    story.append(Spacer(1, 6))
    return story


def _build_discussion_points(
    points: list[DiscussionPoint], styles: dict[str, ParagraphStyle]
) -> list[Any]:
    if not points:
        return []

    story: list[Any] = [_section_heading("Discussion Points", styles)]
    for point in points:
        inner: list[Any] = [
            Paragraph(_escape(point.topic), styles["card_title"]),
            Paragraph(_escape(point.summary), styles["body"]),
        ]
        if point.participants_involved:
            participants = ", ".join(point.participants_involved)
            inner.append(
                Paragraph(
                    f"<b>Participants:</b> {_escape(participants)}",
                    styles["meta"],
                )
            )
        if point.resolution:
            inner.append(
                Paragraph(
                    f"<b>Resolution:</b> {_escape(point.resolution)}",
                    styles["body"],
                )
            )
        story.append(KeepTogether(_card_wrap(inner, ACCENT)))
        story.append(Spacer(1, 6))

    return story


def _build_participant_summary(
    participants: dict[str, ParticipantSummary],
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    if not participants:
        return []

    story: list[Any] = [_section_heading("Per-Participant Tasks", styles)]
    for name, summary in participants.items():
        header_html = (
            f"<font name='Helvetica-Bold'>{_escape(name)}</font>"
            f" &nbsp;<font color='#6B7280'>{_escape(summary.role)}</font>"
        )
        inner: list[Any] = [
            Paragraph(header_html, styles["card_title"]),
            Paragraph(
                f"<b>Contributions:</b> {_escape(summary.contributions)}",
                styles["body"],
            ),
        ]
        if summary.tasks:
            inner.append(Paragraph("<b>Tasks:</b>", styles["body_strong"]))
            inner.extend(_bulleted_list(summary.tasks, styles))
        else:
            inner.append(_muted_line("No tasks assigned.", styles))

        story.append(KeepTogether(_card_wrap(inner, ACCENT_2)))
        story.append(Spacer(1, 6))

    return story


def _build_risks(
    risks: list[str], styles: dict[str, ParagraphStyle]
) -> list[Any]:
    if not risks:
        return []

    story: list[Any] = [_section_heading("Risks and Blockers", styles)]
    story.extend(_bulleted_list(risks, styles))
    story.append(Spacer(1, 6))
    return story


def _build_follow_ups(
    follow_ups: list[str], styles: dict[str, ParagraphStyle]
) -> list[Any]:
    if not follow_ups:
        return []

    story: list[Any] = [_section_heading("Follow-Up Meetings", styles)]
    story.extend(_bulleted_list(follow_ups, styles))
    story.append(Spacer(1, 6))
    return story


# ---------------------------------------------------------------------------
# Page decoration (header band + footer with page numbers)
# ---------------------------------------------------------------------------


class _NumberedCanvas:
    """Adapter that records page state so we can render "Page X of Y" footers.

    ReportLab does not natively know the total page count at draw time on
    arbitrary pages, so we capture each page state on ``showPage`` and emit
    the actual footer text on ``save`` after the total is known.
    """

    # NOTE: implemented via canvasmaker so we get the two-pass page counting
    # without depending on private ReportLab APIs.

    def __init__(self) -> None:  # pragma: no cover - structural placeholder
        raise RuntimeError("Use _make_canvas instead.")


def _make_canvas_maker(footer_left_text: str, styles: dict[str, ParagraphStyle]) -> type:
    """Build a canvas subclass that draws the footer with accurate page totals."""
    from reportlab.pdfgen import canvas as _canvas_module

    footer_left_style = styles["footer_left"]
    footer_right_style = styles["footer_right"]
    page_width = A4[0]
    footer_y = 10 * mm

    class NumberedCanvas(_canvas_module.Canvas):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self._saved_states: list[dict[str, Any]] = []

        def showPage(self) -> None:  # noqa: N802 - ReportLab API
            self._saved_states.append(dict(self.__dict__))
            self._startPage()

        def save(self) -> None:
            total = len(self._saved_states)
            for state in self._saved_states:
                self.__dict__.update(state)
                self._draw_footer(total)
                super().showPage()
            super().save()

        def _draw_footer(self, total_pages: int) -> None:
            page_num = self._pageNumber
            half_width = (page_width - PAGE_MARGIN_LEFT - PAGE_MARGIN_RIGHT) / 2

            # Thin divider above the footer
            self.setStrokeColor(DIVIDER)
            self.setLineWidth(0.4)
            self.line(
                PAGE_MARGIN_LEFT,
                footer_y + 5 * mm,
                page_width - PAGE_MARGIN_RIGHT,
                footer_y + 5 * mm,
            )

            left_para = Paragraph(
                _escape(footer_left_text), footer_left_style
            )
            right_para = Paragraph(
                f"Page {page_num} of {total_pages}", footer_right_style
            )
            left_para.wrapOn(self, half_width, 20)
            left_para.drawOn(self, PAGE_MARGIN_LEFT, footer_y)
            right_para.wrapOn(self, half_width, 20)
            right_para.drawOn(
                self,
                page_width - PAGE_MARGIN_RIGHT - half_width,
                footer_y,
            )

    return NumberedCanvas


def _on_page(
    canvas_obj: Any, doc: BaseDocTemplate
) -> None:
    """Decorative accent bar drawn at the top of every page."""
    canvas_obj.saveState()
    canvas_obj.setFillColor(ACCENT)
    canvas_obj.rect(
        0,
        A4[1] - 6 * mm,
        A4[0],
        6 * mm,
        stroke=0,
        fill=1,
    )
    canvas_obj.setFillColor(ACCENT_2)
    canvas_obj.rect(
        0,
        A4[1] - 6 * mm,
        45 * mm,
        6 * mm,
        stroke=0,
        fill=1,
    )
    canvas_obj.restoreState()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def generate_pdf(report: MeetingReport) -> bytes:
    """Render ``report`` as a PDF and return the raw bytes.

    The PDF is built entirely in memory; nothing is written to disk.
    """
    styles = _register_styles()
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=PAGE_MARGIN_LEFT,
        rightMargin=PAGE_MARGIN_RIGHT,
        topMargin=PAGE_MARGIN_TOP,
        bottomMargin=PAGE_MARGIN_BOTTOM,
        title=report.meeting_title,
        author="Minutely",
        subject="Meeting report",
        creator="Minutely PDF builder",
    )

    story: list[Any] = []
    story.extend(_build_header(report, styles))
    story.extend(_build_executive_summary(report, styles))
    story.extend(_build_outcomes(report.outcomes, styles))
    story.extend(_build_action_items(report.action_items, styles))
    story.extend(_build_key_dates(report.key_dates, styles))
    story.extend(_build_discussion_points(report.discussion_points, styles))
    story.extend(_build_participant_summary(report.participant_summary, styles))
    story.extend(_build_risks(report.risks_and_blockers, styles))
    story.extend(_build_follow_ups(report.follow_up_meetings, styles))

    footer_left = f"Minutely · {_truncate(report.meeting_title, 60)}"
    canvas_maker = _make_canvas_maker(footer_left, styles)

    doc.build(
        story,
        onFirstPage=_on_page,
        onLaterPages=_on_page,
        canvasmaker=canvas_maker,
    )
    return buf.getvalue()
