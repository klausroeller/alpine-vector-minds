# QA Scoring Agent, Evaluation Dashboard, Copilot Feedback

**Date**: 2026-02-08 16:00:00

## Summary

Add QA scoring agent with 6-category rubric, evaluation metrics in dashboard, and copilot feedback buttons.

## Changes

- Added: `QAScoringAgent` — scores conversations against a 6-category QA rubric (Greeting & Empathy, Issue Identification, Troubleshooting Quality, Resolution Accuracy, Documentation Quality, Compliance & Safety) with auto-zero red flags
- Added: `/qa` page — list scored conversations with expandable category breakdowns, color-coded scores, red flag badges
- Added: `POST /api/v1/qa/score/{id}` and `GET /api/v1/qa/scores` endpoints
- Added: QA columns on conversations table (`qa_score`, `qa_scores_json`, `qa_red_flags`, `qa_scored_at`)
- Added: `migrate-qa-columns` Makefile target and migration script
- Added: `EvaluationRun` model — stores `make evaluate` results (hit@1/5/10, classification accuracy) in the database
- Added: `POST /api/v1/evaluation/results` and `GET /api/v1/evaluation/latest` endpoints
- Modified: `evaluate.py` — auto-POSTs results to API after running (best-effort)
- Added: System Accuracy section on dashboard with progress bars for Classification Accuracy, Hit@1, Hit@5, Hit@10
- Added: `CopilotFeedback` model — stores thumbs-up/down feedback on copilot search results
- Added: `POST /api/v1/copilot/feedback` endpoint
- Added: Thumbs-up/down buttons on copilot result cards with color feedback
- Modified: Dashboard — shows QA quality metrics, system accuracy, and copilot feedback metrics when data exists
- Modified: Navigation — added QA Scores entry with ShieldCheck icon

## Affected Components

- `backend/agents/qa_scoring.py` — New QA scoring agent
- `backend/agents/__init__.py` — Register QAScoringAgent
- `backend/vector_db/models/conversation.py` — QA score columns
- `backend/vector_db/models/evaluation_run.py` — New model
- `backend/vector_db/models/copilot_feedback.py` — New model
- `backend/vector_db/models/__init__.py` — Register new models
- `backend/api/v1/qa.py` — QA scoring endpoints
- `backend/api/v1/evaluation.py` — Evaluation results endpoints
- `backend/api/v1/copilot.py` — Feedback endpoint
- `backend/api/v1/dashboard.py` — QA, evaluation, feedback metrics
- `backend/api/v1/schemas/dashboard.py` — New metric schemas
- `backend/api/v1/schemas/qa.py` — QA score schemas
- `backend/scripts/migrate_qa_columns.py` — Migration script
- `backend/scripts/evaluate.py` — Auto-store results
- `frontend/web/src/lib/api.ts` — New types and API methods
- `frontend/web/src/components/layout/app-layout.tsx` — QA nav entry
- `frontend/web/src/app/qa/page.tsx` — QA scores page
- `frontend/web/src/app/dashboard/page.tsx` — New metric sections
- `frontend/web/src/components/copilot/result-card.tsx` — Feedback buttons
- `frontend/web/src/app/copilot/page.tsx` — Feedback state management
- `Makefile` — migrate-qa-columns target
- `README.md` — Updated tables, endpoints, pages
