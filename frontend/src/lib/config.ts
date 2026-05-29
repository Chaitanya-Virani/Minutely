/**
 * Generation configuration fetched from the backend via the Next proxy.
 *
 * GETs /api/config (the server-side proxy — never the backend directly), which
 * forwards to ${BACKEND_URL}/api/v1/config. Keeps BACKEND_URL out of the
 * browser bundle. Shapes mirror the frozen contract verbatim.
 */

export interface ModelOption {
  id: string;
  label: string;
  description: string;
}

export interface GenerationConfig {
  models: ModelOption[];
  default_model: string;
  default_system_prompt: string;
}

export async function fetchGenerationConfig(): Promise<GenerationConfig> {
  const response = await fetch(`/api/config`, { method: "GET" });

  if (!response.ok) {
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
      `Failed to load generation config (${response.status} ${response.statusText})${
        trimmed.length > 0 ? `: ${trimmed}` : ""
      }`,
    );
  }

  const config = (await response.json()) as GenerationConfig;
  return config;
}
