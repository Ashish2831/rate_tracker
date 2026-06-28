# Rate Tracker — Schema Design

## Overview

The schema splits **online ingest** (Django) from **warehouse transforms** (dbt). Django writes immutable raw payloads; dbt builds staging → intermediate → mart tables that power the API and dashboard.

```
Parquet / webhook
        │
        ▼
  rates_rawresponse          ← Django raw ingest (public schema)
        │
        ▼  dbt run (after each ingest)
  staging.stg_raw_responses
        │
        ▼
  intermediate.int_rates_parsed
        │
        ▼
  intermediate.int_rates_deduped
        │
        ├── analytics.mart_rates         ← history + ingested queries
        └── analytics.mart_latest_rates  ← GET /latest
        │
        ▼
  Django REST API + Redis cache
```

**Key files:** `dbt/models/`, `rates/services/rate_writer.py`, `rates/repositories/rate_repository.py`

---

## Django-owned raw table

### `rates_rawresponse`

| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid PK | Internal identifier |
| `external_id` | varchar(64) UNIQUE, indexed | `raw_response_id` from source — idempotency key |
| `source_url` | url | Origin of the payload |
| `raw_body` | jsonb | Full parquet/webhook row preserved for replay |
| `fetched_at` | timestamptz, indexed | When data was acquired |
| `parse_status` | varchar(16) | `success`, `partial`, `failed` (webhook validation path) |
| `error_message` | text | Parse/validation errors |
| `created_at` | timestamptz, indexed | Incremental watermark for dbt |

**Purpose:** Immutable raw ingest. Every distinct `external_id` is stored once; re-runs skip duplicates at this layer.

#### Example — parquet row stored as-is

Parquet input:

```json
{
  "provider": "Chase",
  "rate_type": "30yr_fixed_mortgage",
  "rate_value": 6.75,
  "effective_date": "2025-06-01",
  "ingestion_ts": "2025-06-01T12:00:00",
  "raw_response_id": "abc-123",
  "source_url": "https://www.chase.com/rates/30yr_fixed_mortgage"
}
```

Stored as:

```
rates_rawresponse
┌─────────────┬──────────────┬────────────────────────────────────┬─────────────────────┐
│ external_id │ parse_status │ raw_body                           │ fetched_at          │
├─────────────┼──────────────┼────────────────────────────────────┼─────────────────────┤
│ abc-123     │ success      │ { full original row as JSONB }     │ 2025-06-01T12:00:00 │
└─────────────┴──────────────┴────────────────────────────────────┴─────────────────────┘
```

Rows with null or invalid `rate_value` remain in `raw_body`; dbt excludes them from marts (`WHERE rate_value IS NOT NULL`).

---

## dbt layers

### `staging.stg_raw_responses` (view)

Pass-through of `rates_rawresponse` — typed columns for downstream models.

### `intermediate.int_rates_parsed` (incremental table)

Extracts and validates fields from `raw_body`:

| Derived column | Source |
|----------------|--------|
| `provider_name` | `normalize_provider()` macro on `raw_body->>'provider'` |
| `normalized_name` | `lower(trim(provider))` |
| `rate_type`, `rate_value`, `effective_date`, `ingestion_ts`, `currency` | JSON extract + cast |
| `source_created_at` | `rates_rawresponse.created_at` (incremental watermark) |

Incremental: only rows with `created_at` newer than the model's max watermark.

### `intermediate.int_rates_deduped` (incremental table)

One row per `(normalized_name, rate_type, effective_date)` — keeps the observation with the latest `ingestion_ts`.

~852K parsed rows → ~27K deduplicated business keys (seed data has ~97% duplicate keys).

### `analytics.mart_rates` (incremental table)

| Column | Type | Notes |
|--------|------|-------|
| `id` | bigint PK | `hashtext(external_id)` — stable surrogate |
| `provider_name` | varchar(128) | Canonical display name (e.g. `HSBC`) |
| `normalized_name` | varchar(128), indexed | Lowercase lookup key (e.g. `hsbc`) |
| `rate_type` | varchar(64), indexed | e.g. `30yr_fixed_mortgage` |
| `rate_value` | numeric(8,4) | Non-null only (partial rows excluded) |
| `effective_date` | date, indexed | Business date of the rate |
| `ingestion_ts` | timestamptz, indexed | When record was ingested (UTC in DB; window uses `DJANGO_TIME_ZONE`) |
| `currency` | varchar(3) | ISO currency code |
| `external_id` | varchar(64) UNIQUE | Lineage back to raw payload |

**Unique key:** `external_id` (incremental merge).

Powers `GET /api/rates/history` and `GET /api/rates/ingested`.

### `analytics.mart_latest_rates` (table, rebuilt each dbt run)

Same columns as `mart_rates` (except `source_created_at`), one row per `(normalized_name, rate_type)` — latest `effective_date` then `ingestion_ts`.

Powers `GET /api/rates/latest` and filter dropdowns.

#### Example — provider name normalization (in dbt, not Django)

| Row in parquet `raw_body` | `provider_name` | `normalized_name` |
|---------------------------|-------------------|-------------------|
| `"hsbc"` | HSBC | hsbc |
| `"Hsbc"` | HSBC | hsbc |
| `"HSBC"` | HSBC | hsbc |

All three raw payloads may exist in `rates_rawresponse`; dedupe keeps the latest observation per business key in the mart.

---

## Indexes & Query Patterns

### 1. Latest rate per provider

**Question:** "What is each bank's most recent rate right now?"

