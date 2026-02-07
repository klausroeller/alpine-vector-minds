# Phase 1: Database Models + Data Pipeline

**Date**: 2026-02-07 22:30:00

## Summary

Add 8 SQLAlchemy models, Excel data import pipeline, embedding generation, and IVFFlat vector index creation. Full pipeline accessible via `make seed`.

## Changes

- Added: 8 new SQLAlchemy models (KnowledgeArticle, Script, Ticket, Conversation, Question, KBLineage, LearningEvent, Placeholder)
- Added: `openpyxl` dependency for Excel parsing
- Added: `backend/scripts/import_data.py` — imports all data from `SupportMind__Final_Data.xlsx`
- Added: `backend/scripts/generate_embeddings.py` — generates OpenAI embeddings for KB articles, scripts, and questions
- Added: `backend/scripts/create_vector_indexes.py` — creates IVFFlat indexes on embedding columns
- Modified: `backend/api/main.py` — enables pgvector extension on startup, registers all models
- Modified: `backend/vector_db/models/__init__.py` — exports all 9 models
- Added: Makefile targets `import-data`, `generate-embeddings`, `create-vector-indexes`, `seed`

## Affected Components

- `backend/vector_db/models/` — 8 new model files
- `backend/scripts/` — new data pipeline package (3 scripts)
- `backend/api/main.py` — pgvector extension + model registration
- `Makefile` — data pipeline targets
