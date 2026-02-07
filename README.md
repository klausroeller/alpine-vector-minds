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
| `/api/v1/chat/` | POST | Chat completion (auth required) |

API docs: `/docs` (Swagger) or `/redoc`

## Environment Variables

Copy `.env.example` to `.env` — it has working local dev defaults out of the box. Both `docker-compose.yml` (dev) and `docker-compose.prod.yml` (production) read from root `.env` via `${VAR:-default}` interpolation.

| Variable | Dev default | Description |
|----------|-------------|-------------|
| `POSTGRES_USER` | `postgres` | Database user |
| `POSTGRES_PASSWORD` | `postgres` | Database password |
| `POSTGRES_DB` | `alpine_vector_minds` | Database name |
| `SECRET_KEY` | `dev-secret-key-...` | JWT signing key |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | API URL for frontend |
| `OPENAI_API_KEY` | — | OpenAI API key (for embeddings & chat) |
| `OPENAI_CHAT_MODEL` | `gpt-4o-mini` | Model for chat completions |

## Deployment

All scripts use the domain `alpine-vector-minds.de` by default (overridable via `DEPLOY_HOST`).

**Prerequisites** for deploying:
1. SSH key at `~/.ssh/avm-ec2-key.pem` (get from whoever ran initial `make production` setup, or set `KEY_PATH`)
2. `.env.production` file in the repo root (with real secrets)

```bash
make deploy       # Deploy code + restart containers
make backup       # Download a database backup
make init-ssl     # Re-initialize SSL certificate (ADMIN_EMAIL required)
```

## Adding shadcn Components

```bash
cd frontend/web
pnpm dlx shadcn@latest add button dialog dropdown-menu
```
