# Dashboard: System Accuracy by Difficulty

**Date**: 2026-02-08 16:30:00

## Summary

Show evaluation results broken down by question difficulty (Easy, Medium, Hard) on the dashboard.

## Changes

- Modified: `EvaluationMetrics` schema to include `by_difficulty` field with per-level metrics
- Modified: Dashboard API to parse `by_difficulty_json` from the latest evaluation run
- Modified: Dashboard frontend to render three color-coded difficulty cards (Easy/Medium/Hard) with Classification, Hit@1, and Hit@5 progress bars

## Affected Components

- `backend/api/v1/schemas/dashboard.py` - Added `DifficultyMetrics` model and `by_difficulty` field
- `backend/api/v1/dashboard.py` - Parse and return difficulty breakdown from evaluation run
- `frontend/web/src/lib/api.ts` - Added `by_difficulty` to evaluation TypeScript type
- `frontend/web/src/app/dashboard/page.tsx` - Render difficulty breakdown cards in System Accuracy section
