from typing import Any

from rates.services.parser import parse_rate_record


def parse_http_payload(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Adapter — maps an HTTP scrape response into a normalized parsed rate record."""
    body = payload.get("body")
    if not isinstance(body, dict):
        return None

    record = {
        "provider": body.get("provider"),
        "rate_type": body.get("rate_type"),
        "rate_value": body.get("rate_value"),
        "effective_date": body.get("effective_date"),
        "ingestion_ts": body.get("ingestion_ts"),
        "currency": body.get("currency", "USD"),
        "source_url": payload.get("source_url"),
        "raw_response_id": body.get("raw_response_id"),
    }
    return parse_rate_record(record)
