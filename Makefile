.PHONY: up down build logs seed test test-backend test-frontend migrate shell

up:
	cp -n .env.example .env 2>/dev/null || true
	docker compose up --build -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

seed:
	docker compose exec backend python manage.py seed_data

test: test-backend

test-backend:
	docker compose exec backend pytest

test-frontend:
	docker compose exec frontend npm test

migrate:
	docker compose exec backend python manage.py migrate

shell:
	docker compose exec backend python manage.py shell
