.PHONY: up up-lite down build logs seed test test-backend test-frontend migrate shell frontend-deps createsuperuser

up:
	cp -n .env.example .env 2>/dev/null || true
	docker compose up --build -d

# Postgres + Redis + backend + frontend only (no Celery). Always rebuilds images.
up-lite:
	cp -n .env.example .env 2>/dev/null || true
	docker compose up --build -d postgres redis backend frontend
	docker compose exec frontend npm install

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

seed:
	docker compose exec backend python manage.py seed_data

test: test-backend test-frontend

test-backend:
	docker compose exec backend pytest

test-frontend:
	docker compose exec frontend npm test

migrate:
	docker compose exec backend python manage.py migrate

shell:
	docker compose exec backend python manage.py shell

# Sync frontend node_modules volume after package.json changes (Docker dev mode).
frontend-deps:
	docker compose exec frontend npm install

createsuperuser:
	docker compose exec backend python manage.py createsuperuser
