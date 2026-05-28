import csv
import io

SPEAKER_KEYS: tuple[str, ...] = ("speaker", "name", "participant")
TEXT_KEYS: tuple[str, ...] = ("text", "transcript", "content", "message")
TIME_KEYS: tuple[str, ...] = ("timestamp", "time", "start")


def _find_column(fieldnames: list[str], candidates: tuple[str, ...]) -> str | None:
    """Return the original-cased fieldname whose lowercase form matches any candidate."""
    lowered = {name.lower().strip(): name for name in fieldnames if name is not None}
    for candidate in candidates:
        if candidate in lowered:
            return lowered[candidate]
    return None


def parse(content: bytes, filename: str) -> tuple[str, list[str]]:
    """Parse a CSV transcript into (raw_text, unique_speakers).

    Detects speaker / text / time columns case-insensitively. When no speaker
    column exists, joins all row values as plain text with an empty speaker list.
    """
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("Cannot read CSV file") from exc

    try:
        reader = csv.DictReader(io.StringIO(decoded))
        fieldnames = list(reader.fieldnames or [])

        speaker_col = _find_column(fieldnames, SPEAKER_KEYS)
        text_col = _find_column(fieldnames, TEXT_KEYS)
        # Time column is detected for future use; not emitted in output text.
        _ = _find_column(fieldnames, TIME_KEYS)

        lines: list[str] = []
        speakers: list[str] = []
        seen: set[str] = set()

        if speaker_col is None:
            # No recognizable speaker column: emit each row as joined cell values.
            for row in reader:
                values = [
                    (row[key] or "").strip()
                    for key in fieldnames
                    if key is not None and row.get(key) is not None
                ]
                joined = " ".join(v for v in values if v)
                if joined:
                    lines.append(joined)
            return ("\n".join(lines), [])

        for row in reader:
            speaker_raw = (row.get(speaker_col) or "").strip()
            if text_col is not None:
                text_raw = (row.get(text_col) or "").strip()
            else:
                # No explicit text column: concatenate all non-speaker cells.
                text_raw = " ".join(
                    (row[key] or "").strip()
                    for key in fieldnames
                    if key is not None and key != speaker_col and row.get(key) is not None
                ).strip()

            if not text_raw:
                continue

            if speaker_raw:
                lines.append(f"{speaker_raw}: {text_raw}")
                if speaker_raw not in seen:
                    seen.add(speaker_raw)
                    speakers.append(speaker_raw)
            else:
                lines.append(text_raw)

        return ("\n".join(lines), speakers)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Cannot read CSV file") from exc
