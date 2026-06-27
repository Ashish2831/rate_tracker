select
    id,
    external_id,
    source_url,
    raw_body,
    fetched_at,
    parse_status,
    error_message,
    created_at
from {{ source('rates', 'raw_responses') }}
