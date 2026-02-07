# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Philosophy

**This is a hackathon project.** Prioritize speed and focus:
- Fewer features that work flawlessly with a polished UI over many half-finished ones
- Do not add new features at the cost of breaking or degrading existing ones
- Every feature must be fully functional end-to-end before moving on to the next
- **Design the data model as if it's going to prod tomorrow** — use proper constraints, indexes, non-nullable columns where appropriate, and meaningful foreign keys. Migrating a sloppy schema later costs more than getting it right now

## Documentation

**Keeping documentation concise and up to date is essential.**

- The `README.md` is the single source of truth — update it whenever features, APIs, or deployment steps change
- Keep it focused on these sections: **Overall Scope**, **Backend**, **Frontend**, **Deployment**
- The README must always clearly explain: what the project does, the rough project structure, and enough context for someone new to get oriented quickly
- Be concise: short descriptions, no filler. If something changed, update the docs in the same PR
- Outdated documentation is worse than no documentation

## Project Overview

See [README.md](README.md) for full project documentation.

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

## Parametrize, Don't Hardcode

- **Always use environment variables, config files, or constants** for values that may change across environments — never hardcode paths, URLs, ports, cluster config, or numeric thresholds directly in application code
- Extract magic numbers into named constants or configuration with clear intent (e.g., `MAX_RETRY_ATTEMPTS = 3`, not a bare `3`)
- Paths and endpoints should come from env vars or a central config module, not be scattered as string literals
- Hardcoded values are tech debt — parametrize early to keep the codebase portable and maintainable

## Analysis & Planning Artifacts

**Preserve useful intermediate work from analysis and planning tasks.**

- When performing long, detailed analysis or planning tasks that involve writing analysis scripts or producing intermediate results, **do not delete them afterwards**
- Save the most important scripts, results, and findings as markdown files in `docs/` (e.g., `docs/analysis-<topic>.md`)
- These artifacts are valuable context for human programmers — they document the reasoning, data, and conclusions behind decisions
- **Never delete files in `docs/`** unless explicitly asked to by the user

## Git Conventions

- **Do NOT use `Co-Authored-By:` tags** in commit messages
- Write clear, concise commit messages describing the change
- Use imperative mood in commit subject (e.g., "Add feature" not "Added feature")
