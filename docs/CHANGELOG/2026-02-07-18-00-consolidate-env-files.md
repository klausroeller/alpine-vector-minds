# Consolidate env files to root

**Date**: 2026-02-07 18:00:00

## Summary

Consolidate all environment configuration to root `.env` with proper local dev defaults, and make Docker Compose files use variable interpolation.

## Changes

- Modified: `.env` — rewritten with local dev values (was duplicating production config)
- Modified: `.env.example` — aligned variable names with compose files (`POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB` instead of `DATABASE_URL`)
- Modified: `docker-compose.yml` — replaced hardcoded values with `${VAR:-default}` interpolation, added `OPENAI_API_KEY` passthrough and `NEXT_PUBLIC_API_URL` build arg
- Modified: `frontend/web/Dockerfile` — added `ARG NEXT_PUBLIC_API_URL` in builder stage so `next build` bakes in the API URL
- Removed: `frontend/web/.env.local` — no longer needed, root `.env` provides all values

## Affected Components

- `docker-compose.yml` — uses variable interpolation from root `.env`
- `frontend/web/Dockerfile` — accepts `NEXT_PUBLIC_API_URL` build arg
- `.env` / `.env.example` — consistent local dev defaults
