.PHONY: install dev dev-teardown lint test create-admin infra infra-destroy deploy init-ssl production backup migrate-ticket-embeddings import-data generate-embeddings create-vector-indexes create-fulltext-indexes seed seed-production evaluate

# ─── Development ────────────────────────────────────────────

# Install frontend (pnpm) and backend (uv) dependencies
install:
	cd frontend && pnpm install
	cd backend && uv sync

# Start the full dev environment with Docker Compose
dev:
	docker compose up --build

# Tear down dev environment and remove volumes
dev-teardown:
	docker compose down -v

# Run linter and format checks on backend code
lint:
	cd backend && uv run ruff check .
	cd backend && uv run ruff format --check .

# Run backend test suite
test:
	cd backend && uv run pytest

# ─── Data Pipeline ─────────────────────────────────────────

# Add embedding column to tickets table (idempotent)
migrate-ticket-embeddings:
	docker exec alpine-api uv run python -m scripts.migrate_ticket_embeddings

# Import Excel data into the database
import-data:
	docker exec alpine-api uv run python -m scripts.import_data

# Generate vector embeddings for all imported records
generate-embeddings:
	docker exec alpine-api uv run python -m scripts.generate_embeddings

# Create pgvector indexes for similarity search
create-vector-indexes:
	docker exec alpine-api uv run python -m scripts.create_vector_indexes

# Create full-text search columns and GIN indexes
create-fulltext-indexes:
	docker exec alpine-api uv run python -m scripts.create_fulltext_indexes

# Run full data pipeline: import, embed, index (vector + fulltext)
seed: import-data migrate-ticket-embeddings generate-embeddings create-vector-indexes create-fulltext-indexes

# Run full data pipeline on the production server
seed-production:
	./scripts/seed-production.sh

# Run copilot accuracy evaluation and save reports to data/evaluation-reports/
#   make evaluate ENV=dev EVAL_LIMIT=5 EVAL_START=0 EVAL_EMAIL=dev@example.com EVAL_PASSWORD=dev
evaluate:
	cd backend && uv run python -m scripts.evaluate \
		--env $(or $(ENV),dev) \
		$(if $(EVAL_LIMIT),--limit $(EVAL_LIMIT),) \
		$(if $(EVAL_START),--start $(EVAL_START),) \
		$(if $(BASE_URL),--base-url $(BASE_URL),) \
		$(if $(EVAL_EMAIL),--email $(EVAL_EMAIL),) \
		$(if $(EVAL_PASSWORD),--password $(EVAL_PASSWORD),)

# ─── Production (single command) ───────────────────────────
#
# Full setup from scratch:
#   make production ADMIN_EMAIL=you@example.com
#
# Optional: set ADMIN_PASSWORD (auto-generated if omitted)

production:
	@test -n "$(ADMIN_EMAIL)" || (echo "ERROR: Set ADMIN_EMAIL=you@example.com" && exit 1)
	ADMIN_EMAIL=$(ADMIN_EMAIL) ADMIN_PASSWORD=$(ADMIN_PASSWORD) ./scripts/setup-production.sh

# ─── Individual deployment steps ───────────────────────────

# Provision cloud infrastructure with Terraform
infra:
	cd infrastructure/terraform/environments/dev && \
		terraform init -input=false && \
		terraform apply

# Destroy cloud infrastructure
infra-destroy:
	cd infrastructure/terraform/environments/dev && \
		terraform destroy

# Deploy application to production server
deploy:
	./scripts/deploy.sh

# Initialize SSL certificates via Let's Encrypt
init-ssl:
	@test -n "$(ADMIN_EMAIL)" || (echo "ERROR: Set ADMIN_EMAIL=you@example.com" && exit 1)
	ADMIN_EMAIL=$(ADMIN_EMAIL) ./scripts/init-ssl.sh

# Create a database backup and upload to S3
backup:
	./scripts/backup-db.sh

# Create an admin user account
create-admin:
	@test -n "$(ADMIN_EMAIL)" || (echo "ERROR: Set ADMIN_EMAIL=you@example.com" && exit 1)
	@test -n "$(ADMIN_PASSWORD)" || (echo "ERROR: Set ADMIN_PASSWORD=yourpass" && exit 1)
	cd backend && uv run python -m api.cli --email $(ADMIN_EMAIL) --password $(ADMIN_PASSWORD) $(if $(NAME),--name "$(NAME)",)
