# Add `make evaluate` target with evaluation report generation

**Date**: 2026-02-08 16:00:00

## Summary

Add CLI evaluation workflow via `make evaluate` that calls the copilot evaluation endpoint, saves JSON and markdown reports to `data/evaluation-reports/`.

## Changes

- Added: `backend/scripts/evaluate.py` — CLI script that authenticates, runs evaluation, and saves reports
- Added: `data/evaluation-reports/.gitkeep` — directory marker for report storage
- Modified: `Makefile` — new `evaluate` target with `ENV`, `BASE_URL`, `EVAL_EMAIL`, `EVAL_PASSWORD` parameters

## Affected Components

- `backend/scripts/` — New evaluate script
- `Makefile` — New `evaluate` target in Data Pipeline section
- `data/evaluation-reports/` — New report output directory
