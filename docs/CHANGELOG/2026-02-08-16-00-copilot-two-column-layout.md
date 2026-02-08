# Copilot Two-Column Layout

**Date**: 2026-02-08 16:00:00

## Summary

Restructured the copilot page to use a two-column layout: search bar + AI answer on the left, result cards on the right.

## Changes

- Modified: outer container widened from `max-w-3xl` to `max-w-6xl`
- Modified: search bar, AI answer, errors, and empty state placed in left column (`flex-1`)
- Modified: classification badge and result cards placed in right column (`w-[400px]`, shown only when results exist)
- Modified: research full report renders full-width below the two-column area
- Added: responsive fallback to single-column stacked layout below `lg` breakpoint

## Affected Components

- `frontend/web/src/app/copilot/page.tsx` - Restructured layout to two-column flex
