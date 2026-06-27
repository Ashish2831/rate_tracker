# Rate Tracker — Schema Design

## Overview

The schema separates **providers**, **raw ingestion payloads**, and **cleaned rate records**. This supports idempotent re-ingestion, replay of failed parses, and efficient read patterns for the API and dashboard.

```
HTTP / Parquet source
        │
        ▼
  rates_rawresponse   ← "what we actually received"
        │
        ▼
    rates_rate        ← "cleaned business record"
        ▲
        │
  rates_provider      ← "who issued the rate"
```

---

## Tables

### `rates_provider`

| Column | Type | Notes |
|--------|------|-------|
| `id` | bigint PK | Surrogate key |
| `name` | varchar(128) UNIQUE | Display name (canonical casing) |
| `normalized_name` | varchar(128) UNIQUE, indexed | Lowercase key for deduplication |
| `created_at` | timestamptz | Audit |

**Purpose:** Normalize provider name variants (`hsbc`, `Hsbc`, `HSBC`) into a single entity.

#### Example — provider name normalization

The seed file contains three spellings of the same bank:

| Row in parquet | After ingestion |
|----------------|-----------------|
| `provider: "hsbc"` | → `name: "HSBC"`, `normalized_name: "hsbc"` |
| `provider: "Hsbc"` | → same provider row (lookup by `normalized_name`) |
| `provider: "HSBC"` | → same provider row |

Without this table, the dashboard would show three separate "providers" for one bank. With it, all rates link to a single `provider_id`.

```
rates_provider
┌────┬─────────────────┬─────────────────┐
│ id │ name            │ normalized_name │
├────┼─────────────────┼─────────────────┤
│  1 │ HSBC            │ hsbc            │
│  2 │ Chase           │ chase           │
│  3 │ Bank of America │ bank of america │
└────┴─────────────────┴─────────────────┘
```

---

### `rates_rawresponse`

| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid PK | Internal identifier |
| `external_id` | varchar(64) UNIQUE, indexed | `raw_response_id` from source — idempotency key |
| `source_url` | url | Origin of the payload |
| `raw_body` | jsonb | Full raw payload for replay |
| `fetched_at` | timestamptz, indexed | When data was acquired |
| `parse_status` | varchar(16) | `success`, `partial`, `failed` |
| `error_message` | text | Parse/validation errors |
| `created_at` | timestamptz | Audit |

**Purpose:** Store raw responses alongside cleaned records so failed parses can be replayed.

#### Example — successful scrape

