# DECISIONS.md

Engineering decisions for the Rate Tracker assessment.

## Assumptions

### 1. Seed file simulates scraped data

The parquet file includes `source_url` and `raw_response_id` fields as if data were fetched over HTTP. The `seed_data` command loads from parquet; `scraper.py` handles HTTP transport and `parser.parse_scrape_payload()` normalizes scrape responses (tested with mocked HTTP in `test_scraper.py`).

**Example — a row in the seed file looks like a scrape result:**

```json
{
  "provider": "Chase",
  "rate_type": "5yr_arm_mortgage",
  "rate_value": 6.608,
  "source_url": "https://www.chase.com/rates/5yr_arm_mortgage",
  "raw_response_id": "b86e6b3a-ce03-4e8b-a342-2906a00b119e"
}
```

**How the app uses this:**

| Path | What it does |
|------|--------------|
| `python manage.py seed_data` | Reads parquet in bulk (assessment requirement) |
| `rates/services/scraper.py` | HTTP transport (timeouts, 503 errors) |
| `rates/services/parser.py` | `parse_scrape_payload()` — normalizes HTTP body to parsed record |
| pytest (`test_scraper.py`) | Mocks HTTP and verifies parsed output matches a known fixture |

In production, live URLs would be scraped on a schedule. For the assessment, parquet is the stand-in dataset with the same shape.

---

### 2. Provider names should be canonicalized at ingestion

The seed contains casing variants (`hsbc`, `Hsbc`, `HSBC`). I normalize to a canonical display name at ingestion time rather than at query time, so API responses are consistent.

**Example — seed input:**

```
Row 1:  provider = "hsbc"
Row 2:  provider = "Hsbc"
Row 3:  provider = "HSBC"
```

**After `normalize_provider_name()`:**

```
All three → name: "HSBC", normalized_name: "hsbc"  (single Provider row)
```

**API response always shows:**

```json
{ "provider": "HSBC", "rate_type": "savings_1yr_fixed", "rate_value": "4.7647" }
```

**Alternative rejected:** normalize in every SQL query (`LOWER(provider)`). That is slower, error-prone, and inconsistent across endpoints.

---

### 3. Duplicate business keys keep the latest observation

~97% of rows share `(provider, rate_type, effective_date)`. I deduplicate during parquet batch loading (keep latest `ingestion_ts`) and use `external_id` uniqueness for idempotent re-runs.

**Example — three parquet rows with the same business key:**

| provider | rate_type | effective_date | ingestion_ts | rate_value |
|----------|-----------|----------------|--------------|------------|
| Chase | 30yr_fixed_mortgage | 2025-05-15 | 2025-05-15 08:00 | 6.50 |
| Chase | 30yr_fixed_mortgage | 2025-05-15 | 2025-05-15 14:30 | 6.55 |
| Chase | 30yr_fixed_mortgage | 2025-05-15 | 2025-05-16 09:00 | 6.48 |

**During batch load:**

```python
df.sort_values("ingestion_ts").drop_duplicates(
    subset=["provider", "rate_type", "effective_date"],
    keep="last",
)
```

**Only this row is inserted:**

```
Chase | 30yr_fixed_mortgage | 2025-05-15 | 2025-05-16 09:00 | 6.48
```

~972K of ~1M seed rows are duplicates on this business key. Loading all would bloat the DB without adding information. `external_id` uniqueness separately prevents re-inserting the same raw payload on re-run.

---

### 4. Invalid rates are stored as partial records

Rows with null or non-positive `rate_value` are persisted with `parse_status=partial` and `rate_value=NULL`, excluded from API read endpoints. This supports replay without data loss.

Rows missing required fields (`rate_type`, `effective_date`, `ingestion_ts`) but with a provider are stored with `parse_status=failed` during bulk/parquet ingest. Webhook ingest rejects them with `400` before persistence.

**Example — seed row with null rate:**

```json
{
  "provider": "Chase",
  "rate_type": "30yr_fixed_mortgage",
  "rate_value": null,
  "effective_date": "2025-03-01",
  "raw_response_id": "bad-001"
}
```

**What gets stored:**

