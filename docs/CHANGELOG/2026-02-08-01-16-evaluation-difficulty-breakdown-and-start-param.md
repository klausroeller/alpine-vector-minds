# Evaluation: Difficulty Breakdown + EVAL_START Parameter

**Date**: 2026-02-08 01:16:00

## Summary

Add difficulty-level breakdown to evaluation reports and an EVAL_START parameter to resume evaluations from a specific question index.

## Changes

- Added: `difficulty` field to `EvaluationStepResponse` API schema
- Added: `--start` CLI argument to `evaluate.py` for starting evaluation at a given 0-based index
- Added: `by_difficulty` aggregation in evaluation reports (JSON and markdown) with Count, Classification, Hit@1, Hit@3 per difficulty level
- Modified: `copilot_evaluate()` endpoint to return `difficulty` from the Question model
- Modified: Makefile `evaluate` target to support `EVAL_START` parameter

## Affected Components

- `backend/api/v1/schemas/copilot.py` - Added `difficulty` field to `EvaluationStepResponse`
- `backend/api/v1/copilot.py` - Include `difficulty` in evaluation response
- `backend/scripts/evaluate.py` - `--start` arg, difficulty aggregation, markdown section
- `Makefile` - `EVAL_START` parameter for evaluate target
