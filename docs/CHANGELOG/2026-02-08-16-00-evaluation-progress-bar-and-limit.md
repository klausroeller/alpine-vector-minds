# Add progress bar and limit parameter to evaluation

**Date**: 2026-02-08 16:00:00

## Summary

Replace bulk evaluation endpoint with per-question endpoint; add client-side progress bar and `--limit` parameter.

## Changes

- Modified: `backend/api/v1/copilot.py` — endpoint now accepts `index` query param and evaluates a single question per request
- Added: `backend/api/v1/schemas/copilot.py` — new `EvaluationStepResponse` schema for per-question results
- Modified: `backend/scripts/evaluate.py` — client-side loop with `\r`-based progress bar, `--limit` arg (default 100), client-side aggregation
- Modified: `Makefile` — forward `EVAL_LIMIT` to the evaluate script

## Affected Components

- `backend/api/v1/` — Evaluation endpoint changed from bulk to per-question
- `backend/scripts/` — Evaluate script rewritten with progress bar and limit support
- `Makefile` — New `EVAL_LIMIT` parameter for evaluate target
