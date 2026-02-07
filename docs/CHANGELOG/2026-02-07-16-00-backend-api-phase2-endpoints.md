# Add Phase 2 Backend API endpoints

**Date**: 2026-02-07 16:00:00

## Summary

Implement CRUD endpoints for knowledge base, learning feed, dashboard metrics, plus stubs for copilot and gap detection.

## Changes

- Added: `api/v1/schemas/` directory with Pydantic schemas for copilot, knowledge, learning, dashboard
- Added: `api/core/constants.py` with shared constants (thresholds, pagination defaults)
- Added: `GET /api/v1/knowledge/` — list KB articles with search, filters, pagination
- Added: `GET /api/v1/knowledge/{id}` — article detail with lineage provenance
- Added: `GET /api/v1/learning/events` — list learning events with status filter
- Added: `POST /api/v1/learning/review/{id}` — approve/reject learning events
- Added: `POST /api/v1/learning/detect-gap` — stub (Phase 3: AI agents)
- Added: `GET /api/v1/dashboard/metrics` — aggregate metrics for KB, learning, tickets, scripts
- Added: `POST /api/v1/copilot/ask` — stub (Phase 3: TriageAgent)
- Added: `GET /api/v1/copilot/evaluate` — stub (Phase 3: evaluation pipeline)
- Modified: `api/v1/__init__.py` — registered copilot, knowledge, learning, dashboard routers
- Modified: `api/core/config.py` — added SupportMind AI settings (already present from prior work)

## Affected Components

- `backend/api/v1/` — New route modules and schema directory
- `backend/api/core/` — New constants file
