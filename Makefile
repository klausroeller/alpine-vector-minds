.PHONY: install dev lint test create-admin infra infra-destroy deploy init-ssl production backup

# ─── Development ────────────────────────────────────────────

install:
	cd frontend && pnpm install
	cd backend && uv sync

dev:
	docker compose up --build

lint:
	cd backend && uv run ruff check .
	cd backend && uv run ruff format --check .

test:
	cd backend && uv run pytest

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

infra:
	cd infrastructure/terraform/environments/dev && \
		terraform init -input=false && \
		terraform apply

infra-destroy:
	cd infrastructure/terraform/environments/dev && \
		terraform destroy

deploy:
	./scripts/deploy.sh

init-ssl:
	@test -n "$(ADMIN_EMAIL)" || (echo "ERROR: Set ADMIN_EMAIL=you@example.com" && exit 1)
	ADMIN_EMAIL=$(ADMIN_EMAIL) ./scripts/init-ssl.sh

backup:
	./scripts/backup-db.sh

create-admin:
	@test -n "$(ADMIN_EMAIL)" || (echo "ERROR: Set ADMIN_EMAIL=you@example.com" && exit 1)
	@test -n "$(ADMIN_PASSWORD)" || (echo "ERROR: Set ADMIN_PASSWORD=yourpass" && exit 1)
	cd backend && uv run python -m api.cli --email $(ADMIN_EMAIL) --password $(ADMIN_PASSWORD) $(if $(NAME),--name "$(NAME)",)
