# Fix DB Connection Pool Exhaustion in Evaluation Script

**Date**: 2026-02-08 16:00:00

## Summary

Cap concurrent evaluation requests with a semaphore to prevent database connection pool exhaustion.

## Changes

- Added: `MAX_CONCURRENT_REQUESTS = 5` constant to limit concurrency
- Modified: `_fetch_one` raises `RuntimeError` instead of calling `sys.exit(1)` to avoid asyncio "Task exception was never retrieved" noise
- Modified: `run_evaluation` uses `asyncio.Semaphore` to cap in-flight requests, with try/except around `asyncio.gather` for clean error handling

## Affected Components

- `backend/scripts/evaluate.py` - Concurrency limiting and error handling fixes
