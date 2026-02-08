# Fix research mode: add classification + ranked results

**Date**: 2026-02-08 11:54:00

## Summary

Research mode now returns classification and top-10 ranked results (same as ask mode), fixing broken evaluation scores.

## Changes

- Fixed: DeepResearchAgent RESEARCH path now calls `_classify()` and includes classification + top-10 merged results in the response
- Fixed: Research endpoint extracts classification and builds SearchResult objects for the research-mode branch
- Fixed: evaluate-research endpoint uses unified classification + results instead of hardcoded "RESEARCH" type
- Modified: Frontend copilot page shows right-column result cards + classification badge for all research responses (not just simple fallback)

## Affected Components

- `backend/agents/deep_research.py` — Added classification + merged_results[:10] to RESEARCH response; runs classify and synthesize in parallel
- `backend/api/v1/copilot.py` — Research branch now builds Classification + SearchResult objects; evaluate-research simplified to unified path
- `frontend/web/src/app/copilot/page.tsx` — Removed `researchSimple` guard from right-column and no-results display
