-- Staging view: pass-through from rates_rawresponse with stable column names for downstream models.
-- Materialized as view (see dbt_project.yml) — always reflects current raw rows.

select
    id,
    external_id,
    source_url,
    raw_body,       -- JSON snapshot of provider, rate_type, rate_value, dates, etc.
    fetched_at,
    parse_status,   -- success | partial | failed (from webhook path)
    error_message,
    created_at      -- Incremental watermark for int_rates_parsed
from {{ source('rates', 'raw_responses') }}
