import io

from docx import Document


def parse(content: bytes, filename: str) -> tuple[str, list[str]]:
    """Extract text from a DOCX transcript.

    Iterates document paragraphs, skipping empty ones. Speakers list is empty;
    speaker detection on plain DOCX paragraphs is not reliable.
    """
    try:
        doc = Document(io.BytesIO(content))
        paragraphs: list[str] = []
        for p in doc.paragraphs:
            text = p.text
            if text and text.strip():
                paragraphs.append(text)
        return ("\n".join(paragraphs), [])
    except Exception as exc:
        raise ValueError("Cannot read DOCX file") from exc
