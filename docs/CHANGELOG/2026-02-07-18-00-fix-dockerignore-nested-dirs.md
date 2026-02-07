# Fix .dockerignore to exclude nested node_modules

**Date**: 2026-02-07 18:00:00

## Summary

Fix Docker build failure caused by local web/node_modules conflicting with container deps.

## Changes

- Fixed: `.dockerignore` patterns to use `**/ ` globbing for `node_modules` and `.next`

## Affected Components

- `frontend/.dockerignore` - Use recursive glob patterns to exclude nested directories
