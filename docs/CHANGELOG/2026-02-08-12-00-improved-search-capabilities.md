# Improved Search Capabilities

**Date**: 2026-02-08 12:00:00

## Summary

Major search quality improvements: ticket embeddings, hybrid search (semantic + FTS with RRF), LLM query rewriting, classification few-shots, and LLM reranking.

## Changes

- Added: Embedding column to Ticket model with IVFFlat vector index
- Added: Ticket embedding generation in `generate_embeddings.py`
- Added: Migration script `migrate_ticket_embeddings.py` for existing databases
- Modified: `search_tickets()` rewritten to use direct ticket embeddings instead of KB article join proxy
- Added: Full-text search (tsvector) columns and GIN indexes for KB articles, scripts, and tickets
- Added: `fulltext_search_*()` methods using `plainto_tsquery` + `ts_rank`
- Added: Reciprocal Rank Fusion (RRF) utility to merge semantic and FTS results
- Modified: `search_all()` now performs hybrid search (semantic + FTS + RRF)
- Modified: Classification prompt with few-shot examples for better accuracy
- Added: Query rewriting in classification LLM call (zero extra latency)
- Added: LLM reranking step after retrieval for better Hit@1
- Added: Constants for hybrid search and reranking configuration
- Added: Makefile targets `migrate-ticket-embeddings`, `create-fulltext-indexes`
- Modified: `make seed` pipeline includes ticket migration and fulltext index creation

## Affected Components

- `backend/vector_db/models/ticket.py` — Added embedding column
- `backend/vector_db/search.py` — Hybrid search with FTS methods and RRF
- `backend/agents/triage.py` — Few-shot classification, query rewriting, LLM reranking
- `backend/scripts/generate_embeddings.py` — Ticket embedding generation
- `backend/scripts/create_vector_indexes.py` — Ticket IVFFlat index
- `backend/scripts/migrate_ticket_embeddings.py` — New migration script
- `backend/scripts/create_fulltext_indexes.py` — New FTS setup script
- `backend/api/core/constants.py` — Hybrid search and reranking constants
- `Makefile` — New targets, updated seed pipeline
