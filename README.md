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

### Ingest from a live HTTP URL

```bash
docker compose exec backend python manage.py ingest_url https://example.com/rate.json
```

Uses `HttpRateSource` (scraper + `parse_scrape_payload` adapter). Useful for one-off live source tests; scheduled ingest still uses parquet via Celery.

### Run tests

Requires the stack running (`make up`). Runs backend pytest (including API integration tests against Postgres/Redis) and frontend Vitest:

```bash
make test
# or individually:
make test-backend
make test-frontend
```

Without Docker, unit tests only (26 backend + 20 frontend — API tests need Postgres):

```bash
cd backend && python3 -m pytest rates/tests/test_parser.py rates/tests/test_services.py rates/tests/test_scraper.py
cd frontend && npm test
```

### Tail logs

```bash
make logs
```

### Makefile commands

| Command | Description |
|---------|-------------|
| `make up` | Build and start all containers |
| `make up-lite` | Postgres, Redis, backend, frontend only (no Celery) |
| `make down` | Stop containers |
| `make build` | Rebuild Docker images |
| `make seed` | Load parquet into raw tables + run dbt marts |
| `make dbt` | Re-run dbt mart models only (incremental) |
| `make dbt-full` | Rebuild all dbt models from scratch |
| `make test` | Run backend pytest + frontend Vitest |
| `make test-backend` | Backend pytest only (in Docker) |
| `make test-frontend` | Frontend Vitest only (in Docker) |
| `make migrate` | Run Django migrations |
| `make shell` | Django shell in backend container |
| `make frontend-deps` | Sync frontend `node_modules` after `package.json` changes |
| `make createsuperuser` | Create Django admin user |
| `make logs` | Follow container logs |

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/rates/latest` | None | Latest rate per provider. Optional `?provider=` and `?type=` filters. Cache-aside (Redis, 60s TTL, epoch invalidation on ingest). |
| GET | `/api/rates/history` | None | Paginated history. Requires `?provider=` and `?type=`. Optional `?from=` and `?to=`. |
| GET | `/api/rates/filters` | None | Provider and rate-type options for dashboard filters. |
| GET | `/api/rates/ingested` | None | Rates ingested in a 24-hour window. Optional `?provider=`, `?type=`, `?from=`, `?to=`. |
| POST | `/api/rates/ingest` | Bearer token | Webhook ingest. Set `INGEST_BEARER_TOKEN` in `.env`. |

### Ingest webhook demo

Full walkthrough (auth, validation, DB write, cache invalidation, idempotency): **[docs/INGEST_WEBHOOK.md](docs/INGEST_WEBHOOK.md)**

Quick example:

```bash
curl -X POST http://localhost:8000/api/rates/ingest \
  -H "Authorization: Bearer dev-ingest-token-change-me" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "Chase",
    "rate_type": "30yr_fixed_mortgage",
    "rate_value": "6.75",
    "effective_date": "2025-06-01",
    "raw_response_id": "webhook-demo-001"
  }'
```

## Architecture

```
Parquet / webhook
       │
       ▼
  Django ingest (raw-only) ──► rates_rawresponse
       │
       ▼
  dbt run (stg → int → mart) ──► analytics.mart_rates / mart_latest_rates
       │
       ▼
 Django REST API ◄── Redis cache (reads marts)
       │
       ▼
 Next.js Dashboard (auto-refresh 60s)
```

`make seed` loads parquet into raw tables and runs dbt automatically. Manual refresh: `make dbt`.

See [docs/SCHEMA.md](./docs/SCHEMA.md) for database design and [docs/DECISIONS.md](./docs/DECISIONS.md) for engineering rationale and SOLID/design-pattern notes.

## Architecture (SOLID)

### Backend

```
API Views (HTTP only)
    ├── LatestRatesCacheService  → RateRepository + Redis (Cache-Aside + epoch invalidation)
    ├── RateHistoryService       → RateRepository
    ├── IngestedRatesService     → RateRepository
    ├── RateFiltersService       → RateRepository
    ├── IngestionService         → RateWriter + RateRecordSource (Strategy)
    └── pagination.py            → shared history/ingested pagination (PaginatedRateListMixin)

RateWriter (raw persist)  →  rates_rawresponse only
DbtRunner               →  stg/int/mart SQL transforms after ingest
ParquetRateSource       →  implements RateRecordSource (Open/Closed)
HttpRateSource          →  live HTTP JSON ingest via scraper + adapter
create_rate_source()    →  Factory Method for source selection
parsed_rate.py          →  ParsedRate value object (webhook validation)
parser.py               →  parse_scrape_payload() maps HTTP body → record (Adapter)
RateRepository          →  reads analytics.mart_* (dbt-built)
```

### Frontend

```
QueryProvider (TanStack Query)
DashboardClient.tsx (thin shell — delegates to useDashboard + tab panels)
    ├── useDashboard          → filters, tab-scoped queries, coordinated refresh
    ├── useRateFilters        → filter dropdown options (cached 5 min)
    ├── useLatestRates        → fetch + auto-refresh + loading/error (SRP)
    ├── useRateHistory        → chart data fetch + day aggregation (SRP)
    ├── useIngestedRates      → 24h ingested table (SRP)
    └── useSortableRates      → sort state → sortRates() pure fn (SRP)

