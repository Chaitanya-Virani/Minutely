# Dynamic Settings — FROZEN CONTRACT

> Both the backend track and the frontend track reference this file.
> **These field names and shapes do not change during implementation.**
> Last verified against Anthropic docs (platform.claude.com) on 2026-05-29.

## Interface A — `GET /api/v1/config` (read)

Backend exposes; frontend reads it through the Next proxy `GET /api/config`.

Response JSON:

```json
{
  "models": [
    { "id": "claude-opus-4-8",           "label": "Claude Opus 4.8",   "description": "Most capable. Best for complex reasoning and nuanced reports. Slowest, highest cost. 1M context." },
    { "id": "claude-sonnet-4-6",         "label": "Claude Sonnet 4.6", "description": "Balanced default. Strong quality with good speed. 1M context." },
    { "id": "claude-haiku-4-5-20251001", "label": "Claude Haiku 4.5",  "description": "Fastest and most economical. Great for quick drafts. 200k context." }
  ],
  "default_model": "claude-sonnet-4-6",
  "default_system_prompt": "<the SYSTEM_INSTRUCTIONS constant verbatim>"
}
```

- `models[].id` / `label` / `description` are all strings.
- `default_model` MUST be one of `models[].id` (it is `claude-sonnet-4-6`).
- `default_system_prompt` is the `SYSTEM_INSTRUCTIONS` constant from
  `backend/app/report/prompt_builder.py`, served verbatim.

## Verified model IDs (do not assume — these are confirmed)

| Label | API ID |
|-------|--------|
| Claude Opus 4.8 | `claude-opus-4-8` |
| Claude Sonnet 4.6 | `claude-sonnet-4-6` |
| Claude Haiku 4.5 | `claude-haiku-4-5-20251001` |

## Interface B — `POST /api/v1/generate-report` (write)

Existing multipart endpoint gains **two new form fields** alongside the three
existing file fields (`my_context`, `client_context`, `transcript`). The Next
proxy forwards the raw multipart body unchanged, so no proxy change is needed.

| Field name (FROZEN) | Type | Empty behaviour | Invalid behaviour |
|---------------------|------|-----------------|-------------------|
| `model`             | str (form) | empty/omitted → server default (`claude-sonnet-4-6`) | not in allow-list → **HTTP 400**, extractor never called |
| `system_prompt`     | str (form) | empty/whitespace → server default `SYSTEM_INSTRUCTIONS`, silently | n/a |

- Frontend `FormData` keys: exactly `"model"` and `"system_prompt"` (underscore).
- Backend `Form(...)` params: exactly `model` and `system_prompt` (underscore).

## localStorage (frontend only)

- Key: `"minutely.systemPrompt"`.
- Read only inside `useEffect` (never during render — SSR hydration safety).
- On generate: custom prompt (≠ server default, non-empty) → `setItem`;
  prompt equals server default OR empty → `removeItem`.
- Model selection is **not** persisted — resets to `default_model` each load.
