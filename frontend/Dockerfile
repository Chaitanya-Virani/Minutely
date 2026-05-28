# syntax=docker/dockerfile:1.7
# Minutely frontend image — Next.js 14 standalone output on Node 20 Alpine.
# Multi-stage build:
#   1. deps    — install npm dependencies once (cacheable on package*.json hash)
#   2. builder — compile the app and produce `.next/standalone`
#   3. runner  — minimal runtime image with only the standalone bundle + assets

# ---------- Stage 1: deps ----------
FROM node:20-alpine AS deps
WORKDIR /app
# libc6-compat is required by some Next.js native deps on Alpine.
RUN apk add --no-cache libc6-compat
COPY package.json package-lock.json* npm-shrinkwrap.json* ./
# Prefer reproducible installs via lockfile when available, fall back otherwise.
RUN if [ -f package-lock.json ] || [ -f npm-shrinkwrap.json ]; then \
        npm ci; \
    else \
        npm install --no-audit --no-fund; \
    fi

# ---------- Stage 2: builder ----------
FROM node:20-alpine AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Ensure a public/ directory always exists so the runner COPY never fails,
# even when the source tree omits it.
RUN mkdir -p public
RUN npm run build

# ---------- Stage 3: runner ----------
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

# Non-root runtime user.
RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

# Static assets and the standalone server bundle.
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

# Next.js standalone entry point. PORT is read from the environment by the
# generated server.js (set above; Railway overrides at runtime).
CMD ["node", "server.js"]
