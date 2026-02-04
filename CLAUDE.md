# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

See [README.md](README.md) for full project documentation including:
- Project structure
- Quick start guide
- Development commands
- API endpoints
- Environment variables

## Key Paths

| Component | Path |
|-----------|------|
| Backend (unified) | `backend/` |
| API routes | `backend/api/` |
| Vector search | `backend/vector_db/` |
| AI agents | `backend/agents/` |
| Frontend | `frontend/web/` |
| Shared packages | `frontend/packages/` |
| Infrastructure | `infrastructure/terraform/` |

## Tech Stack Quick Reference

- **Backend**: Python 3.13, FastAPI, SQLAlchemy 2.0, Alembic, pytest, Ruff
- **Frontend**: Next.js 15, TypeScript, Tailwind CSS, shadcn/ui, Lucide
- **Database**: PostgreSQL 16 with pgvector
- **Package Managers**: uv (Python), pnpm (Node.js)

## Changelog Guidelines

**Every change must be documented in a changelog entry.**

Create a markdown file in `docs/CHANGELOG/` with this naming convention:

```
YYYY-MM-DD-HH-MM-short-description.md
```

Template:
```markdown
# Short Description

**Date**: YYYY-MM-DD HH:MM:SS

## Summary

Brief one-line description of the change.

## Changes

- Added: new feature or file
- Modified: existing functionality
- Removed: deprecated code
- Fixed: bug fix

## Affected Components

- `backend/api/` - Description of API changes
- `frontend/web/` - Description of frontend changes
```

## Git Conventions

- **Do NOT use `Co-Authored-By:` tags** in commit messages
- Write clear, concise commit messages describing the change
- Use imperative mood in commit subject (e.g., "Add feature" not "Added feature")