Parquet / HTTP input:

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
│ abc-123     │ success      │ { full original JSON preserved }   │ 2025-06-01T12:00:00 │
└─────────────┴──────────────┴────────────────────────────────────┴─────────────────────┘
```

#### Example — partial parse (invalid rate value)

Parquet row with `rate_value: null`:

```
rates_rawresponse
┌─────────────┬──────────────┬─────────────────────────────────────┐
│ external_id │ parse_status │ error_message                       │
├─────────────┼──────────────┼─────────────────────────────────────┤
│ xyz-456     │ partial      │ Invalid or missing rate_value       │
└─────────────┴──────────────┴─────────────────────────────────────┘
```

The raw payload is **kept** so an engineer can fix the parser and replay `xyz-456` later without re-scraping the source URL.

---

### `rates_rate`

| Column | Type | Notes |
|--------|------|-------|
| `id` | bigint PK | Surrogate key |
| `provider_id` | FK → provider | PROTECT on delete |
| `rate_type` | varchar(64), indexed | e.g. `30yr_fixed_mortgage` |
| `rate_value` | decimal(8,4), nullable | Null for partial/failed parses |
| `effective_date` | date, indexed | Business date of the rate |
| `ingestion_ts` | timestamptz, indexed | When record was ingested |
| `currency` | varchar(3) | ISO currency code |
| `raw_response_id` | FK → rawresponse | PROTECT on delete |
| `created_at` | timestamptz | Audit |

**Unique constraint:** `(provider_id, rate_type, effective_date, ingestion_ts)` — prevents exact duplicate snapshots while allowing multiple observations per day.

#### Example — unique constraint in practice

If we used a simpler constraint `UNIQUE (provider_id, rate_type, effective_date)`, only one row per day would be allowed and re-scrape history would be lost. The four-column constraint is more precise:

**Allowed — multiple observations on the same effective date:**

```
Chase | 30yr_fixed_mortgage | 2025-05-15 | 2025-05-15 08:00 | 6.50  ✅
Chase | 30yr_fixed_mortgage | 2025-05-15 | 2025-05-15 14:30 | 6.55  ✅
Chase | 30yr_fixed_mortgage | 2025-05-15 | 2025-05-16 09:00 | 6.48  ✅
```

Same bank, same product, same effective date — but scraped at different times → different snapshots.

**Blocked — exact duplicate snapshot (idempotent re-run):**

```
Chase | 30yr_fixed_mortgage | 2025-05-15 | 2025-05-15 08:00 | 6.50  ✅ first insert
Chase | 30yr_fixed_mortgage | 2025-05-15 | 2025-05-15 08:00 | 6.50  ❌ rejected on re-run
```

When the API asks for the latest rate, it picks the best snapshot with `ORDER BY effective_date DESC, ingestion_ts DESC`. In the example above, `6.48` (ingested 2025-05-16) wins for the 2025-05-15 effective date.

---

## Indexes & Query Patterns

### 1. Latest rate per provider

**Question:** "What is each bank's most recent rate right now?"

```sql
-- Supported by composite index: (provider_id, rate_type, effective_date DESC)
SELECT DISTINCT ON (provider_id, rate_type) *
FROM rates_rate
WHERE rate_value IS NOT NULL
ORDER BY provider_id, rate_type, effective_date DESC, ingestion_ts DESC;
```

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
-- Supported by index: (provider_id, rate_type, effective_date)
SELECT *
FROM rates_rate
WHERE provider_id = 2          -- Chase
  AND rate_type = '30yr_fixed_mortgage'
  AND effective_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY effective_date;
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

**Question:** "What did our ingestion pipeline load between midnight and midnight yesterday?"

```sql
-- Supported by index: (ingestion_ts)
SELECT *
FROM rates_rate
WHERE ingestion_ts >= '2025-06-01 00:00:00'
  AND ingestion_ts <  '2025-06-02 00:00:00';
```

**Example use:** Ops/debugging — verifying that last night's Celery job ingested data as expected.

---

## Tradeoffs

| Decision | Rationale | Example |
|----------|-----------|---------|
| Separate `Provider` table | Enables name normalization without mutating historical rows | `"hsbc"`, `"Hsbc"`, `"HSBC"` all map to one row; old `rates_rate` rows keep `provider_id=1` unchanged |
| `external_id` uniqueness on raw responses | Guarantees idempotent ingestion at the payload level | Row with `raw_response_id: "abc-123"` is inserted once; second ingest of the same ID is skipped |
| Nullable `rate_value` | Preserves partial records for observability/replay | Row with null rate stored (`rate_value = NULL`, `parse_status = partial`) but excluded from API reads |
| Composite unique on rate snapshots | Handles duplicate business keys in seed data by keeping distinct ingestion timestamps | ~972K seed rows share `(provider, rate_type, effective_date)`; distinct `ingestion_ts` values preserve scrape history |
| JSONB for `raw_body` | Flexible storage for varying source formats; supports replay | Chase returns JSON today; another bank may return a different structure tomorrow — JSONB stores both without schema changes |

---

## End-to-end example: one row through the schema

```
Parquet input:
  { provider: "hsbc", rate_value: 4.76, raw_response_id: "8868d928-...", ... }

Step 1 — rates_provider
  → lookup normalized_name "hsbc" → create/find Provider(name="HSBC")

Step 2 — rates_rawresponse
  → insert external_id="8868d928-...", parse_status="success", raw_body={...}

Step 3 — rates_rate
  → insert provider_id=1, rate_type="savings_1yr_fixed", rate_value=4.76, ...

Step 4 — API
  → GET /api/rates/latest includes HSBC row
  → GET /api/rates/history?provider=HSBC&type=savings_1yr_fixed returns time series
```

If the same row is ingested again:

```
Step 2 — rates_rawresponse → external_id already exists → skipped
Step 3 — rates_rate       → no new row created
Stats: skipped_duplicates += 1
```
