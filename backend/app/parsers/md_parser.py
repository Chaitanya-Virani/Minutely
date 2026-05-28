import re

CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`([^`]*)`")
HEADER_RE = re.compile(r"^#+\s+", re.MULTILINE)
BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
ITALIC_RE = re.compile(r"\*(.+?)\*", re.DOTALL)
LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]*\)")


def parse(content: bytes, filename: str) -> tuple[str, list[str]]:
    """Strip Markdown formatting and return plain text.

    Removal order:
      1. Fenced code blocks ```...```
      2. Inline code `...`        → kept content unwrapped
      3. ATX headers ^#+\\s        → stripped marker
      4. Bold **...**             → kept content
      5. Italic *...*             → kept content
      6. Links [text](url)        → kept text
    """
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("Cannot read MD file") from exc

    text = CODE_FENCE_RE.sub("", decoded)
    text = INLINE_CODE_RE.sub(r"\1", text)
    text = HEADER_RE.sub("", text)
    text = BOLD_RE.sub(r"\1", text)
    text = ITALIC_RE.sub(r"\1", text)
    text = LINK_RE.sub(r"\1", text)

    return (text, [])
