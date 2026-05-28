# Minutely — Tech Stack Skills Reference

## FastAPI
- Always use async def for route handlers
- Use APIRouter for route grouping; mount at /api/v1
- Lifespan context manager for startup/shutdown (NOT deprecated @app.on_event)
- HTTPException with correct status: 400 bad input, 413 too large, 422 validation, 500 server
- UploadFile + File(...) for multipart uploads; read via await file.read()
- Pydantic v2 models for ALL request/response schemas
- CORS middleware required for frontend communication
- StreamingResponse for returning PDF bytes (media_type application/pdf)
- Never use sync blocking I/O inside async endpoints
- Validate file size: len(await file.read()) before processing
- Always reset file pointer if reading twice: await file.seek(0)
- Use Depends() for shared dependencies like settings

## Anthropic SDK (Python) — CRITICAL PATTERNS
- Use AsyncAnthropic client, initialize ONCE as module singleton
- Model: claude-sonnet-4-6 (200K context window, GA with extended support)
- tool_use for structured output — NEVER ask for raw JSON in prose
- Tool definition: name, description, input_schema (JSON schema matching Pydantic)
- Force tool use: tool_choice={"type": "tool", "name": "generate_report"}
- Extract result: loop response.content, find block.type == "tool_use", use block.input
- Prompt caching: cache_control={"type": "ephemeral"} on system + context blocks
- System must be a LIST of content blocks when using cache_control:
  system=[{"type": "text", "text": "...", "cache_control": {"type": "ephemeral"}}]
- max_tokens: 4096 for report extraction
- Log response.usage: input_tokens, output_tokens, cache_creation_input_tokens, cache_read_input_tokens
- Catch: anthropic.APIError, anthropic.RateLimitError, anthropic.APIStatusError
- Retry on RateLimitError with exponential backoff (max 3 retries)

## ReportLab PDF
- SimpleDocTemplate with A4 pagesize, margins in mm
- Platypus flowables: Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak, KeepTogether
- ParagraphStyle for text; never use raw canvas.drawString for body text (no word wrap)
- Custom Flowable subclass ONLY for diagrams/visual bars (override draw + wrap)
- Colors: colors.HexColor("#6366F1")
- Units: from reportlab.lib.units import mm
- Tables: always set TableStyle with GRID, ROWBACKGROUNDS, VALIGN, padding
- Long cell text: wrap in Paragraph, not bare string
- generate_pdf must return bytes via BytesIO buffer, not write to disk:
  buf = BytesIO(); doc = SimpleDocTemplate(buf, ...); doc.build(story); return buf.getvalue()
- Status/priority badges: small colored Table cells or styled Paragraphs
- Avatar initials: colored circle via custom Flowable or styled table cell

## File Parsers
- All parsers return: tuple[str, list[str]] → (raw_text, unique_speakers)
- CSV: csv.DictReader on io.StringIO(content.decode("utf-8-sig"))
  Detect columns case-insensitively: speaker/name/participant, text/transcript/content/message, timestamp/time/start
  Skip empty rows; format as "Speaker: text" lines
- TXT: decode utf-8-sig; regex r"^([A-Z][\w\s]+):\s*(.+)$" for speaker turns
  Fallback: treat whole file as plain text, speakers = []
- PDF: pypdf PdfReader(io.BytesIO(content)); loop pages; page.extract_text(); join "\n"
- DOCX: python-docx Document(io.BytesIO(content)); loop doc.paragraphs; p.text
- MD: decode text; strip via regex: headers (^#+\s), bold (\*\*), italic (\*), code (`)
- Validate extension BEFORE parsing; raise HTTPException(400) if unsupported
- Handle decode errors gracefully with try/except → HTTPException(400, "Cannot read file")

## Next.js 14 + Tailwind
- App Router only — all in src/app/; no pages/ directory
- Server components default; "use client" ONLY for interactivity (uploads, state, animation)
- fetch() for API — no axios
- FormData for file uploads: formData.append("transcript", file)
- Response as blob: const blob = await res.blob() for PDF download
- Download trigger: URL.createObjectURL(blob) + temporary <a> click
- Dark theme: bg-zinc-950, text-zinc-100, accents indigo-500/teal-500/amber-500
- Tailwind utilities only; no CSS modules, no styled-components
- cn() helper for conditional classes (clsx + tailwind-merge)
- Responsive: stack columns on mobile (flex-col md:flex-row)
- NEVER use localStorage/sessionStorage if deploying as artifact — but this is a real Next app, so localStorage IS fine here for caching context files later

## Framer Motion
- motion.div, motion.button for animated elements
- AnimatePresence wraps conditionally-rendered elements (mode="wait")
- variants pattern for staggered lists: container + item variants
- initial/animate/exit props; transition with type spring or easeOut
- whileHover={{ scale: 1.02 }}, whileTap={{ scale: 0.98 }} for buttons
- Keep subtle: opacity + y-translate, avoid layout/scale-heavy animations
- Stagger: transition={{ staggerChildren: 0.1 }} on container
- Processing steps: sequential fade-in with delay per index

## Docker
- Backend base: python:3.11-slim
- Frontend base: node:20-alpine
- Multi-stage for frontend: builder (npm ci + build) → runner (standalone)
- Next standalone: set output: "standalone" in next.config.ts
- COPY requirements.txt / package.json FIRST → install → THEN copy code (layer caching)
- Non-root user: RUN useradd appuser; USER appuser
- Use $PORT env var (Railway injects): --port $PORT, or PORT for next
- EXPOSE 8000 (backend), 3000 (frontend)
- .dockerignore: node_modules, __pycache__, .env, .git, *.pdf

## Railway
- railway.toml: [[services]] blocks, each with name + source subdirectory
- Health check: GET /health returning {"status": "ok"} — Railway uses for readiness
- PORT injected by Railway — never hardcode; use $PORT
- Service-to-service: use RAILWAY_PRIVATE_DOMAIN for internal calls
- Frontend NEXT_PUBLIC_API_URL points to backend's public Railway URL
- Set env vars in Railway dashboard, not in committed files
- Stateless — no volumes needed

## Verification / QA Standards (for verifier agent)
- Python: every file must import without error (python -c "import module")
- Python: no undefined names, no missing imports, type hints present
- FastAPI: app must start (uvicorn app.main:app --reload boots clean)
- Pydantic: all models instantiate; tool schema matches MeetingReport exactly
- Frontend: npm run build completes with zero TypeScript errors
- Frontend: no unused imports, no any types in critical paths
- Integration: /health returns 200; /generate-report accepts 3 files
- Every file referenced in CLAUDE.md folder structure exists and is non-empty
- No placeholder comments ("# TODO", "# add logic", "pass  # implement")
- All env vars referenced exist in .env.example