components/dashboard/     → header, stats, filters, tab bar, SortableRatesTab, per-tab panels
components/RateTable/     → sortable table + column header subcomponents
lib/api.ts                → ratesApiClient (DIP)
lib/apiPagination.ts      → multi-page fetch + next-link normalization
lib/queryKeys.ts          → TanStack Query cache keys
lib/history.ts            → aggregateHistoryByDay (chart)
lib/rates.ts              → groupRatesByProvider, bestRateFromRates
lib/sortRates.ts          → pure sort utilities
lib/format.ts             → formatRateType(), formatRateValue()
lib/errors.ts             → getErrorMessage() shared by hooks
constants/dashboardTabs.ts → tab metadata (labels, titles, descriptions)
interfaces/               → shared types (rates, hooks, RatesApiClient)
hooks/                    → data-fetching and sort-state hooks
```

## Environment Variables

Copy `.env.example` to `.env`. All required variables are documented there. The application fails fast at startup if any required variable is missing.

## Project Structure

```
├── backend/           # Django + DRF + Celery
├── dbt/               # dbt models (staging → marts)
├── frontend/          # Next.js dashboard
├── data/              # rates_seed.parquet
├── docs/              # SCHEMA.md, DECISIONS.md, AWS_DEPLOYMENT.md, INGEST_WEBHOOK.md
├── infra/terraform/   # AWS infrastructure
├── scripts/           # aws/*.sh
├── docker-compose.yml
└── Makefile
```

## Architectural Choices

- **Django + DRF** for typed API with built-in admin and migrations
- **PostgreSQL** with composite indexes tuned for the three required query patterns
- **Redis** for API response caching (cache-aside + epoch invalidation) and Celery broker
- **Celery Beat** for scheduled ingestion (justified in [docs/DECISIONS.md](./docs/DECISIONS.md))
- **Bulk parquet loading** with batch deduplication for ~1M row performance
- **Structured JSON logging** for ingestion jobs and slow-request warnings (>200ms)

## Caching

Only `GET /api/rates/latest` is cached.

| Aspect | Approach |
|--------|----------|
| **Read pattern** | Cache-Aside — check Redis, on miss query Postgres and populate cache |
| **Write pattern** | Write-around — ingest writes DB only, does not update cache |
| **Invalidation** | Epoch bump (`INCR rates:latest:epoch`) on every ingest; keys include epoch |
| **Eviction** | TTL (60s passive) + epoch orphan cleanup; no LRU/LFU (small keyspace) |
| **TTL** | 60 seconds per cached response |

See [docs/DECISIONS.md](./docs/DECISIONS.md#caching-strategy) for flow examples and tradeoffs.

## Observability

- Ingestion worker logs: `ingestion_start`, `ingestion_end`, `ingestion_error`
- API webhook logs: `webhook_ingest`
- Slow request middleware warns on requests exceeding `SLOW_QUERY_THRESHOLD_MS` (default 200ms)
- All logs use JSON format via Python's `logging` module

## Frontend Features

- Four tabbed views: dashboard overview, latest rates table, 30-day history chart, ingested (24h) table
- Server-side provider and rate-type filters with TanStack Query caching
- Sortable rate comparison tables (by rate, provider, last updated)
- 30-day line chart for selected provider + rate type
- Auto-refresh every 60 seconds without page reload
- Visible loading and error states with retry
- Responsive layout (375px+)

## CI

GitHub Actions (`.github/workflows/ci.yml`) runs on push/PR to `main`:

- **Backend:** Postgres + Redis services, migrations, full pytest suite (38 tests)
- **Frontend:** ESLint, Vitest, production `next build`

CI sets `DBT_RUN_AFTER_INGEST=false`; API tests seed mart tables via test helpers instead of running dbt.

## AWS deployment (CI/CD)

Production deployment to **ECS Fargate + RDS + ElastiCache + ALB** in **`ap-south-1` (Mumbai)** with automated deploy on merge to `main`.

The backend image is built from the **repo root** (`docker build -f backend/Dockerfile .`) so the dbt project is baked in at `/dbt`. ECS tasks receive `DBT_PROJECT_DIR`, `DBT_PROFILES_DIR`, and `DBT_RUN_AFTER_INGEST=true`. On startup, `entrypoint.sh` runs `run_dbt --if-missing` so mart tables exist on fresh RDS (empty until seeded).

See **[docs/AWS_DEPLOYMENT.md](./docs/AWS_DEPLOYMENT.md)** for the full guide. Summary:

1. `./scripts/aws/bootstrap-state.sh` — create Terraform remote state
2. `terraform init` + `terraform apply` in `infra/terraform/` — VPC, RDS, Redis, ECS, ALB, ECR
3. Upload seed parquet to S3
4. Push Docker images (`scripts/aws/push-images.sh` or GitHub Deploy)
5. **Run one-off ECS seed task** — required once so `/api/rates/*` has data (health alone is not enough)
6. Set GitHub secret `AWS_ROLE_ARN` (from Terraform output)
7. Push to `main` → **CI** runs tests → **Deploy** builds images, pushes ECR, rolls ECS

**Production 500 on rate APIs?** Health can pass while dbt marts are missing. See [AWS_DEPLOYMENT.md — Troubleshooting](./docs/AWS_DEPLOYMENT.md#troubleshooting).

| Workflow | File | Trigger |
|----------|------|---------|
| CI | `.github/workflows/ci.yml` | Push/PR to `main` |
| Deploy | `.github/workflows/deploy.yml` | CI success on `main`, or manual |

## Submission checklist

Before sending to the reviewer:

- [ ] Private GitHub repo shared with assessors
- [ ] Loom walkthrough (architecture, tradeoffs, demo)
- [ ] `docker compose up --build` verified end-to-end (seed + dashboard)
- [ ] `make test` passes with stack running
- [ ] `.env` uses non-default secrets for any shared environment
