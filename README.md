# Alpine Vector Minds

A full-stack monorepo template for AI-powered applications.

**Authors**: Dr. Volker Pernice and Dr. Klaus Röller

## Tech Stack

- **Backend**: Python 3.13 + FastAPI + SQLAlchemy + PostgreSQL with pgvector
- **Frontend**: Next.js 15 + TypeScript + shadcn/ui + Lucide icons
- **Infrastructure**: Docker containers deployed to AWS EC2

## Quick Start

```bash
# Copy environment file
cp .env.example .env

# Start all services (DB + API + Web with hot reload)
make dev
```

This starts:
- PostgreSQL with pgvector on `:5432`
- FastAPI backend on `:8000`
- Next.js frontend on `:3000`

Access the API docs at http://localhost:8000/docs once running.

## Project Structure

```
├── backend/                  # Python backend (unified package)
│   ├── api/                  # FastAPI routes and core logic
│   │   ├── core/             # Config, database, security
│   │   ├── models/           # SQLAlchemy models
│   │   ├── v1/               # API v1 routes
│   │   └── main.py           # FastAPI entry point
│   ├── vector_db/            # Vector search with pgvector
│   ├── agents/               # AI agent services
│   ├── tests/                # Backend tests
│   └── Dockerfile            # API container definition
├── frontend/
│   ├── web/                  # Next.js frontend (TypeScript)
│   │   └── Dockerfile        # Web container definition
│   └── packages/             # Shared TypeScript packages
├── infrastructure/
│   └── terraform/            # AWS infrastructure as code
├── docs/
│   └── CHANGELOG/            # Changelog entries
└── .github/workflows/        # CI/CD pipelines
```

## Development Commands

```bash
make install      # Install all dependencies (frontend + backend)
make dev          # Start all services in Docker
```

## API Endpoints

Base URL: `http://localhost:8000`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint |
| `/health` | GET | Health check |
| `/api/v1/auth/token` | POST | Login (OAuth2) |
| `/api/v1/users/` | POST | Create user |
| `/api/v1/users/me` | GET | Get current user |

API docs: `/docs` (Swagger) or `/redoc`

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/alpine_vector_minds
SECRET_KEY=your-secret-key

# Optional
OPENAI_API_KEY=sk-...  # For embeddings
```

## Adding shadcn Components

```bash
cd frontend/web
pnpm dlx shadcn@latest add button dialog dropdown-menu
```
