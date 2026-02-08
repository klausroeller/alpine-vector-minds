# Alpine Vector Minds — SupportMind AI

A **self-learning support intelligence layer** for the RealPage SupportMind AI hackathon challenge. Two hero features:

1. **Intelligent Triage Copilot** — Classify support questions, retrieve best-match answers via hybrid search (semantic + full-text with RRF), LLM query rewriting, and LLM reranking
2. **Self-Learning Knowledge Loop** — Detect knowledge gaps from resolved tickets, auto-generate draft KB articles, human-in-the-loop review

**Authors**: Dr. Volker Pernice and Dr. Klaus Röller

## Tech Stack

- **Backend**: Python 3.13 + FastAPI + SQLAlchemy 2.0 + PostgreSQL 16 with pgvector
- **Frontend**: Next.js 15 + TypeScript + Tailwind CSS + shadcn/ui + Lucide icons
- **AI**: OpenAI `text-embedding-3-small` (1536 dims) for embeddings, GPT for LLM agents
- **Infrastructure**: Docker Compose (dev), AWS EC2 (prod)

## Quick Start

```bash
# 1. Copy environment file and set your OpenAI key
cp .env.example .env
# Edit .env → set OPENAI_API_KEY

# 2. Install host dependencies (needed for data pipeline scripts)
make install

# 3. Start all services (DB + API + Web)
make dev

# 4. In a separate terminal: seed the database with data + embeddings + indexes
#    Requires make dev to be running (scripts connect to DB on localhost:5432)
make seed
```

**What `make dev` starts:**
- PostgreSQL with pgvector on `:5432`
- FastAPI backend on `:8000` (auto-creates tables + pgvector extension on startup)
- Next.js frontend on `:3000`

**What `make seed` does (in order):**
1. `make import-data` — Imports all data from `data/SupportMind__Final_Data.xlsx` into the database (3,207 KB articles, 714 scripts, 400 tickets, 1,000 questions, etc.)
2. `make migrate-ticket-embeddings` — Adds embedding column to tickets table
3. `make migrate-qa-columns` — Adds QA scoring columns to conversations table
4. `make generate-embeddings` — Generates OpenAI embeddings for KB articles, scripts, tickets, and questions (~$0.06 cost)
5. `make create-vector-indexes` — Creates IVFFlat indexes on embedding columns for fast similarity search
6. `make create-fulltext-indexes` — Creates tsvector columns and GIN indexes for full-text search

> **Important**: `make seed` runs on the host via `uv run` and connects to the Dockerized DB at `localhost:5432`. The DB must be up (`make dev`) before running `make seed`.

Access the API docs at http://localhost:8000/docs once running.

## Project Structure

```
├── backend/                  # Python backend (unified package)
│   ├── api/                  # FastAPI routes and core logic
│   │   ├── core/             # Config, database, security
│   │   ├── v1/               # API v1 routes (auth, users, chat)
│   │   └── main.py           # FastAPI entry point (pgvector init, table creation)
│   ├── vector_db/            # Vector search with pgvector
│   │   ├── models/           # SQLAlchemy models (9 tables)
│   │   ├── database.py       # Async engine + session
│   │   └── embeddings.py     # OpenAI embedding service
│   ├── agents/               # AI agent services (triage, gap detection, KB generation, QA scoring)
│   ├── scripts/              # Data pipeline CLI scripts
│   │   ├── import_data.py    # Excel → database import
│   │   ├── generate_embeddings.py  # Batch embedding generation
│   │   └── create_vector_indexes.py  # IVFFlat index creation
│   ├── tests/                # Backend tests
│   └── Dockerfile
├── data/                     # Local data files (gitignored)
│   └── SupportMind__Final_Data.xlsx
├── frontend/
│   ├── web/                  # Next.js frontend (TypeScript)
│   └── packages/             # Shared TypeScript packages
├── infrastructure/
│   └── terraform/            # AWS infrastructure as code
├── docs/
│   ├── IMPLEMENTATION_PLAN.md  # Full implementation plan
│   └── CHANGELOG/            # Changelog entries
└── .github/workflows/        # CI/CD pipelines
```

## Database Schema

11 tables, all with proper constraints and indexes:

