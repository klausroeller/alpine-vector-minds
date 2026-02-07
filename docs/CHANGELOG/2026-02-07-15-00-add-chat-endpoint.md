# Add OpenAI Chat Completion Endpoint

**Date**: 2026-02-07 15:00:00

## Summary

Add authenticated POST `/api/v1/chat/` endpoint that sends a prompt to OpenAI's chat completion API and returns the response.

## Changes

- Added: `backend/api/v1/chat.py` — new chat route with `ChatRequest`/`ChatResponse` models
- Modified: `backend/vector_db/embeddings.py` — added `OPENAI_CHAT_MODEL` setting (default `gpt-4o-mini`)
- Modified: `backend/api/v1/__init__.py` — registered chat router at `/chat`

## Affected Components

- `backend/api/v1/` — New chat endpoint requiring authentication
- `backend/vector_db/` — Extended EmbeddingSettings with chat model config
