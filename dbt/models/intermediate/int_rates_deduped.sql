{{
  config(
    materialized='incremental',
    unique_key=['normalized_name', 'rate_type', 'effective_date'],
    incremental_strategy='merge'
  )
}}

{% if is_incremental() %}

with new_parsed as (
    select *
    from {{ ref('int_rates_parsed') }}
    where source_created_at > (
        select coalesce(max(source_created_at), '1970-01-01'::timestamptz)
        from {{ this }}
    )
),
affected_keys as (
    select distinct normalized_name, rate_type, effective_date
    from new_parsed
),
candidates as (
    select p.*
    from {{ ref('int_rates_parsed') }} p
    inner join affected_keys k
        using (normalized_name, rate_type, effective_date)
),
ranked as (
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
where _rn = 1

{% else %}

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
