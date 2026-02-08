# Fix deep research layout: move summary/evidence below search bar

**Date**: 2026-02-08 14:00:00

## Summary

Move ResearchReportView from full-width bottom position into the left column, directly below the search bar.

## Changes

- Fixed: ResearchReportView now renders inside the left column instead of outside the two-column container

## Affected Components

- `frontend/web/src/app/copilot/page.tsx` - Moved ResearchReportView JSX into left column div
