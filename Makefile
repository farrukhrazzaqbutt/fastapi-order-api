.PHONY: help build up down logs test clean migrate seed

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## View logs
	docker-compose logs -f api

logs-all: ## View all service logs
	docker-compose logs -f

test: ## Run tests
	docker-compose exec api pytest

test-cov: ## Run tests with coverage
	docker-compose exec api pytest --cov=app --cov-report=html

test-watch: ## Run tests in watch mode
	docker-compose exec api pytest -f

migrate: ## Run database migrations
	docker-compose exec api alembic upgrade head

migrate-create: ## Create new migration
	docker-compose exec api alembic revision --autogenerate -m "$(message)"

seed: ## Seed admin user
	docker-compose exec api python -c "from app.db import SessionLocal; from app.models import User; from app.auth import get_password_hash; db = SessionLocal(); db.add(User(username='admin', hashed_password=get_password_hash('admin'))); db.commit(); print('Admin user created')"

shell: ## Open Python shell
	docker-compose exec api python

db-shell: ## Open database shell
	docker-compose exec db psql -U app -d app

redis-shell: ## Open Redis shell
	docker-compose exec redis redis-cli

clean: ## Clean up containers and volumes
	docker-compose down -v
	docker system prune -f

dev-setup: ## Setup development environment
	cp env.sample .env
	docker-compose up -d db redis
	sleep 10
	make migrate
	make seed

format: ## Format code
	docker-compose exec api black .
	docker-compose exec api isort .

lint: ## Lint code
	docker-compose exec api flake8 .
	docker-compose exec api black --check .
	docker-compose exec api isort --check-only .

security: ## Run security checks
	docker-compose exec api bandit -r app/
	docker-compose exec api safety check

full-test: ## Run full test suite with all checks
	make test
	make lint
	make security
