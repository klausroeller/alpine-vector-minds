.PHONY: install dev

install:
	cd frontend && pnpm install
	cd backend && uv sync

dev:
	docker compose up --build