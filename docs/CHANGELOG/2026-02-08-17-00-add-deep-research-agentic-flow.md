# Add Deep Research Agentic Flow

**Date**: 2026-02-08 17:00:00

## Summary

Add a new `/research` endpoint with an agentic deep research flow that decomposes complex queries, runs parallel searches across multiple pools, and synthesizes structured reports with evidence attribution.

## Changes

- Added: `DeepResearchAgent` in `backend/agents/deep_research.py` — routes complexity, decomposes queries, runs parallel hybrid searches, synthesizes reports via GPT-4o
- Added: `POST /api/v1/copilot/research` endpoint for deep research
- Added: `GET /api/v1/copilot/evaluate-research` endpoint for evaluating the research agent
- Added: Research schemas (`CopilotResearchRequest`, `ResearchReport`, `EvidenceItem`, `RelatedResource`, `SubQueryInfo`, `CopilotResearchResponse`)
- Added: Frontend mode toggle (Quick Search / Deep Research) on the copilot page
- Added: `ResearchReportView` component rendering summary, evidence cards, related resources, and sub-query decomposition
- Added: `copilotResearch()` API method in frontend
- Added: `--mode` flag to evaluation script (`ask` or `research`)
- Modified: Extracted `_build_search_results()` helper in copilot endpoint to share between `/ask` and `/research`
- Modified: Makefile `evaluate` target now supports `EVAL_MODE` variable

## Affected Components

- `backend/agents/deep_research.py` - New DeepResearchAgent with routing, decomposition, parallel search, synthesis
- `backend/api/v1/copilot.py` - New `/research` and `/evaluate-research` endpoints, shared helper extraction
- `backend/api/v1/schemas/copilot.py` - New research-related Pydantic schemas
- `backend/api/core/constants.py` - Deep research constants (max sub-queries, results per query, max context)
- `frontend/web/src/lib/api.ts` - Research TypeScript interfaces and API method
- `frontend/web/src/components/copilot/search-bar.tsx` - Mode toggle (Quick Search / Deep Research)
- `frontend/web/src/components/copilot/research-report.tsx` - Research report renderer
- `frontend/web/src/app/copilot/page.tsx` - Mode state wiring and conditional rendering
- `backend/scripts/evaluate.py` - `--mode` flag support
- `Makefile` - `EVAL_MODE` passthrough
