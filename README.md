# Rate Tracker

A production-shaped interest rate tracking application: data ingestion → PostgreSQL persistence → cached Django REST API → Next.js dashboard.

Built as a senior full-stack take-home assessment for Forbes Advisor / Marketplace.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) 24+ and Docker Compose v2
- [Make](https://www.gnu.org/software/make/) (optional, for convenience commands)
- ~4 GB free disk space (seed file + Docker images)

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env

# 2. Start all services (Django, Postgres, Redis, Celery, Next.js)
make up
# or: docker compose up --build -d

# 3. Load seed data (~1M rows, takes a few minutes)
make seed
# or: docker compose exec backend python manage.py seed_data

# 4. Open the dashboard
open http://localhost:3000
```

The API is available at `http://localhost:8000/api/`.

**Reviewer note:** The dashboard loads immediately after `docker compose up` (empty state). Run `make seed` to populate data. Total startup to dashboard: under 2 minutes.

## How to Run Locally

### Start the stack

```bash
docker compose up --build
```

Services:

| Service | Port | Description |
|---------|------|-------------|
| frontend | 3000 | Next.js dashboard |
| backend | 8000 | Django REST API |
| postgres | 5432 | PostgreSQL 16 |
| redis | 6379 | Cache + Celery broker |
| celery-worker | — | Background ingestion worker |
| celery-beat | — | Scheduler (every 15 min) |

### Seed the database

```bash
make seed
# or
python manage.py seed_data  # inside backend container
```

### Run tests

```bash
make test
# or
docker compose exec backend pytest
```

### Tail logs

```bash
make logs
# or
./scripts/logs.sh
```

### Makefile commands

| Command | Description |
|---------|-------------|
| `make up` | Build and start all containers |
| `make down` | Stop containers |
| `make seed` | Load parquet seed data |
| `make test` | Run backend pytest suite |
| `make migrate` | Run Django migrations |
| `make logs` | Follow container logs |

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/rates/latest` | None | Latest rate per provider. Optional `?type=` filter. Cached 60s. |
| GET | `/api/rates/history` | None | Paginated history. Requires `?provider=` and `?type=`. Optional `?from=` and `?to=`. |
| POST | `/api/rates/ingest` | Bearer token | Webhook ingest. Set `INGEST_BEARER_TOKEN` in `.env`. |

### Example: ingest webhook

```bash
curl -X POST http://localhost:8000/api/rates/ingest \
  -H "Authorization: Bearer dev-ingest-token-change-me" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "Chase",
    "rate_type": "30yr_fixed_mortgage",
    "rate_value": "6.75",
    "effective_date": "2025-06-01"
  }'
```

## Architecture

```
rates_seed.parquet
       │
       ▼
  seed_data / Celery worker
       │
       ▼
 PostgreSQL ◄── RawResponse + Rate tables
       │
       ▼
 Django REST API ◄── Redis cache
       │
       ▼
 Next.js Dashboard (auto-refresh 60s)
```

See [schema.md](./schema.md) for database design and [DECISIONS.md](./DECISIONS.md) for engineering rationale and SOLID/design-pattern notes.

## Architecture (SOLID)

### Backend

```
API Views (HTTP only)
    ├── LatestRatesCacheService  → RateRepository + Redis (Facade)
    ├── RateHistoryService       → RateRepository
    └── IngestionService         → RateWriter + RateRecordSource (Strategy)

RateWriter (persist)  →  ProviderResolver + ORM
ParquetRateSource     →  implements RateRecordSource (Open/Closed)
adapters/http.py      →  HTTP response → parsed record (Adapter)
```

### Frontend

```
page.tsx (composition only)
    ├── useLatestRates      → fetch + auto-refresh + loading/error (SRP)
    ├── useRateHistory      → chart data fetch (SRP)
    ├── useSortableRates    → sort state → sortRates() pure fn (SRP)
    └── useDefaultProvider  → initial provider selection

lib/ratesApiClient.ts   → default RatesApiClient implementation (DIP)
lib/sortRates.ts        → pure sort/order utilities (testable without React)
interfaces/             → all shared types & interfaces (rates, sort, hooks, api client)
components/             → presentational UI only (RateTable, RateChart, ErrorBanner)
```

## Environment Variables

Copy `.env.example` to `.env`. All required variables are documented there. The application fails fast at startup if any required variable is missing.

## Project Structure

```
├── backend/           # Django + DRF + Celery
├── frontend/          # Next.js dashboard
├── data/              # rates_seed.parquet
├── scripts/           # Helper scripts
├── docker-compose.yml
├── Makefile
├── schema.md
└── DECISIONS.md
```

## Architectural Choices

- **Django + DRF** for typed API with built-in admin and migrations
- **PostgreSQL** with composite indexes tuned for the three required query patterns
- **Redis** for API response caching and Celery broker
- **Celery Beat** for scheduled ingestion (justified in DECISIONS.md)
- **Bulk parquet loading** with batch deduplication for ~1M row performance
- **Structured JSON logging** for ingestion jobs and slow-request warnings (>200ms)

## Observability

- Ingestion worker logs: `ingestion_start`, `ingestion_end`, `ingestion_error`
- API webhook logs: `webhook_ingest`
- Slow request middleware warns on requests exceeding `SLOW_QUERY_THRESHOLD_MS` (default 200ms)
- All logs use JSON format via Python's `logging` module

## Frontend Features

- Sortable rate comparison table (by rate, provider, last updated)
- 30-day line chart for selected provider + rate type
- Auto-refresh every 60 seconds without page reload
- Visible loading and error states with retry
- Responsive layout (375px+)
