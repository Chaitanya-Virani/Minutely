/**
 * Client for the Minutely report-generation endpoint.
 *
 * Posts three files as multipart form-data and expects an
 * `application/pdf` blob back. Filename is pulled from the
 * `Content-Disposition` header when present.
 */

export interface ReportFiles {
  my_context: File;
  client_context: File;
  transcript: File;
}

export interface ReportResult {
  blob: Blob;
  filename: string;
}

const DEFAULT_FILENAME = "meeting-report.pdf";

function parseFilenameFromDisposition(header: string | null): string {
  if (!header) {
    return DEFAULT_FILENAME;
  }

  // RFC 5987 style: filename*=UTF-8''...
  const utf8Match = /filename\*=(?:UTF-8'')?([^;]+)/i.exec(header);
  if (utf8Match && utf8Match[1]) {
    try {
      return decodeURIComponent(utf8Match[1].trim().replace(/^"|"$/g, ""));
    } catch {
      // fall through to the plain variant
    }
  }

  const plainMatch = /filename="?([^";]+)"?/i.exec(header);
  if (plainMatch && plainMatch[1]) {
    return plainMatch[1].trim();
  }

  return DEFAULT_FILENAME;
}

export async function generateReport(files: ReportFiles): Promise<ReportResult> {
  const fd = new FormData();
  fd.append("my_context", files.my_context);
  fd.append("client_context", files.client_context);
  fd.append("transcript", files.transcript);

  const response = await fetch("/api/v1/generate-report", {
    method: "POST",
    body: fd,
  });

  if (!response.ok) {
    let detail = "";
    try {
      detail = await response.text();
    } catch {
      detail = "";
    }
    const trimmed = detail.trim();
    throw new Error(
      `Report generation failed (${response.status} ${response.statusText})${
        trimmed.length > 0 ? `: ${trimmed}` : ""
      }`,
    );
  }

  const blob = await response.blob();
  const filename = parseFilenameFromDisposition(
    response.headers.get("Content-Disposition"),
  );

  return { blob, filename };
}