```
rates_rawresponse:  parse_status = "partial", error_message = "Invalid or missing rate_value"
rates_rate:         rate_value = NULL  (linked to raw response)
```

**What the API returns:**

```
GET /api/rates/latest  → this row is EXCLUDED (WHERE rate_value IS NOT NULL)
```

The raw payload is preserved so an engineer can inspect `raw_body`, fix the parser, and replay `bad-001` without re-scraping. There are ~215 such rows in the seed (200 null + 15 non-positive).

---

### 5. Celery Beat re-processes the seed file on schedule

In production this would call live provider URLs; for the assessment, scheduled ingestion re-runs parquet loading idempotently to demonstrate the scheduler wiring.

**Example — every 15 minutes:**

```
Celery Beat triggers → run_scheduled_ingestion task
                     → reads /data/rates_seed.parquet
                     → skips existing external_id values (idempotent)
```

**Example log output on second run:**

```json
{"event": "scheduled_ingestion_end", "inserted_rates": 0, "skipped_duplicates": 32930}
```

**In production this would be:**

```
Celery Beat → fetch https://chase.com/rates → parse → store
```

Using parquet for the demo avoids dependency on external sites being up during review.

---

## Idempotency Strategy

The seed file has four categories of duplication/quality issues:

| Issue | Count (approx.) | Handling |
|-------|-----------------|----------|
| Duplicate `(provider, rate_type, effective_date)` | ~972K | Pre-dedupe per batch: sort by `ingestion_ts`, keep last |
| Duplicate `raw_response_id` | 0 | `external_id` UNIQUE + `get_or_create` / `ignore_conflicts` on bulk insert |
| Invalid `rate_value` (null or ≤0) | 215 | Store as `partial` raw response; skip from read APIs |
| Provider casing variants | 3 variants of HSBC | `normalized_name` lookup table at ingestion |

### Example — re-run safety for `seed_data`

```
Run 1: external_id "abc-123" → inserted  (inserted_rates += 1)
Run 2: external_id "abc-123" → skipped   (skipped_duplicates += 1)
```

Running `python manage.py seed_data` multiple times does not create duplicate rates.

### Example — webhook idempotency

Full live demo (auth, validation, cache bust, structured errors): **[INGEST_WEBHOOK.md](INGEST_WEBHOOK.md)**

```bash
# First call
curl -X POST http://localhost:8000/api/rates/ingest \
  -H "Authorization: Bearer $INGEST_BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "Chase",
    "rate_type": "30yr_fixed_mortgage",
    "rate_value": "6.75",
    "effective_date": "2025-06-01",
    "raw_response_id": "webhook-001"
  }'
# → 201 Created

# Same payload again
# → 200 { "message": "Duplicate record — idempotent no-op", "status": "duplicate" }
```

### How schema and idempotency connect

```
Parquet row: { provider: "hsbc", rate_value: null, raw_response_id: "x1" }
  ├─ Assumption 2: canonicalize → Provider(name="HSBC")
  ├─ Assumption 4: partial record → RawResponse(parse_status="partial")
  ├─ Schema: rates_rate.rate_value = NULL
  └─ API: excluded from /latest, but preserved for replay

Parquet row: { provider: "Chase", same business key, older ingestion_ts }
  ├─ Assumption 3: dedupe batch → dropped (newer row kept)
  └─ Schema: composite unique allows different ingestion_ts if both were kept

Re-run seed_data
  ├─ Idempotency: external_id UNIQUE → 0 new rows
  └─ Stats: skipped_duplicates = total existing count
```

---

## Conscious Tradeoff: Celery Beat over cron

**Chose Celery Beat** over a host-level cron job.

### What we chose

```
docker-compose.yml:
  celery-worker   → executes tasks
  celery-beat     → schedules every 15 min
  redis           → message broker (shared with cache)
```

**Example scheduled run (first time after seed):**

```json
{"event": "scheduled_ingestion_start", "job_id": "abc...", "path": "/data/rates_seed.parquet"}
{"event": "scheduled_ingestion_end", "inserted_rates": 0, "skipped_duplicates": 32930}
```

### Alternative: cron inside the container

