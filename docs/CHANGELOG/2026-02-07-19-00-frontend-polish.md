# Frontend polish: chart colors, dropdown visibility, error messages

**Date**: 2026-02-07 19:00:00

## Summary

Fix three frontend UI issues: priority chart colors, invisible dropdown options, and unhelpful error messages.

## Changes

- Fixed: `priority-donut-chart.tsx` — Color map keys were uppercase but API returns lowercase, causing all segments to render as gray. Now uses lowercase keys with case-insensitive lookup.
- Fixed: `article-filters.tsx` — Select dropdown items were invisible (dark text on dark background). Added explicit `text-slate-300` and `focus:bg-white/[0.08] focus:text-white` classes.
- Modified: `api.ts` — `ApiError` now includes `endpoint`, `method`, and a `debugMessage` getter that formats as `"POST /api/v1/copilot/ask — [500] Internal server error"`. Network errors include original error message. Added try/catch around fetch for network-level failures.
- Modified: All page files (`dashboard`, `knowledge`, `learning`, `copilot`) — Error state now uses `ApiError.debugMessage` for detailed display. Pages that previously swallowed errors silently now show red error banners.

## Affected Components

- `frontend/web/src/components/dashboard/priority-donut-chart.tsx`
- `frontend/web/src/components/knowledge/article-filters.tsx`
- `frontend/web/src/lib/api.ts`
- `frontend/web/src/app/dashboard/page.tsx`
- `frontend/web/src/app/knowledge/page.tsx`
- `frontend/web/src/app/learning/page.tsx`
- `frontend/web/src/app/copilot/page.tsx`
