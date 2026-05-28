# Meeting Intelligence — Project Context

## What This Is
Internal tool: 3 docs in (my context .MD + client context .MD + transcript) → single Claude API call → PDF report out.

## Core Decisions (Do Not Second-Guess)
- NO RAG, NO vector DB, NO chunking
- Claude Sonnet 4.6 with 1M context window — all 3 docs go in directly
- NO database, NO auth — internal tool, stateless pipeline
- tool_use for structured JSON output (not raw JSON prompting)
- Prompt caching on system prompt + client context blocks

## Stack
- Backend: FastAPI (Python)
- Frontend: Next.js + Tailwind
- PDF: ReportLab
- Parsers: pypdf + python-docx + csv (stdlib)
- Hosting: Railway (2 services)
- LLM: claude-sonnet-4-6

## Folder Structure
backend/  → FastAPI app
frontend/ → Next.js app

## Environment Variables Needed
ANTHROPIC_API_KEY
NEXT_PUBLIC_API_URL

## Coding Rules
- Async everywhere in FastAPI
- Pydantic models for all request/response schemas
- Proper HTTP status codes
- No placeholder logic
- Type hints everywhere
- Structured error responses