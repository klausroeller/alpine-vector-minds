# Fix SQL syntax error in vector search queries

**Date**: 2026-02-08 00:00:00

## Summary

Fix 500 errors on copilot "Ask" by replacing `::vector` cast syntax with `CAST(... AS vector)` in raw SQL queries.

## Changes

- Fixed: replaced `:embedding::vector` with `CAST(:embedding AS vector)` in all three search methods to prevent SQLAlchemy/asyncpg parameter-substitution conflicts

## Affected Components

- `backend/vector_db/search.py` - Fixed vector cast syntax in `search_knowledge_articles`, `search_scripts`, and `search_tickets`
