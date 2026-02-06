# Fix CI Workflow

**Date**: 2026-02-06 20:54:00

## Summary

Fix GitHub Actions CI failures and remove broken deploy workflow.

## Changes

- Removed: `.github/workflows/deploy.yml` — placeholder ECR-based deploy with unconfigured AWS secrets
- Fixed: pnpm version conflict by removing explicit `version: 9` from action (auto-detects from `packageManager` in root package.json)
- Fixed: pnpm lockfile cache path from `frontend/web/pnpm-lock.yaml` to `frontend/pnpm-lock.yaml`
- Fixed: pnpm install now runs from workspace root (`frontend/`) where lockfile lives
- Added: mypy overrides in `pyproject.toml` to ignore missing imports for `jose` and `passlib`

## Affected Components

- `.github/workflows/` — Removed deploy.yml, fixed ci.yml
- `backend/pyproject.toml` — Added mypy overrides for third-party libs without type stubs