```cron
*/15 * * * * python manage.py seed_data
```

| | Celery Beat | cron |
|---|-------------|------|
| Retry on failure | ✅ automatic (max 3 retries) | ❌ manual |
| Structured JSON logging | ✅ built-in | ❌ separate setup |
| Scales to N workers | ✅ | ❌ one job at a time |
| Extra containers | ❌ worker + beat | ✅ none |
| Docker-native | ✅ no host cron needed | ⚠️ requires cron in image |

- **Why Celery:** Keeps scheduling inside Docker Compose with no host dependencies; shares Redis broker with cache; retries and structured logging come free.
- **Why not cron:** Simpler for a toy project, but lacks visibility, retry semantics, and doesn't scale to multiple workers.
- **Constraint:** 48-hour window — Celery adds containers but matches how Marketplace-style systems run background jobs.

---

## One Thing I'd Change With More Time

### Primary: materialized view or denormalized `latest_rates` table

**Current approach:**

`GET /api/rates/latest` on cache miss runs:

```sql
DISTINCT ON (provider_id, rate_type) ...
ORDER BY effective_date DESC, ingestion_ts DESC
```

Across ~30K deduplicated rows, with Redis cache (60s TTL).

**Example under load:**

```
1000 requests/min, cache expires every 60s
→ ~17 expensive DB queries/sec on cache miss path
```

**Proposed improvement:**

```
latest_rates table (denormalized, refreshed on every ingest):

┌──────────┬─────────────────────┬────────────┬──────────────┐
│ provider │ rate_type           │ rate_value │ updated_at   │
├──────────┼─────────────────────┼────────────┼──────────────┤
│ Chase    │ 30yr_fixed_mortgage │ 6.75       │ 2025-06-01   │
│ HSBC     │ savings_1yr_fixed   │ 4.76       │ 2025-01-12   │
└──────────┴─────────────────────┴────────────┴──────────────┘

Refreshed via Celery signal after each ingest
→ GET /latest becomes SELECT * FROM latest_rates  (O(1) per row)
→ cache invalidation simplifies to a single table refresh
```

### Secondary: WebSocket push instead of 60-second polling

**Current frontend behavior:**

```
Every 60 seconds → fetch /api/rates/latest
(even when nothing has changed)
```

**Example waste:**

```
Dashboard open for 1 hour = 60 API calls
Only 1 ingest event occurred = 59 unnecessary calls
```

**Proposed improvement:**

```
POST /api/rates/ingest succeeds
  → server pushes WebSocket event: { "event": "rates_updated" }
  → dashboard refreshes immediately
  → no polling when idle
```

This would reduce API load and give true real-time updates when ingest webhooks fire.

### Tertiary: JWT for ingest authentication (replacing static bearer secret)

**Current approach (assessment requirement 2B):**

Ingest uses DRF `BearerTokenAuthentication` with a **single shared secret** from `INGEST_BEARER_TOKEN`:

```http
Authorization: Bearer dev-ingest-token-change-me
```

Validation is string equality — no expiry, no per-client identity, no scopes. Read endpoints remain `AllowAny`. Staff session login on `/api-auth/login/` is a dev-only convenience for the browsable API, not production ingest auth.

**Why this is correct for the take-home:**

- Satisfies “ingest requires bearer token, GET works without auth”
- No external auth service (Auth0, Cognito, etc.)
- Simple for one webhook caller or demo `curl`

**Example limitation at scale:**

```
Partner A and Partner B both use the same INGEST_BEARER_TOKEN
  → cannot revoke one without rotating for both
  → no audit trail of which client ingested a row
  → leaked token is valid until manual env rotation
```

**Proposed improvement:**

Replace the static secret with **signed JWTs** (still sent as `Authorization: Bearer <jwt>` — Bearer is the scheme, JWT is the token format):

```
POST /api/rates/ingest
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
         │
         ├─ iss: "rate-tracker"
         ├─ sub: "partner-chase-webhook"
         ├─ scope: "rates:ingest"
         └─ exp: 1h
```

Implementation sketch (still no external IdP required for v1):

