# Add Production Database Seeding

**Date**: 2026-02-07 23:22:00

## Summary

Unify database seeding to run inside Docker containers for both dev and production environments.

## Changes

- Modified: `backend/Dockerfile` — include seed scripts in the image (`COPY scripts ./scripts`)
- Modified: `docker-compose.yml` — add scripts and data volume mounts to api service
- Modified: `docker-compose.prod.yml` — add `OPENAI_API_KEY` env var and data volume mount to api service
- Modified: `Makefile` — change `seed`/sub-targets to use `docker exec`, add `seed-production` target
- Added: `scripts/seed-production.sh` — standalone remote seeding script for deployed instances
- Modified: `scripts/setup-production.sh` — add Step 8 (database seeding after admin creation)

## Affected Components

- `backend/Dockerfile` — Seed scripts now included in container image
- `docker-compose.yml` — Dev api service gets scripts + data volume mounts
- `docker-compose.prod.yml` — Prod api service gets OPENAI_API_KEY + data mount
- `Makefile` — `make seed` runs via `docker exec`; new `make seed-production` target
- `scripts/seed-production.sh` — New script for remote seeding
- `scripts/setup-production.sh` — Full setup now includes seeding before "Done"
