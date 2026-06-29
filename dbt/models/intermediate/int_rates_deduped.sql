{#
  Dedupe on (normalized_name, rate_type, effective_date).
  Winner: highest ingestion_ts, then external_id desc.
  Incremental: re-rank only keys touched by new parsed rows.
#}
{{
  config(
    materialized='incremental',
    unique_key=['normalized_name', 'rate_type', 'effective_date'],
    incremental_strategy='merge'
  )
}}

{% if is_incremental() %}

with new_parsed as (
    -- Rows parsed since last dedup run (watermark on source_created_at)
    -- e.g. after webhook: only demo-webhook-003 with source_created_at = 2026-06-28 10:18
    select *
    from {{ ref('int_rates_parsed') }}
    where source_created_at > (
        select coalesce(max(source_created_at), '1970-01-01'::timestamptz)
        from {{ this }}
    )
),
affected_keys as (
    -- Which business keys might have a new winner after this batch?
    -- e.g. (chase, 15yr_fixed_mortgage, 2026-06-28) — one key from one webhook
    select distinct normalized_name, rate_type, effective_date
    from new_parsed
),
candidates as (
    -- All parsed rows for those keys — not only today's new row
    -- e.g. chase|15yr|2026-06-28 → raw-001, raw-002, demo-webhook-003 (3 rows to compare)
    select p.*
    from {{ ref('int_rates_parsed') }} p
    inner join affected_keys k
        using (normalized_name, rate_type, effective_date)
),
ranked as (
    -- One winner per key: highest ingestion_ts, then external_id
    -- e.g. raw-002 @ 12:00 → _rn=1 | webhook @ 10:18 → _rn=2 | raw-001 @ 08:00 → _rn=3
    select
        *,
        row_number() over (
            partition by normalized_name, rate_type, effective_date
            order by ingestion_ts desc, external_id desc
        ) as _rn
    from candidates
)

select
    external_id,
    provider_name,
    normalized_name,
    rate_type,
    rate_value,
    effective_date,
    ingestion_ts,
    currency,
    parse_status,
    source_url,
    source_created_at
from ranked
where _rn = 1  -- output: chase|15yr|2026-06-28 → raw-002, rate 8.75, ingestion_ts 12:00

{% else %}

-- Full refresh on first run: same rule as row_number() = 1 over all parsed rows
-- e.g. ~852K parsed → ~27K rows (one per provider + rate_type + effective_date)
select distinct on (normalized_name, rate_type, effective_date)
    external_id,
    provider_name,
    normalized_name,
    rate_type,
    rate_value,
    effective_date,
    ingestion_ts,
    currency,
    parse_status,
    source_url,
    source_created_at
from {{ ref('int_rates_parsed') }}
order by normalized_name, rate_type, effective_date, ingestion_ts desc, external_id desc

{% endif %}
