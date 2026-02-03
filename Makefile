.PHONY: install-dev deploy-dev deploy-prod

install-dev:
	cd frontend && pnpm install
	cd backend && uv sync

deploy-dev:
	docker-compose up

deploy-prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