```sql
-- Pre-computed in analytics.mart_latest_rates (~50 rows)
SELECT provider_name, rate_type, rate_value, effective_date, ingestion_ts, currency
FROM analytics.mart_latest_rates
ORDER BY provider_name, rate_type;
```

Django reads via `MartLatestRate` ORM (unmanaged model). Redis cache-aside (60s TTL) wraps this path.

**Example result** (powers `GET /api/rates/latest`):

| provider | rate_type | rate_value | effective_date |
|----------|-----------|------------|----------------|
| Chase | 30yr_fixed_mortgage | 6.75 | 2025-06-01 |
| HSBC | savings_1yr_fixed | 4.76 | 2025-01-12 |
| Truist | 5yr_arm_mortgage | 6.60 | 2025-05-15 |

---

### 2. Rate change over the last 30 days for a given type

**Question:** "How did Chase's 30-year fixed rate move this month?"

```sql
SELECT provider_name, rate_type, rate_value, effective_date, ingestion_ts
FROM analytics.mart_rates
WHERE normalized_name = 'chase'
  AND rate_type = '30yr_fixed_mortgage'
  AND effective_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY effective_date, ingestion_ts;
```

**Example result** (powers the frontend line chart via `GET /api/rates/history`):

| effective_date | rate_value |
|----------------|------------|
| 2025-05-08 | 6.90 |
| 2025-05-15 | 6.75 |
| 2025-05-22 | 6.60 |
| 2025-05-29 | 6.55 |

---

### 3. All records ingested in a given 24-hour window

**Question:** "What did our ingestion pipeline load in the last 24 hours?"

```sql
SELECT provider_name, rate_type, rate_value, effective_date, ingestion_ts
FROM analytics.mart_rates
WHERE ingestion_ts >= NOW() - INTERVAL '24 hours'
  AND ingestion_ts < NOW()
ORDER BY ingestion_ts DESC;
```

**Example use:** Ops/debugging — verifying recent ingest activity. Powers `GET /api/rates/ingested` (default window uses `DJANGO_TIME_ZONE`, e.g. `Asia/Kolkata`).

---

## Incremental dbt refresh

| Run type | When | Typical duration |
|----------|------|------------------|
| Full refresh (`--full-refresh`) | First seed / `make dbt-full` | ~5s on seed data |
| Incremental | Celery re-run, webhook ingest | ~0.6s when no new raw rows |

Watermark: `rates_rawresponse.created_at` → `int_rates_parsed.source_created_at`.

Commands:

```bash
make seed       # raw load + dbt (auto full-refresh if marts missing)
make dbt        # incremental refresh
make dbt-full   # rebuild all incremental models
```

---

## Tradeoffs

| Decision | Rationale | Example |
|----------|-----------|---------|
| Raw-only Django ingest | Keeps online path simple; transforms versioned in SQL | Webhook writes one `rates_rawresponse` row, dbt builds marts |
| dbt for transforms | Staging/int/mart layering, incremental models, schema tests | Provider normalize + dedupe in `int_rates_*` models |
| Provider columns on mart (not separate table) | Normalization in SQL macro; no Django FK wiring | `"hsbc"`, `"Hsbc"`, `"HSBC"` → `provider_name: HSBC` |
| `external_id` uniqueness on raw | Idempotent ingest at payload level | `raw_response_id: "abc-123"` inserted once; re-run skipped |
| Dedupe in dbt, not Python | All raw rows preserved; business logic in one SQL layer | ~852K raw → ~27K mart rows after dedupe |
| Exclude null `rate_value` from marts | Partial rows stay in raw for replay | Null rate in raw_body → not in `mart_rates` |
| `mart_latest_rates` table rebuild | Only ~50 rows; simpler than incremental latest logic | `/latest` is O(1) per row on cache miss |
| JSONB for `raw_body` | Flexible storage; supports replay without re-scrape | Full parquet row preserved regardless of parse outcome |

---

## End-to-end example: one row through the schema

```
Parquet input:
  { provider: "hsbc", rate_value: 4.76, raw_response_id: "8868d928-...", ... }

Step 1 — Django: rates_rawresponse
  → insert external_id="8868d928-...", raw_body={ full row }, parse_status="success"

Step 2 — dbt: int_rates_parsed
  → extract fields, provider_name="HSBC", normalized_name="hsbc"

Step 3 — dbt: int_rates_deduped
  → keep latest row per (hsbc, rate_type, effective_date)

Step 4 — dbt: analytics.mart_rates + mart_latest_rates
  → rate_value=4.76 available for API reads

Step 5 — API
  → GET /api/rates/latest includes HSBC row
  → GET /api/rates/history?provider=HSBC&type=savings_1yr_fixed returns time series
```

If the same row is ingested again:

```
Step 1 — rates_rawresponse → external_id already exists → skipped
Step 2–4 — dbt incremental → no new source_created_at → MERGE 0 rows
Stats: skipped_duplicates += 1
```

---

## Django migrations

| Migration | Purpose |
|-----------|---------|
| `0001_initial` | Creates `rates_rawresponse` (raw ingest) |
| `0002_unmanaged_mart_models` | Registers `MartRate` / `MartLatestRate` in Django state only (`managed=False`) — tables are created by dbt, not Django |

---

## Legacy note

Earlier iterations used Django-owned `rates_provider` and `rates_rate` tables. Those were removed — all transform logic now lives in dbt marts under the `analytics` schema. Django never creates mart DDL; `python manage.py run_dbt` (or `seed_data`) builds them.
