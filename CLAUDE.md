# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Philosophy

**This is a hackathon project.** Prioritize speed and focus:
- Fewer features that work flawlessly with a polished UI over many half-finished ones
- Do not add new features at the cost of breaking or degrading existing ones
- Every feature must be fully functional end-to-end before moving on to the next

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

- **Backend**: Python 3.13, FastAPI, SQLAlchemy 2.0, pytest, Ruff
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

## Python Virtual Environment

- **Always use `uv run`** to execute Python commands (e.g., `uv run pytest`, `uv run ruff check .`)
- **Never use bare `python` or `pip`** — all Python execution must go through `uv` to ensure the correct virtual environment and dependencies
- Run `uv sync` from `backend/` to install or update dependencies
- When adding new dependencies, add them to `backend/pyproject.toml` and run `uv sync` — do not use `pip install`

## Reproducibility

**All changes must be fully reproducible from the repository.**

- Never make manual, one-off changes to infrastructure, cloud accounts (e.g., AWS), databases, or services
- Every action must be captured in code: scripts, Terraform, Makefile targets, Docker configs, etc.
- If a change requires a new command or process, add it to the `Makefile`, a script, or the appropriate IaC tool — so that anyone can re-run it from scratch
- The goal is a reliable production system where the entire environment can be torn down and rebuilt from the repo alone

## Makefile

- **Always update the `Makefile`** when adding new commands, scripts, or repeatable tasks
- The `Makefile` is the single entry point for all development commands — keep it up to date
- **Never run scripts directly** (e.g., `./scripts/deploy.sh`) — always use the corresponding `make` target (e.g., `make deploy`). Makefile targets may include validation, environment setup, or parameter handling that scripts alone do not.

## Git Conventions

- **Do NOT use `Co-Authored-By:` tags** in commit messages
- Write clear, concise commit messages describing the change
- Use imperative mood in commit subject (e.g., "Add feature" not "Added feature")
