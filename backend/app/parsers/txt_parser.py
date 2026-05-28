import re

SPEAKER_LINE_RE = re.compile(r"^([A-Z][\w\s]{0,40}):\s*(.+)$")


def parse(content: bytes, filename: str) -> tuple[str, list[str]]:
    """Parse a plain-text transcript into (raw_text, unique_speakers).

    Detects "Speaker: text" lines via regex. When no speaker turns are found,
    returns the full decoded text with an empty speaker list. The text itself
    is returned verbatim — never reformatted.
    """
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("Cannot read TXT file") from exc

    speakers: list[str] = []
    seen: set[str] = set()

    for line in decoded.splitlines():
        match = SPEAKER_LINE_RE.match(line)
        if match:
            speaker = match.group(1).strip()
            if speaker and speaker not in seen:
                seen.add(speaker)
                speakers.append(speaker)

    return (decoded, speakers)
