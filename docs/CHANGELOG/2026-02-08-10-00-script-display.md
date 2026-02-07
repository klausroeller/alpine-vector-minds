# Fix script display across copilot and knowledge base

**Date**: 2026-02-08 10:00:00

## Summary

Fix scripts showing as "KB Article" in copilot results and render script content as formatted code blocks.

## Changes

- Fixed: `copilot.py` — Map agent source_type values (SCRIPT/KB/TICKET_RESOLUTION) to frontend values (script/kb_article/ticket). Scripts were incorrectly falling through to `kb_article` default.
- Modified: `knowledge.py` — Detail endpoint now falls back to `scripts` table for SCRIPT-* IDs, so script detail pages resolve correctly.
- Modified: `result-card.tsx` — Script previews render as `<pre><code>` blocks with emerald syntax coloring. Both KB articles and scripts are now clickable links.
- Modified: `knowledge/[id]/page.tsx` — Body renders as code block when `source_type === 'script'`. Added "Script" to source badge config. Shows article ID in header.

## Affected Components

- `backend/api/v1/copilot.py`
- `backend/api/v1/knowledge.py`
- `frontend/web/src/components/copilot/result-card.tsx`
- `frontend/web/src/app/knowledge/[id]/page.tsx`