| Piece | Approach |
|-------|----------|
| Issue tokens | Internal admin endpoint or CLI (`manage.py issue_ingest_token --client chase`) |
| Verify | DRF auth class using `PyJWT` + `INGEST_JWT_SECRET` (or RS256 key pair) |
| Revoke | Short TTL (15–60 min) + optional denylist in Redis for compromised tokens |
| Multi-tenant | `sub` / `client_id` claim logged on each ingest for audit |

Read endpoints stay public; only ingest moves from static bearer → JWT. Webhook callers would fetch or receive a JWT instead of a forever-shared string.

---

## Caching Strategy

`GET /api/rates/latest` is cached in Redis. History and ingest endpoints are not cached.

### Pattern: Cache-Aside (lazy loading)

| Phase | What happens |
|-------|--------------|
| **Read hit** | `LatestRatesCacheService` returns serialized JSON from Redis |
| **Read miss** | Query Postgres → serialize → `cache.set()` with 60s TTL |
| **Write (ingest)** | Persist to Postgres only — cache is **not** updated on write |

This is **not** Write-Through (no synchronous cache+DB write), **not** Write-Back (no async DB flush from cache), and **not** pure Write-Around as the overall pattern — reads are explicitly cache-aside. Writes follow **write-around behavior**: ingest skips Redis and invalidates instead.

### Invalidation: epoch bump (O(1))

On every successful ingest (`IngestionService` → `invalidate_rate_caches()`):

```
INCR rates:latest:epoch
```

Cache keys include the epoch: `rates:latest:{epoch}:{type|all}`. After ingest, the epoch increments, old keys are orphaned, and the next read repopulates under the new epoch. Stale entries expire via TTL — no `KEYS` scan or `delete_pattern`.

**Example:**

```
Epoch 0: GET /latest → miss → DB → set rates:latest:0:all
Epoch 0: GET /latest → hit  (cached: true)

Ingest completes → INCR epoch to 1

Epoch 1: GET /latest → miss → DB → set rates:latest:1:all
(rates:latest:0:all still in Redis but unreachable — expires in ≤60s)
```

### Eviction

Eviction is **when stale entries leave Redis**. This app uses two mechanisms — one active (logical), one passive (physical):

| Mechanism | Type | When | What |
|-----------|------|------|------|
| **TTL (60s)** | Passive / time-based | Every `cache.set()` on read miss | Redis `EXPIRE` removes the key after 60 seconds with no access |
| **Epoch bump** | Active / logical | Every ingest | Old keys are **immediately unreachable** (wrong epoch in key); Redis deletes them when their TTL fires |
| **Epoch key** | Never evicted | `rates:latest:epoch` set with `timeout=None` | Stays in Redis permanently — single integer counter |

We do **not** use application-level **LRU** or **LFU** — the keyspace is tiny (one entry per `?type=` filter × epoch). Redis `maxmemory-policy` is not configured in Docker Compose (demo default: no memory cap); in production you would set `maxmemory` + `allkeys-lru` as a safety net.

**How TTL and epoch work together:**

```
No ingest for 60s     → TTL expires → key physically removed from Redis
Ingest before TTL     → epoch bumps → key logically dead, TTL cleans up within ≤60s
Steady read traffic   → cache refreshed on miss; TTL resets on each set()
```

**What we deliberately avoid:**

- **`delete_pattern` / `KEYS` scan** — O(n) over keyspace; replaced by epoch + TTL
- **Manual delete per key** — would require tracking every `?type=` variant

### Why this combination

- **Cache-Aside:** Simple, app-controlled; fits read-heavy `/latest` with infrequent ingest
- **Epoch invalidation:** Cheap bust across all `?type=` variants without tracking individual keys
- **Write-around on ingest:** Avoids stale partial cache updates when bulk parquet loads insert thousands of rows

### Code locations

| File | Role |
|------|------|
| `rates/services/latest_rates_service.py` | Cache-aside read path |
| `rates/services/cache.py` | Epoch key, key builder, invalidation |
| `rates/services/ingestion.py` | Calls invalidation after persist |

---

## Architecture — SOLID

