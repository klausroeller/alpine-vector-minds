# Improve research mode retrieval: add baseline search + rerank

**Date**: 2026-02-08 12:43:00

## Summary

Research mode now runs the same baseline search as ask mode (classify → embed → primary + secondary pool search) alongside decomposed sub-query searches, then reranks the merged result set with LLM.

## Changes

- Modified: `_parallel_search()` now accepts a `classification` dict and runs a baseline search (primary + secondary pool) in parallel with sub-query searches
- Modified: `run()` RESEARCH path now runs `_classify` and `_decompose` in parallel instead of sequentially
- Added: LLM reranking step on merged candidates before synthesis and result selection
- Added: Import of `_secondary_pool` from triage, `ENABLE_RERANKING` and `SEARCH_RESULT_LIMIT` from constants

## Affected Components

- `backend/agents/deep_research.py` - Add baseline search to parallel search, rerank merged results, parallelize classify+decompose
