/**
 * Client for the Minutely report-generation endpoint.
 *
 * Posts three files as multipart form-data to the local Next.js API route
 * at /api/generate-report, which proxies to the backend server-side.
 * This avoids CORS entirely and keeps BACKEND_URL out of the browser bundle.
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

export interface GenerateReportRequest extends ReportFiles {
  model: string;
  systemPrompt: string;
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

export async function generateReport(
  req: GenerateReportRequest,
): Promise<ReportResult> {
  const fd = new FormData();
  fd.append("my_context", req.my_context);
  fd.append("client_context", req.client_context);
  fd.append("transcript", req.transcript);
  fd.append("model", req.model);
  fd.append("system_prompt", req.systemPrompt);

  const response = await fetch(`/api/generate-report`, {
    method: "POST",
    body: fd,
  });

  if (!response.ok) {
    // Try to surface the backend's JSON detail (e.g. {"detail": "..."}); if
    // that fails or the body is plain text, fall back to the raw text. This
    // produces a much more useful error than the bare HTTP reason phrase.
    let detail = "";
    try {
      const contentType = response.headers.get("content-type") ?? "";
      if (contentType.includes("application/json")) {
        const payload = (await response.json()) as { detail?: unknown };
        if (typeof payload.detail === "string") {
          detail = payload.detail;
        } else if (payload.detail !== undefined) {
          detail = JSON.stringify(payload.detail);
        }
      } else {
        detail = await response.text();
      }
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
