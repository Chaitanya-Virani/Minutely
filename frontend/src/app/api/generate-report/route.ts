// IMPORTANT: This proxy MUST stay a raw multipart passthrough. The request body
// is forwarded as an untouched ArrayBuffer with the original content-type so the
// multipart boundary is preserved. Do NOT refactor this to parse/re-encode the
// body as JSON or FormData — doing so would break multipart uploads (including
// the `model` and `system_prompt` form fields).
import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = (
  process.env.BACKEND_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

export async function POST(request: NextRequest) {
  const contentType = request.headers.get("content-type") ?? "";

  // Forward raw body with original content-type so the multipart boundary is preserved.
  const body = await request.arrayBuffer();

  let upstream: Response;
  try {
    upstream = await fetch(`${BACKEND_URL}/api/v1/generate-report`, {
      method: "POST",
      headers: { "content-type": contentType },
      body,
    });
  } catch (err) {
    return NextResponse.json(
      { detail: `Could not reach backend: ${String(err)}` },
      { status: 502 },
    );
  }

  if (!upstream.ok) {
    const text = await upstream.text();
    let detail = text;
    try {
      const json = JSON.parse(text) as { detail?: string };
      if (json.detail) detail = json.detail;
    } catch {
      /* plain text — keep as-is */
    }
    return NextResponse.json({ detail }, { status: upstream.status });
  }

  const pdf = await upstream.arrayBuffer();
  const disposition = upstream.headers.get("Content-Disposition");

  const headers = new Headers({ "Content-Type": "application/pdf" });
  if (disposition) headers.set("Content-Disposition", disposition);

  return new NextResponse(pdf, { headers, status: 200 });
}
