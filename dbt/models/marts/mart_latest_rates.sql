{{
  config(
    materialized='table',
    tags=['rates_marts']
  )
}}

select distinct on (normalized_name, rate_type)
    id,
    provider_name,
    normalized_name,
    rate_type,
    rate_value,
    effective_date,
    ingestion_ts,
    currency,
    external_id
from {{ ref('mart_rates') }}
order by normalized_name, rate_type, effective_date desc, ingestion_ts desc
