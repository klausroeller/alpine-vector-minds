# Fix KB articles generated with empty title/body

**Date**: 2026-02-08 14:00:00

## Summary

Fix KB article generation returning empty content when conversation transcripts are too long for the LLM.

## Changes

- Added: `MAX_KB_TRANSCRIPT_CHARS` constant (8000 chars) in `api/core/constants.py`
- Fixed: Truncate conversation transcript before passing to KB generation to prevent oversized prompts
- Fixed: Raise `ValueError` when LLM returns empty title and body instead of silently creating an empty article

## Affected Components

- `backend/api/core/constants.py` - New transcript truncation constant
- `backend/api/v1/learning.py` - Truncate transcript before KB generation
- `backend/agents/kb_generation.py` - Raise error on empty LLM response instead of silently returning empty content
