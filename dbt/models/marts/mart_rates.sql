{#
  Analytics fact table — cleaned rates for history / ingested API endpoints.
  Django MartRate ORM reads analytics.mart_rates (managed=False).

  Excludes partial rows (rate_value IS NULL). Stable numeric id via hashtext(external_id).
#}
{{
  config(
    materialized='incremental',
    unique_key=['normalized_name', 'rate_type', 'effective_date'],
    incremental_strategy='merge',
    tags=['rates_marts']
  )
}}

select
    abs(hashtext(external_id))::bigint as id,  -- Deterministic surrogate for Django ORM PK
    provider_name,
    normalized_name,
    rate_type,
    rate_value,
    effective_date,
    ingestion_ts,
    currency,
    external_id,
    source_created_at
from {{ ref('int_rates_deduped') }}
where rate_value is not null  -- Partial/failed parses excluded from read APIs
{% if is_incremental() %}
  -- Only merge mart rows whose business keys changed in this ingest batch
  and (normalized_name, rate_type, effective_date) in (
      select normalized_name, rate_type, effective_date
      from {{ ref('int_rates_deduped') }}
      where source_created_at > (
          select coalesce(max(source_created_at), '1970-01-01'::timestamptz)
          from {{ this }}
      )
  )
{% endif %}
