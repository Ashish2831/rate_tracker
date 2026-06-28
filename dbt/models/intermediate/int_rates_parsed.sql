{#
  Parse raw JSON into typed columns.
  Incremental: only rows with created_at newer than max(source_created_at) in this table.
  Excludes rows missing required fields or with invalid rate_value (null kept for audit).
#}
{{
  config(
    materialized='incremental',
    unique_key='external_id',
    incremental_strategy='merge'
  )
}}

with extracted as (
    select
        external_id,
        {{ normalize_provider("raw_body->>'provider'") }} as provider_name,
        lower(trim(raw_body->>'provider')) as normalized_name,  -- Join/filter key
        trim(raw_body->>'rate_type') as rate_type,
        case
            when raw_body->>'rate_value' is null or trim(raw_body->>'rate_value') = '' then null
            when (raw_body->>'rate_value')::numeric <= 0 then null
            else (raw_body->>'rate_value')::numeric
        end as rate_value,
        (raw_body->>'effective_date')::date as effective_date,
        coalesce(
            (raw_body->>'ingestion_ts')::timestamptz,
            fetched_at
        ) as ingestion_ts,
        upper(
            coalesce(
                nullif(trim(raw_body->>'currency'), ''),
                'USD'
            )
        ) as currency,
        parse_status,
        source_url,
        created_at as source_created_at  -- Carried through for incremental watermarks
    from {{ ref('stg_raw_responses') }}
    where raw_body->>'provider' is not null
      and trim(raw_body->>'provider') <> ''
      and raw_body->>'rate_type' is not null
      and trim(raw_body->>'rate_type') <> ''
      and raw_body->>'effective_date' is not null
      and raw_body->>'ingestion_ts' is not null
      {% if is_incremental() %}
      -- Watermark: rates_rawresponse.created_at → source_created_at
      and created_at > (select coalesce(max(source_created_at), '1970-01-01'::timestamptz) from {{ this }})
      {% endif %}
)

select *
from extracted
where effective_date is not null
  and ingestion_ts is not null
