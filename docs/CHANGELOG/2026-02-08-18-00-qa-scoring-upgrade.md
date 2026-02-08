# QA Scoring Upgrade: Full Rubric, Score All, Transcript Viewer, Monthly Chart

**Date**: 2026-02-08 18:00:00

## Summary

Major upgrade to QA scoring: full evaluation rubric with Interaction QA + Case QA, batch scoring, transcript viewer with chat bubbles, and monthly score timeline on dashboard.

## Changes

- Modified: `backend/agents/qa_scoring.py` — replaced simple 6-category rubric with full QA_Evaluation_Prompt (Interaction QA 10 params, Case QA 10 params, Red Flags, Business Intelligence, summaries, recommendation)
- Modified: `backend/api/v1/qa.py` — added POST /score-all (concurrent batch scoring), GET /detail/{id} returns full JSON + transcript, updated score endpoint to pass all ticket fields
- Modified: `backend/api/v1/schemas/qa.py` — added QADetailResponse, ScoreAllResponse schemas
- Modified: `backend/api/v1/schemas/dashboard.py` — added QAMonthlyScore for timeline data
- Modified: `backend/api/v1/dashboard.py` — added monthly avg QA score query grouped by conversation_end month
- Modified: `frontend/web/src/app/qa/page.tsx` — Score All button with batch progress, collapsible Interaction QA/Case QA sections, red flags checklist, summaries, transcript viewer modal with chat bubbles
- Modified: `frontend/web/src/app/dashboard/page.tsx` — recharts AreaChart showing avg QA score over time by month
- Modified: `frontend/web/src/lib/api.ts` — updated types for QADetailResponse, ScoreAllResponse, monthly_scores

## Affected Components

- `backend/agents/` - Full QA evaluation rubric with tracking items library
- `backend/api/v1/` - Score-all endpoint, detail with transcript, monthly metrics
- `frontend/web/` - QA page overhaul, dashboard timeline chart
