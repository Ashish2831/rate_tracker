# Ingest Webhook — Demo Guide

`POST /api/rates/ingest` is an authenticated webhook endpoint. It accepts JSON matching the rate data model, validates strictly, writes to PostgreSQL, invalidates the latest-rates cache, and returns structured errors (400/403) instead of unhandled 500s for bad input.

Use this guide to demonstrate each requirement live (terminal + browser) or in a review walkthrough.

---

## Prerequisites

```bash
make up-lite
# or: docker compose up -d postgres redis backend frontend

export TOKEN="dev-ingest-token-change-me"   # INGEST_BEARER_TOKEN from .env
export API="http://localhost:8000/api"
```

---

## Requirement checklist

| Requirement | Demo |
|-------------|-------------------|
| Authenticated webhook | curl without / with `Authorization: Bearer` |
| JSON matches data model | Valid payload → 201 with rate fields |
| Validates strictly | Bad payload → **400** + field-level `errors` |
| Writes to DB | Row visible via `/api/rates/latest` or Django admin |
| Invalidates cache | `"cached": false` on first GET after ingest |
| Structured errors, not 500s | Show 400/403 JSON bodies for invalid input |

---

## 1. Authentication required

**No token → 403:**

```bash
curl -s -w "\nHTTP %{http_code}\n" -X POST "$API/rates/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "Chase",
    "rate_type": "30yr_fixed_mortgage",
    "rate_value": "6.75",
    "effective_date": "2025-06-01"
  }'
```

Expected:

```json
{"detail":"Authentication credentials were not provided."}
HTTP 403
```

**Wrong token → 403:**

```bash
curl -s -w "\nHTTP %{http_code}\n" -X POST "$API/rates/ingest" \
  -H "Authorization: Bearer wrong-token" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "Chase",
    "rate_type": "30yr_fixed_mortgage",
    "rate_value": "6.75",
    "effective_date": "2025-06-01"
  }'
```

Read endpoints (`GET /api/rates/latest`, `/history`, etc.) remain public — only ingest requires auth.

---

## 2. Valid JSON → 201 + DB write

```bash
curl -s -w "\nHTTP %{http_code}\n" -X POST "$API/rates/ingest" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "Chase",
    "rate_type": "30yr_fixed_mortgage",
    "rate_value": "6.99",
    "effective_date": "2025-06-01",
    "raw_response_id": "demo-webhook-001",
    "currency": "USD"
  }'
```

Expected: **HTTP 201** with a structured rate object (`provider`, `rate_type`, `rate_value`, `effective_date`, `ingestion_ts`, `currency`).

**Verify persistence:**

```bash
curl -s "$API/rates/latest?provider=Chase&type=30yr_fixed_mortgage" | python3 -m json.tool
```

Or open Django admin → **Rates** and search for the new row / `demo-webhook-001`.

**Browsable API (optional):**

1. Open http://localhost:8000/api/rates/ingest
2. Log in at http://localhost:8000/api-auth/login/ (staff user — `make createsuperuser`)
3. POST via the HTML form

---

## 3. Strict validation → 400 with structured errors

Validation runs in `IngestRateSerializer` before any DB write. Invalid payloads return **400** with an `errors` object — not 500.

**Negative rate:**

```bash
curl -s -w "\nHTTP %{http_code}\n" -X POST "$API/rates/ingest" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "Chase",
    "rate_type": "savings_easy_access",
    "rate_value": "-1.00",
    "effective_date": "2025-06-01"
  }'
```

Expected:

```json
{
  "errors": {
    "rate_value": ["rate_value must be greater than zero."]
  }
}
HTTP 400
```

**Missing required fields:**

```bash
curl -s -w "\nHTTP %{http_code}\n" -X POST "$API/rates/ingest" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"provider": "Chase"}'
```

Expected: **400** with `"errors"` listing missing `rate_type`, `rate_value`, `effective_date`, etc.

---

## 4. Idempotent duplicate → 200

Re-post the **same** payload (same `raw_response_id`):

```bash
# Repeat the successful curl from section 2
```

Expected:

```json
{"message":"Duplicate record — idempotent no-op","status":"duplicate"}
HTTP 200
```

Webhook retries are safe — the same external id will not double-insert.

---

## 5. Cache invalidation after ingest

```bash
# Warm cache
curl -s "$API/rates/latest" | python3 -c "import sys,json; d=json.load(sys.stdin); print('cached:', d['cached'])"

# Ingest (use a NEW raw_response_id and different rate_value)
curl -s -X POST "$API/rates/ingest" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "Chase",
    "rate_type": "30yr_fixed_mortgage",
    "rate_value": "7.01",
    "effective_date": "2025-06-02",
    "raw_response_id": "demo-webhook-002"
  }'

# First read after ingest should miss cache (epoch bumped)
curl -s "$API/rates/latest" | python3 -c "import sys,json; d=json.load(sys.stdin); print('cached:', d['cached'])"
```

Expected flow:

1. First GET → `"cached": false`, then `"cached": true`
2. After ingest → `"cached": false` again (fresh data from DB)
3. Second GET → `"cached": true`

Ingest calls `invalidate_rate_caches()` — Redis epoch `INCR` orphans old keys under the previous epoch.

---

## 6. Automated tests

```bash
make test-backend
# or:
docker compose exec backend pytest rates/tests/test_api.py -k ingest -v
```

| Test | Proves |
|------|--------|
| `test_ingest_requires_auth` | No token → 401/403 |
| `test_ingest_with_valid_token` | Valid bearer → 201 |
| `test_ingest_validation_error` | Bad payload → 400 + `errors` |
| `test_ingest_with_staff_session` | Staff session works in dev (browsable API) |

---

## Request body reference

| Field | Required | Notes |
|-------|----------|-------|
| `provider` | Yes | Bank name (normalized at ingest) |
| `rate_type` | Yes | e.g. `30yr_fixed_mortgage` |
| `rate_value` | Yes | Decimal > 0 |
| `effective_date` | Yes | ISO date `YYYY-MM-DD` |
| `ingestion_ts` | No | Defaults to now |
| `currency` | No | Defaults to `USD` |
| `source_url` | No | Stored on `RawResponse` |
| `raw_response_id` | No | Idempotency key (recommended for webhooks) |

---

## Implementation map

| Concern | Location |
|---------|----------|
| Bearer auth | `rates/api/authentication.py` → `BearerTokenAuthentication` |
| Permission | `rates/api/permissions.py` → `HasBearerToken` |
| Validation | `rates/api/serializers.py` → `IngestRateSerializer` |
| View / error handling | `rates/api/views.py` → `IngestRateView` |
| Persist + cache bust | `rates/services/ingestion.py` → `ingest_from_api_payload` + `invalidate_rate_caches` |

---

## One-line summary

> POST `/api/rates/ingest` requires a bearer token, validates with DRF serializers and returns field-level 400s, persists via `IngestionService`, busts the latest-rates cache with an epoch bump, and treats duplicate webhooks as idempotent 200s.
