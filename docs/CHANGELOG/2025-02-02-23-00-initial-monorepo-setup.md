# Initial Monorepo Setup

**Date**: 2025-02-02 23:00

## Summary

Created the foundational monorepo structure for Alpine Vector Minds, a full-stack AI-powered application template.

## Changes

### Structure Created
- `apps/api/` - FastAPI backend with Python 3.13 and uv package manager
- `apps/web/` - Next.js 15 frontend with TypeScript, shadcn/ui, and Lucide icons
- `services/agents/` - AI agent services (placeholder)
- `services/search/` - Vector search service with pgvector integration
- `packages/shared/` - Shared TypeScript types between frontend and backend
- `infrastructure/terraform/` - AWS infrastructure as code with VPC module
- `docker/` - Dockerfiles for API and Web services
- `.github/workflows/` - CI/CD pipelines (ci.yml, deploy.yml)

### Backend Features
- FastAPI with async support
- SQLAlchemy 2.0 with asyncpg driver
- Alembic for database migrations
- JWT authentication (python-jose + passlib)
- User model and auth/users API endpoints
- Ruff for linting, pytest for testing

### Frontend Features
- Next.js 15 with App Router
- Tailwind CSS with shadcn/ui component system
- Lucide React icons
- TypeScript strict mode

### Infrastructure
- Docker Compose for local development (PostgreSQL with pgvector)
- Docker Compose for full stack deployment
- Terraform modules for AWS VPC
- GitHub Actions for CI (linting, testing, Docker builds)
- GitHub Actions for deployment to AWS ECR

### Tooling Choices
- **Python Package Manager**: uv
- **Node Package Manager**: pnpm with Turborepo
- **Database ORM**: SQLAlchemy + Alembic
- **Vector Storage**: pgvector (PostgreSQL extension)
- **Authentication**: JWT tokens
- **Infrastructure**: Terraform
- **CI/CD**: GitHub Actions

## Authors

Dr. Volker Pernice and Dr. Klaus Röller
