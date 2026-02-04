# Restructure Monorepo

**Date**: 2026-02-03 18:06:00

## Summary

Flatten the monorepo hierarchy, improve naming, co-locate Dockerfiles, and add Makefile.

## Changes

- Moved: `apps/api/` to `api/`
- Moved: `apps/web/` to `frontend/web/`
- Moved: `packages/` to `frontend/packages/`
- Moved: `services/search/` to `vector-db/`
- Moved: `services/agents/` to `agents/`
- Moved: `docker/Dockerfile.api` to `api/Dockerfile`
- Moved: `docker/Dockerfile.web` to `frontend/web/Dockerfile`
- Removed: `apps/`, `services/`, and `docker/` directories
- Added: `frontend/pnpm-workspace.yaml` for frontend workspace
- Added: `frontend/package.json` for frontend workspace scripts
- Added: `Makefile` with common development commands
- Modified: `pnpm-workspace.yaml` with new workspace paths
- Modified: `package.json` with updated script paths
- Modified: `docker-compose.yml` with new build contexts and volumes
- Modified: `.github/workflows/ci.yml` with new paths
- Modified: `.github/workflows/deploy.yml` with new Docker build paths
- Modified: `api/Dockerfile` with co-located COPY paths
- Modified: `frontend/web/Dockerfile` with co-located COPY paths
- Modified: `README.md` with new project structure and commands
- Modified: `CLAUDE.md` simplified to reference README.md

## Affected Components

- `api/` - Relocated from `apps/api/`, Dockerfile co-located
- `frontend/web/` - Relocated from `apps/web/`, Dockerfile co-located
- `frontend/packages/` - Relocated from `packages/`
- `vector-db/` - Relocated from `services/search/`
- `agents/` - Relocated from `services/agents/`
- `.github/workflows/` - Updated all path references
- Root config files - Updated workspace and script paths
