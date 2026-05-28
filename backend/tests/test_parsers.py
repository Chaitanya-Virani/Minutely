"""Unit tests for ``app.parsers`` — dispatcher and every per-format parser.

Each test exercises real bytes through the real parser code; nothing is
mocked. PDF and DOCX fixtures are generated in-memory from the same libraries
the production parsers consume, so the suite is self-contained and does not
ship binary blobs.
"""

from __future__ import annotations

import io

import pytest

from app.parsers import parse_file
from app.parsers import csv_parser, docx_parser, md_parser, pdf_parser, txt_parser


# ---------------------------------------------------------------------------
# Router (dispatch) tests
# ---------------------------------------------------------------------------


def test_router_unsupported_extension() -> None:
    """Files with an extension outside the allow-list raise ``ValueError``."""
    with pytest.raises(ValueError, match="Unsupported file type"):
        parse_file(b"anything", "transcript.xyz")


def test_router_empty_content() -> None:
    """Zero-byte uploads are rejected before any per-format parser runs."""
    with pytest.raises(ValueError, match="Empty file"):
        parse_file(b"", "transcript.csv")


def test_router_dispatches_by_extension() -> None:
    """The router routes ``.md`` files to the markdown parser, not the txt one."""
    text, speakers = parse_file(b"# Heading\n\nbody", "doc.md")
    # The MD parser strips the leading "# " — the txt parser would not.
    assert "Heading" in text
    assert text.lstrip().startswith("Heading")
    assert speakers == []


# ---------------------------------------------------------------------------
# CSV parser
# ---------------------------------------------------------------------------


def test_csv_zoom_style() -> None:
    """Zoom-style CSVs expose Speaker/Text columns and yield ordered speakers."""
    payload = (
        "Speaker,Text,Timestamp\n"
        "Alice,Welcome everyone to the call,00:00:01\n"
        "Bob,Thanks Alice glad to be here,00:00:05\n"
        "Alice,Let us start with the roadmap,00:00:12\n"
    ).encode("utf-8")

    text, speakers = csv_parser.parse(payload, "zoom.csv")

    assert speakers == ["Alice", "Bob"]  # order of first appearance, no dupes
    assert "Alice: Welcome everyone to the call" in text
    assert "Bob: Thanks Alice glad to be here" in text
    # Timestamp column must not bleed into the emitted body text.
    assert "00:00:01" not in text


def test_csv_no_speaker_column_falls_back_to_joined_text() -> None:
    """CSVs without a recognised speaker column emit joined cells, empty speakers."""
    payload = b"col_a,col_b\nhello,world\nfoo,bar\n"
    text, speakers = csv_parser.parse(payload, "raw.csv")

    assert speakers == []
    assert "hello world" in text
    assert "foo bar" in text


def test_csv_routed_via_parse_file() -> None:
    """End-to-end dispatch sanity check for CSV."""
    payload = b"Name,Message\nCarol,hi there\n"
    text, speakers = parse_file(payload, "x.csv")
    assert "Carol: hi there" in text
    assert speakers == ["Carol"]


# ---------------------------------------------------------------------------
# TXT parser
# ---------------------------------------------------------------------------


def test_txt_with_speakers() -> None:
    """Lines matching the ``Name: text`` pattern populate the speakers list."""
    text, speakers = txt_parser.parse(b"Alice: hi\nBob: yo", "chat.txt")
    assert speakers == ["Alice", "Bob"]
    assert "Alice: hi" in text
    assert "Bob: yo" in text


def test_txt_plain_fallback() -> None:
    """Plain prose without the speaker pattern produces an empty speaker list."""
    body = b"This is just narrative text with no name colon pattern at all."
    text, speakers = txt_parser.parse(body, "plain.txt")
    assert speakers == []
    assert text == body.decode("utf-8")


def test_txt_dedup_speakers() -> None:
    """Repeated speaker turns appear only once in the speakers list."""
    text, speakers = txt_parser.parse(
        b"Alice: one\nBob: two\nAlice: three\n",
        "dialog.txt",
    )
    assert speakers == ["Alice", "Bob"]
    assert text.count("Alice: ") == 2  # body text is preserved verbatim


# ---------------------------------------------------------------------------
# Markdown parser
# ---------------------------------------------------------------------------


def test_md_strip() -> None:
    """Headers, bold, italic, inline code and fenced code are all stripped."""
    md = (
        b"# Heading one\n"
        b"## Subheading\n"
        b"This is **bold** and *italic* and `inline` code.\n"
        b"```python\nprint('hidden')\n```\n"
        b"Visit [our site](https://example.com) for more.\n"
    )

    text, speakers = md_parser.parse(md, "notes.md")

    assert speakers == []
    # Headers: marker removed, content kept.
    assert "Heading one" in text
    assert "# Heading one" not in text
    # Bold / italic / inline code: wrappers removed, content kept.
    assert "bold" in text and "**bold**" not in text
    assert "italic" in text and "*italic*" not in text
    assert "inline" in text and "`inline`" not in text
    # Fenced code block: removed entirely.
    assert "print('hidden')" not in text
    # Links: text retained, URL dropped.
    assert "our site" in text
    assert "https://example.com" not in text


# ---------------------------------------------------------------------------
# PDF parser — generate a tiny PDF with reportlab and round-trip through pypdf.
# ---------------------------------------------------------------------------


def _make_pdf(text: str) -> bytes:
    """Generate a single-page PDF containing ``text`` using reportlab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica", 12)
    c.drawString(72, 800, text)
    c.showPage()
    c.save()
    return buf.getvalue()


def test_pdf_happy_path() -> None:
    """A reportlab-generated PDF round-trips through the parser."""
    pytest.importorskip("reportlab")
    pdf_bytes = _make_pdf("Hello from a unit-tested PDF transcript.")
    text, speakers = pdf_parser.parse(pdf_bytes, "round.pdf")
    assert speakers == []
    # pypdf preserves the substring even if surrounding whitespace differs.
    assert "Hello from a unit-tested PDF transcript." in text


def test_pdf_rejects_garbage() -> None:
    """Non-PDF bytes raise a wrapped ``ValueError`` from the parser layer."""
    with pytest.raises(ValueError, match="Cannot read PDF"):
        pdf_parser.parse(b"this is definitely not a pdf", "broken.pdf")


# ---------------------------------------------------------------------------
# DOCX parser — generate a tiny DOCX with python-docx and round-trip back.
# ---------------------------------------------------------------------------


def _make_docx(paragraphs: list[str]) -> bytes:
    """Generate a minimal DOCX file containing the supplied paragraphs."""
    from docx import Document

    doc = Document()
    for line in paragraphs:
        doc.add_paragraph(line)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_docx_happy_path() -> None:
    """A python-docx-generated DOCX round-trips through the parser."""
    pytest.importorskip("docx")
    docx_bytes = _make_docx(
        [
            "Meeting notes for the planning sync.",
            "",  # empty paragraphs must be filtered out
            "Alice will own the roadmap deliverable.",
        ]
    )
    text, speakers = docx_parser.parse(docx_bytes, "notes.docx")
    assert speakers == []
    assert "Meeting notes for the planning sync." in text
    assert "Alice will own the roadmap deliverable." in text
    # Empty paragraph contributed nothing — confirm we don't have blank lines.
    assert "\n\n" not in text


def test_docx_rejects_garbage() -> None:
    """Non-DOCX bytes raise a wrapped ``ValueError``."""
    with pytest.raises(ValueError, match="Cannot read DOCX"):
        docx_parser.parse(b"not a docx file", "broken.docx")