| Table | Rows (seed) | Embeddings | Description |
|-------|-------------|------------|-------------|
| `knowledge_articles` | 3,207 | 1536-dim | KB articles (seed + auto-generated) |
| `scripts` | 714 | 1536-dim | SQL fix scripts with placeholders |
| `tickets` | 400 | 1536-dim | Support tickets with resolution |
| `conversations` | 400 | — | Chat/phone transcripts linked to tickets (+ QA scores) |
| `questions` | 1,000 | 1536-dim | Ground-truth Q&A for evaluation |
| `kb_lineage` | 483 | — | Provenance chain for auto-generated articles |
| `learning_events` | 161 | — | Knowledge gap detection + review workflow |
| `evaluation_runs` | — | — | Stored copilot evaluation results (hit@1/5/10) |
| `copilot_feedback` | — | — | User thumbs-up/down feedback on search results |
| `placeholders` | 25 | — | Script placeholder reference data |
| `users` | 1 | — | Auth users (dev user auto-seeded) |

## Development Commands

```bash
make install                 # Install all dependencies (frontend + backend)
make dev                     # Start all services in Docker
make seed                    # Full pipeline: import, migrate, embed, index (vector + FTS)
make import-data             # Import Excel data only
make migrate-ticket-embeddings  # Add embedding column to tickets table
make migrate-qa-columns      # Add QA scoring columns to conversations table
make generate-embeddings     # Generate embeddings (KB, scripts, tickets, questions)
make create-vector-indexes   # Create IVFFlat indexes only
make create-fulltext-indexes # Create tsvector columns + GIN indexes
make lint                    # Run ruff linter + formatter check
make test                    # Run pytest
```

## API Endpoints

Base URL: `http://localhost:8000`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/auth/token` | POST | Login (OAuth2) |
| `/api/v1/users/` | POST | Create user |
| `/api/v1/users/me` | GET | Get current user |
| `/api/v1/chat/` | POST | Chat completion (auth required) |
| `/api/v1/dashboard/metrics` | GET | Dashboard metrics (auth required) |
| `/api/v1/knowledge/` | GET | List KB articles with filters (auth required) |
| `/api/v1/knowledge/{id}` | GET | Get KB article detail (auth required) |
| `/api/v1/learning/events` | GET | List learning events (auth required) |
| `/api/v1/learning/review/{id}` | POST | Approve/reject learning event (auth required) |
| `/api/v1/copilot/ask` | POST | Copilot triage + vector search (auth required) |
| `/api/v1/copilot/evaluate` | GET | Run ground-truth evaluation (auth required) |
| `/api/v1/copilot/feedback` | POST | Submit feedback on search result (auth required) |
| `/api/v1/learning/detect-gap` | POST | Detect knowledge gap from ticket (auth required) |
| `/api/v1/qa/score/{id}` | POST | Score a conversation with QA rubric (auth required) |
| `/api/v1/qa/scores` | GET | List scored conversations with filters (auth required) |
| `/api/v1/evaluation/results` | POST | Store evaluation run results (auth required) |
| `/api/v1/evaluation/latest` | GET | Get latest evaluation run (auth required) |

API docs: `/docs` (Swagger) or `/redoc`

## Frontend Pages

| Route | Description |
|-------|-------------|
| `/dashboard` | Metrics overview with charts, QA quality, system accuracy, feedback |
| `/copilot` | AI-powered search with thumbs-up/down feedback buttons |
| `/knowledge` | Knowledge base list with search, filters, pagination |
| `/knowledge/[id]` | Article detail with provenance chain |
| `/learning` | Learning feed with status tabs and approve/reject workflow |
| `/qa` | QA scores — conversation quality assessment with 6-category rubric |

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
| `DEFAULT_USER_EMAIL` | `dev@example.com` | Email for auto-seeded dev user |
| `DEFAULT_USER_PASSWORD` | `dev` | Password for auto-seeded dev user |
| `OPENAI_API_KEY` | — | **Required** for embeddings + chat |

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

## Implementation Status

See [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) for the full plan.

- **Phase 1 — Foundation**: Complete. Database models, data import, embeddings, vector indexes.
- **Phase 2A — Backend API**: Complete. CRUD endpoints for knowledge, learning, dashboard, copilot.
- **Phase 2B — AI Agents**: Complete. Triage agent, gap detection, KB generation, vector search service.
- **Phase 2C — Frontend**: Complete. Sidebar layout, dashboard, copilot, knowledge base, learning feed pages.
- **Phase 3 — Integration & Polish**: Complete. Copilot wired to TriageAgent with provenance enrichment, detect-gap wired to GapDetection + KBGeneration agents, embedding generation on article approval, ground-truth evaluation endpoint.
