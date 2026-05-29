# Minutely

**AI-powered meeting intelligence — three documents in, one polished PDF report out.**

Minutely is a stateless web tool that turns a raw meeting transcript and two context documents into a comprehensive, structured PDF meeting report. It sends all three inputs to Claude in a single API call and returns a professionally formatted PDF covering action items, decisions, risks, key dates, and per-participant summaries — all written from your first-person perspective.

---

## How It Works

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  My Context   │   │Client Context│   │  Transcript   │
│    (.md)      │   │    (.md)     │   │ .csv .txt .pdf│
│               │   │              │   │  .docx .md    │
└──────┬───────┘   └──────┬───────┘   └──────┬────────┘
       │                  │                   │
       └──────────┬───────┘───────────────────┘
                  ▼
        ┌─────────────────┐
        │   FastAPI        │  Parse → single Claude API call → PDF render
        │   Backend        │
        └────────┬────────┘
                 ▼
        ┌─────────────────┐
        │   PDF Report     │  Action items, decisions, risks, dates,
        │   (download)     │  participant summaries, follow-ups
        └─────────────────┘
```

### The Three Inputs

| Input | Format | Purpose |
|---|---|---|
| **My Context** | `.md` | Your background, goals, and what to listen for — the report is written from *your* first-person perspective |
| **Client Context** | `.md` | Info about the client/counterparty — names, project codenames, org relationships |
| **Transcript** | `.csv`, `.txt`, `.pdf`, `.docx`, `.md` | Raw meeting transcript export from any call tool |

### What the PDF Contains

- **Executive Summary** — first-person recap of what you came away with
- **Outcomes** — every decision, tagged as `decided` / `pending` / `tabled`
- **Action Items** — tasks with assignees, due dates, and priority levels
- **Key Dates** — deadlines, milestones, scheduled meetings
- **Discussion Points** — clustered topics with participants and resolutions
- **Per-Participant Summary** — role, contributions, and assigned tasks for each speaker
- **Risks & Blockers** — unresolved concerns and dependencies
- **Follow-Up Meetings** — proposed or scheduled syncs

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python · FastAPI · Uvicorn |
| Frontend | Next.js 14 · React 18 · TypeScript · Tailwind CSS |
| LLM | Claude Sonnet (Anthropic) via `tool_use` for structured output |
| PDF Generation | ReportLab (in-memory, no disk writes) |
| File Parsers | pypdf · python-docx · csv (stdlib) |
| Deployment | Railway (2 services) · Docker |

---

## Project Structure

```
Minutely/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point, CORS, error handling
│   │   ├── config.py            # Pydantic settings from env vars
│   │   ├── api/
│   │   │   └── routes.py        # POST /generate-report endpoint
│   │   ├── parsers/             # File parsers (csv, txt, pdf, docx, md)
│   │   │   └── router.py        # Dispatcher by file extension
│   │   └── report/
│   │       ├── extractor.py     # Claude API call with retry logic
│   │       ├── prompt_builder.py# System + user prompt construction
│   │       ├── schemas.py       # Pydantic models for the report structure
│   │       ├── tool_schema.py   # Claude tool_use definition
│   │       └── pdf_builder.py   # ReportLab PDF renderer (~800 lines)
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js app router (single page)
│   │   ├── components/          # ThreeDocUploader, UploadZone, ProcessingSteps, etc.
│   │   ├── lib/                 # API client
│   │   └── types/
│   ├── Dockerfile
│   └── package.json
├── demo/                        # Sample input files for testing
├── docker-compose.yml
└── RAILWAY_DEPLOY.md
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com/)

### 1. Clone & configure

```bash
git clone https://github.com/Chaitanya-Virani/Minutely.git
cd Minutely
cp .env.example .env
# Fill in your ANTHROPIC_API_KEY in .env
```

### 2. Backend

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env    # set ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
# Ensure NEXT_PUBLIC_API_URL=http://localhost:8000 in .env.local
npm run dev
```

The app will be running at `http://localhost:3000`.

### Docker (alternative)

```bash
docker compose up --build
```

Backend on `:8000`, frontend on `:3000`.

---

## API

### `POST /api/v1/generate-report`

Multipart form upload with three file fields:

| Field | Type | Accepted |
|---|---|---|
| `my_context` | file | `.md` |
| `client_context` | file | `.md` |
| `transcript` | file | `.csv`, `.txt`, `.pdf`, `.docx`, `.md` |

**Returns:** `application/pdf` streamed as an attachment.

### `GET /health`

Returns `{"status": "ok"}` — used by Railway for health checks.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | **Required.** Your Anthropic API key |
| `CLAUDE_MODEL` | `claude-sonnet-4-6` | Model ID for report generation |
| `MAX_FILE_SIZE_MB` | `25` | Max upload size per file |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |
| `PORT` | `8000` | Backend server port |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend URL (baked into Next.js at build time) |

---

## Deployment

See [RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md) for full Railway deployment instructions. Both services are stateless and scale horizontally — no database or persistent storage required.

---

## Architecture Decisions

- **No RAG / no vector DB** — Claude's 1M-token context window fits all three documents in a single call, so chunking and retrieval add complexity without benefit.
- **No database / no auth** — this is a stateless pipeline; documents are processed in-memory and never persisted.
- **`tool_use` for structured output** — Claude is forced to call a `generate_report` tool with a strict JSON schema, which Pydantic validates into typed models. No fragile JSON parsing.
- **Prompt caching** — the system prompt and client context blocks are marked `ephemeral` so repeated calls for the same client reuse cached tokens, reducing cost and latency.
- **In-memory PDF** — ReportLab renders the PDF to a `BytesIO` buffer and streams it directly back to the caller. Nothing ever hits disk.

---

## License

This project is for internal / personal use.