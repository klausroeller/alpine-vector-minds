# Refactor Evaluation: Endpoint Reuses copilot_ask, Script Adds Concurrency

**Date**: 2026-02-08 15:00:00

## Summary

Eliminate duplicated pipeline logic in `/evaluate` endpoint and add concurrent batch execution to the evaluation script.

## Changes

- Modified: `backend/api/v1/copilot.py` — `/evaluate` endpoint now calls `copilot_ask` internally instead of manually instantiating EmbeddingService, VectorSearchService, and TriageAgent
- Modified: `backend/scripts/evaluate.py` — switched from sync `httpx.Client` to async `httpx.AsyncClient` with batched concurrent requests via `asyncio.gather`; batch size is `max(1, total // 10)` for ~10 progress bar updates

## Affected Components

- `backend/api/v1/copilot.py` — Removed duplicated agent pipeline in evaluate endpoint
- `backend/scripts/evaluate.py` — Async concurrency for faster evaluation runs
