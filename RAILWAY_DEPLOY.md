# Railway Deployment Guide — Minutely

## Services to Create in Railway Dashboard

| Service  | Root Dir   | Type        |
|----------|------------|-------------|
| backend  | /backend   | Web Service |
| frontend | /frontend  | Web Service |

## Backend Environment Variables

Set these in Railway Dashboard → backend service → Variables:

| Variable | Value | Required |
|---|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-...` | **YES** |
| `CLAUDE_MODEL` | `claude-sonnet-4-6` | Yes |
| `MAX_FILE_SIZE_MB` | `25` | Yes |
| `ALLOWED_ORIGINS` | `https://your-frontend.up.railway.app` | **YES** |
| `ENVIRONMENT` | `production` | Yes |

## Frontend Environment Variables

Set these in Railway Dashboard → frontend service → Variables:

| Variable | Value | Required |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://your-backend.up.railway.app` | **YES** |

> ⚠️ `NEXT_PUBLIC_API_URL` is baked into the Next.js bundle at build time.
> After setting it, trigger a redeploy of the frontend service.

## Deployment Steps

### Option A — Railway CLI (Recommended)

```bash
npm install -g @railway/cli
railway login
railway link        # select your project

# Deploy backend
cd backend
railway up --service backend

# Deploy frontend
cd ../frontend
railway up --service frontend
```

### Option B — Railway Dashboard (GitHub)

1. Create a new service → GitHub Repo → select `Minutely`
2. In the service **Settings → Source → Root Directory**, set `backend`
3. Redeploy — Railway reads `backend/railway.toml` and uses the Dockerfile
4. Repeat for frontend with Root Directory = `frontend`

## Health Checks

| Service  | Path     | Expected response |
|----------|----------|-------------------|
| backend  | `/health` | `{"status":"ok","service":"minutely-backend"}` |
| frontend | `/`       | HTTP 200 |

## Notes

- This is a **stateless pipeline** — no database, no Redis, no persistent storage needed
- Each request processes documents in-memory and streams the PDF back
- Both services scale horizontally without shared state
- Prompt caching on Anthropic API reduces costs on repeated requests for the same client
