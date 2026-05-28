from pathlib import Path

from . import csv_parser, docx_parser, md_parser, pdf_parser, txt_parser

SUPPORTED_EXTENSIONS: set[str] = {".csv", ".txt", ".pdf", ".docx", ".md"}


def parse_file(content: bytes, filename: str) -> tuple[str, list[str]]:
    """Dispatch a file to the appropriate parser based on its extension.

    Args:
        content: Raw bytes of the uploaded file.
        filename: Original filename, used solely for extension detection.

    Returns:
        A tuple of (raw_text, unique_speakers) where speakers are deduplicated
        in order of first appearance.

    Raises:
        ValueError: If the file is empty or its extension is unsupported.
    """
    if not content:
        raise ValueError("Empty file")

    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")

    if ext == ".csv":
        return csv_parser.parse(content, filename)
    if ext == ".txt":
        return txt_parser.parse(content, filename)
    if ext == ".pdf":
        return pdf_parser.parse(content, filename)
    if ext == ".docx":
        return docx_parser.parse(content, filename)
    if ext == ".md":
        return md_parser.parse(content, filename)

    # Defensive: SUPPORTED_EXTENSIONS gate above should make this unreachable.
    raise ValueError(f"Unsupported file type: {ext}")
