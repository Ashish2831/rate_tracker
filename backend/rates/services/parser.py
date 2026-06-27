"""Parse and normalize rate records from parquet rows, webhooks, and HTTP scrape payloads."""

import re
import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from rates.services.exceptions import InvalidIngestPayloadError
from rates.services.parsed_rate import ParsedRate

# Canonical display names for known seed-data casing variants.
PROVIDER_ALIASES = {
    "hsbc": "HSBC",
    "chase": "Chase",
    "bank of america": "Bank of America",
    "truist": "Truist",
    "us bancorp": "US Bancorp",
    "td bank": "TD Bank",
    "pnc bank": "PNC Bank",
    "capital one": "Capital One",
    "citibank": "Citibank",
    "wells fargo": "Wells Fargo",
}


def normalize_provider_name(name: str) -> str:
    """Map casing variants to a single display name (e.g. 'hsbc' → 'HSBC')."""
    key = re.sub(r"\s+", " ", name.strip().lower())
    return PROVIDER_ALIASES.get(key, name.strip().title())


def validate_rate_value(value: Any) -> Decimal | None:
    """Return Decimal for positive values; None for null, zero, or invalid input."""
    if value is None:
        return None
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if decimal_value <= 0:
        return None
    return decimal_value


def build_raw_body(record: dict[str, Any]) -> dict[str, Any]:
    """Snapshot of source fields stored on RawResponse for replay/debugging."""
    return {
        "provider": record.get("provider"),
        "rate_type": record.get("rate_type"),
        "rate_value": record.get("rate_value"),
        "effective_date": str(record.get("effective_date")),
        "ingestion_ts": str(record.get("ingestion_ts")),
        "currency": record.get("currency"),
        "source_url": record.get("source_url"),
    }


def parse_rate_record(record: dict[str, Any]) -> ParsedRate | None:
    """Core parser — shared by parquet, webhook, and scrape paths."""
    provider = record.get("provider")
    rate_type = record.get("rate_type")
    effective_date = record.get("effective_date")
    ingestion_ts = record.get("ingestion_ts")

    if not provider or not rate_type or not effective_date or not ingestion_ts:
        return None

    rate_value = validate_rate_value(record.get("rate_value"))
    external_id = record.get("raw_response_id") or str(uuid.uuid4())

    return ParsedRate(
        external_id=str(external_id),
        provider_name=normalize_provider_name(str(provider)),
        rate_type=str(rate_type).strip(),
        rate_value=rate_value,
        effective_date=effective_date,
        ingestion_ts=ingestion_ts,
        currency=(record.get("currency") or "USD").upper(),
        source_url=record.get("source_url") or "",
        raw_body=build_raw_body(record),
        # Partial records are stored but excluded from read APIs (rate_value IS NOT NULL).
        parse_status="success" if rate_value is not None else "partial",
        error_message="" if rate_value is not None else "Invalid or missing rate_value",
    )


def _record_from_ingest(validated: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider": validated.get("provider"),
        "rate_type": validated.get("rate_type"),
        "rate_value": validated.get("rate_value"),
        "effective_date": validated.get("effective_date"),
        "ingestion_ts": validated.get("ingestion_ts"),
        "currency": validated.get("currency", "USD"),
        "source_url": validated.get("source_url", ""),
        "raw_response_id": validated.get("raw_response_id"),
    }


def parsed_from_ingest(validated: dict[str, Any]) -> ParsedRate:
    """Build parsed record from DRF-validated webhook payload."""
    parsed = parse_rate_record(_record_from_ingest(validated))
    if not parsed:
        raise InvalidIngestPayloadError("Invalid ingest payload")
    return parsed


def parse_scrape_payload(payload: dict[str, Any]) -> ParsedRate | None:
    """Parse HTTP scrape response body into a normalized rate record (Adapter pattern)."""
    body = payload.get("body")
    if not isinstance(body, dict):
        return None
    return parse_rate_record(
        {
            "provider": body.get("provider"),
            "rate_type": body.get("rate_type"),
            "rate_value": body.get("rate_value"),
            "effective_date": body.get("effective_date"),
            "ingestion_ts": body.get("ingestion_ts"),
            "currency": body.get("currency", "USD"),
            "source_url": payload.get("source_url"),
            "raw_response_id": body.get("raw_response_id"),
        }
    )


def coerce_parsed_dates(parsed: ParsedRate) -> ParsedRate | None:
    """Normalize date fields on a parsed record to Django-compatible types."""
    effective = parsed.effective_date
    if not isinstance(effective, date):
        effective = parse_date(str(effective))
    ingestion = parsed.ingestion_ts
    if isinstance(ingestion, str):
        ingestion = parse_datetime(ingestion)
    if ingestion and timezone.is_naive(ingestion):
        ingestion = timezone.make_aware(ingestion, timezone.utc)
    if not effective or not ingestion:
        return None
    parsed.effective_date = effective
    parsed.ingestion_ts = ingestion
    return parsed
