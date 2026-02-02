# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Alpine Vector Minds is a full-stack monorepo template for AI-powered applications with:
- **Backend**: Python 3.13 + FastAPI + SQLAlchemy + PostgreSQL with pgvector
- **Frontend**: Next.js 15 + TypeScript + shadcn/ui + Lucide icons
- **Infrastructure**: Docker containers deployed to AWS EC2 (non-serverless)

## Quick Start

```bash
# 1. Install dependencies
pnpm install                    # Frontend/monorepo deps
cd apps/api && uv sync          # Backend deps
cd ../..

# 2. Copy environment file
cp .env.example .env

# 3. Start all services (DB + API + Web)
pnpm dev
```

This starts:
- PostgreSQL with pgvector on `:5432`
- FastAPI backend on `:8000` (with hot reload)
- Next.js frontend on `:3000` (with hot reload)

Access the API docs at http://localhost:8000/docs once running.

## Monorepo Structure

```
├── apps/
│   ├── api/          # FastAPI backend (Python)
│   └── web/          # Next.js frontend (TypeScript)
├── services/
│   ├── agents/       # AI agent services
│   └── search/       # Vector search with pgvector
├── packages/
│   └── shared/       # Shared TypeScript types
├── infrastructure/
│   └── terraform/    # AWS infrastructure as code
├── docker/           # Dockerfiles for API and Web
├── docs/
│   └── CHANGELOG/    # Changelog entries (see Changelog Guidelines)
└── .github/workflows # CI/CD pipelines
```

## Development Commands

```bash
# Install all dependencies
pnpm install                    # Frontend/monorepo deps
cd apps/api && uv sync          # Backend deps

# Start all services locally (DB + API + Web)
pnpm dev

# Individual services
pnpm dev:db                     # PostgreSQL with pgvector (Docker)
pnpm dev:api                    # FastAPI on :8000
pnpm dev:web                    # Next.js on :3000

# Database
pnpm db:migrate                 # Run Alembic migrations
pnpm db:makemigrations "msg"    # Create new migration

# Testing
pnpm test                       # All tests
pnpm test:api                   # Backend tests only
cd apps/api && uv run pytest -v # Verbose backend tests

# Linting
pnpm lint                       # All linting
cd apps/api && uv run ruff check . && uv run ruff format .

# Docker
pnpm docker:up                  # Start full stack in Docker
pnpm docker:down                # Stop containers
```

## Changelog Guidelines

**Every change to this repository must be documented in a changelog entry.**

Create a new markdown file in `docs/CHANGELOG/` with the following naming convention:

```
YYYY-MM-DD-HH-MM-short-description.md
```

Example: `2025-02-02-23-00-initial-monorepo-setup.md`, where HH-MM is the current time in hours and minutes

Each changelog entry should include:
- **Date**: The timestamp of the change (including time HH-MM-SS)
- **Summary**: A brief one-line description
- **Changes**: Detailed list of what was added, modified, or removed
- **Affected Components**: Which parts of the codebase were touched (apps/api, apps/web, services, etc.)

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

- `apps/api/` - Description of API changes
- `apps/web/` - Description of frontend changes
```

## Tech Stack Details

### Backend (apps/api)
- **Package Manager**: uv
- **Framework**: FastAPI with async support
- **ORM**: SQLAlchemy 2.0 with async (asyncpg driver)
- **Migrations**: Alembic
- **Auth**: JWT tokens (python-jose + passlib)
- **Linting**: Ruff
- **Testing**: pytest + pytest-asyncio

### Frontend (apps/web)
- **Package Manager**: pnpm (workspace managed by Turborepo)
- **Framework**: Next.js 15 with App Router
- **Styling**: Tailwind CSS + shadcn/ui components
- **Icons**: Lucide React

### Database
- PostgreSQL 16 with pgvector extension for vector embeddings
- Connection: `postgresql+asyncpg://` (async driver)

### Infrastructure
- AWS EC2 for hosting (avoiding serverless)
- CloudFront for frontend CDN (optional Docker on EC2)
- Terraform for infrastructure as code
- GitHub Actions for CI/CD

## API Endpoints

Base URL: `http://localhost:8000`

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /api/v1/auth/token` - Login (OAuth2 password flow)
- `POST /api/v1/users/` - Create user
- `GET /api/v1/users/me` - Get current user (requires auth)

API docs available at `/docs` (Swagger) or `/redoc` when running.

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/alpine_vector_minds
SECRET_KEY=your-secret-key

# Optional
OPENAI_API_KEY=sk-...  # For embeddings in search service
```

## Adding shadcn Components

```bash
cd apps/web
pnpm dlx shadcn@latest add button dialog dropdown-menu
```

## Git Conventions

- **Do NOT use `Co-Authored-By:` tags** in commit messages
- Write clear, concise commit messages describing the change
- Use imperative mood in commit subject (e.g., "Add feature" not "Added feature")

## Project Context

Authors: Dr. Volker Pernice and Dr. Klaus Röller
