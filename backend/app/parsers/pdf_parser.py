import io

from pypdf import PdfReader


def parse(content: bytes, filename: str) -> tuple[str, list[str]]:
    """Extract text from a PDF transcript.

    Speakers list is always empty — PDFs do not reliably carry speaker turns
    that can be detected without heuristics outside this parser's scope.
    """
    try:
        reader = PdfReader(io.BytesIO(content))
        pages_text: list[str] = []
        for page in reader.pages:
            pages_text.append(page.extract_text() or "")
        return ("\n".join(pages_text), [])
    except Exception as exc:
        raise ValueError("Cannot read PDF file") from exc