| Principle | How it is applied |
|-----------|-------------------|
| **S — Single Responsibility** | `parser` transforms data, `scraper` handles HTTP transport, `RateWriter` persists, `IngestionService` orchestrates, views handle HTTP only |
| **O — Open/Closed** | New data sources implement `RateRecordSource` (Protocol) without modifying `IngestionService` |
| **L — Liskov Substitution** | `ParquetRateSource` is substitutable anywhere a `RateRecordSource` is expected |
| **I — Interface Segregation** | Thin `RateRecordSource` protocol; views depend on focused `LatestRatesCacheService` / `RateHistoryService` |
| **D — Dependency Inversion** | Services accept `RateRepository`, `RateWriter`, and cache invalidators via constructor injection (defaults provided) |

---

## Design Patterns

| Pattern | Location | Purpose |
|---------|----------|---------|
| **Repository** | `rates/repositories/rate_repository.py` | Encapsulates ORM queries |
| **Strategy** | `rates/services/sources.py` | Pluggable record sources (parquet, HTTP URL) |
| **Factory Method** | `rates/services/sources.py` (`create_rate_source`) | Selects concrete source from path without changing callers |
| **Value Object** | `rates/services/parsed_rate.py` (`ParsedRate`) | Typed domain record replacing raw dicts through parser → writer |
| **Adapter** | `rates/services/parser.py` (`parse_scrape_payload`) | Maps HTTP scrape responses to parsed records |
| **Facade** | `rates/services/latest_rates_service.py` | Cache-aside + serialization for latest rates |
| **Epoch invalidation** | `rates/services/cache.py` | O(1) cache bust via INCR on ingest; keys include epoch, stale entries TTL out |
| **Typed exceptions** | `rates/services/exceptions.py` | Explicit error handling instead of string matching |

---

## Frontend (React SOLID)

| Principle | Location |
|-----------|----------|
| **SRP** | Custom hooks (`useRateFilters`, `useLatestRates`, `useRateHistory`, `useIngestedRates`, `useSortableRates`) each own one concern |
| **DIP** | `RatesApiClient` in `interfaces/ratesApiClient.ts` — hooks accept injectable client (default in `lib/api.ts`) |
| **Pure functions** | `lib/sortRates.ts`, `lib/format.ts`, `lib/rates.ts`, `lib/history.ts`, `lib/errors.ts` — testable without React |
| **Composition** | `DashboardClient.tsx` wires hooks + presentational components; filters default to `""` via `useState` |

---

## Testing

| Layer | Location | Needs Docker? |
|-------|----------|---------------|
| Parser / writer unit tests | `test_parser.py`, `test_services.py` | No |
| HTTP scrape transport + payload parsing | `test_scraper.py` | No |
| API integration tests | `test_api.py` | Yes (Postgres + Redis via Compose) |
| Frontend unit tests | `sortRates.test.ts`, `rates.test.ts`, `history.test.ts` (Vitest) | No |

`make test` runs the full suite inside Compose. Without Docker, run the unit-test rows above locally; API tests require the database.

---

## Production mapping (interview framing)

This take-home runs locally via Docker Compose. In a Forbes Advisor / Marketplace production stack, the same boundaries map as follows:

| Local component | Production analogue |
|-----------------|---------------------|
| Structured JSON logs (`rates.ingestion`, slow-request middleware) | **CloudWatch** (or Datadog) log groups + metric filters on `ingestion_end`, `ingestion_error` |
| `RawResponse` + `parse_status` | **Data lineage** — immutable source payload, replay, and quality flags (`success` / `partial` / `failed`) |
| Redis cache-aside + epoch invalidation | ElastiCache Redis; same key pattern, TTL, and INCR invalidation |
| Celery Beat (15 min parquet ingest) | EventBridge / cron → worker task or Step Functions for scheduled pulls |
| `ingest_url` / webhook POST | API Gateway + Lambda or internal service for partner webhooks |
| Django admin 24h filter + `date_hierarchy` | Operator/debug UI; production would add read-only analytics or Metabase on Postgres |
| GitHub Actions CI | Same pipeline extended with deploy stages (ECS/EKS), image scan, and smoke tests |

---
