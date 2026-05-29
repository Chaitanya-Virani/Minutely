import { NextResponse } from "next/server";

const BACKEND_URL = (
  process.env.BACKEND_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

export async function GET() {
  let upstream: Response;
  try {
    upstream = await fetch(`${BACKEND_URL}/api/v1/config`, { method: "GET" });
  } catch (err) {
    return NextResponse.json(
      { detail: `Could not reach backend: ${String(err)}` },
      { status: 502 },
    );
  }

  const text = await upstream.text();
  if (!upstream.ok) {
    let detail = text;
    try {
      const json = JSON.parse(text) as { detail?: string };
      if (json.detail) detail = json.detail;
    } catch {
      /* plain text — keep as-is */
    }
    return NextResponse.json({ detail }, { status: upstream.status });
  }

  try {
    const json = JSON.parse(text) as unknown;
    return NextResponse.json(json, { status: 200 });
  } catch {
    return NextResponse.json(
      { detail: "Backend returned a non-JSON config response." },
      { status: 502 },
    );
  }
}
