# Self-Learning Loop UI

**Date**: 2026-02-08 16:00:00

## Summary

Add gap detection trigger and post-approval feedback with provenance to the Learning Feed, plus auto-search support on the Copilot page.

## Changes

- Added: Collapsible "Detect Gap" form on the Learning Feed page with ticket ID input, loading state, and inline result display (gap found with article preview + provenance badge, or no-gap info message)
- Added: Post-approval feedback panel showing activated article content, full provenance chain (Ticket → Conversation → Script), and a "Verify in Copilot" button
- Added: Post-rejection feedback message on the Learning Feed
- Added: `?q=` URL param support on the Copilot page — pre-fills search and auto-triggers query on mount
- Added: Suspense boundary around Copilot page content for Next.js 15 compatibility
- Added: Missing frontend dependencies (recharts, @radix-ui/react-progress, @radix-ui/react-select)

## Affected Components

- `frontend/web/src/app/learning/page.tsx` - Added detect-gap form, post-approval/rejection feedback panels with provenance chain
- `frontend/web/src/app/copilot/page.tsx` - Added URL param auto-search and Suspense boundary
