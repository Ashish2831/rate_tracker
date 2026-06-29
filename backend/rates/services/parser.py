"""Parse and normalize rate records from parquet rows, webhooks, and HTTP scrape payloads.

Used on the online ingest path (webhook + HTTP scrape). Bulk parquet seed skips this
module per row — dbt parses raw JSON in SQL instead.

Example — webhook record flowing through this module:

    record = {
        "provider": "Chase",
        "rate_type": "30yr_fixed_mortgage",
        "rate_value": "6.75",
        "effective_date": "2025-06-01",
        "ingestion_ts": "2025-06-01T12:00:00Z",
        "raw_response_id": "webhook-001",
    }
    parsed = parse_rate_record(record)
    # → ParsedRate(parse_status="success", provider_name="Chase", rate_value=Decimal("6.75"), ...)
"""

import math
import re
import uuid
from datetime import date, timezone as dt_timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from rates.services.exceptions import InvalidIngestPayloadError
from rates.services.parsed_rate import ParsedRate

# Canonical display names for the 10 seed banks with casing variants.
# Unknown providers still work — normalize_provider_name() falls back to .title().
# Examples: "hsbc" → "HSBC"  |  "barclays" (not listed) → "Barclays"
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
    """Map casing variants to a single display name for API filters and ParsedRate.

    Examples:
        normalize_provider_name("hsbc")    → "HSBC"      (alias)
        normalize_provider_name("  Chase") → "Chase"     (alias)
        normalize_provider_name("barclays") → "Barclays" (fallback .title())
    """
    key = re.sub(r"\s+", " ", name.strip().lower())
    return PROVIDER_ALIASES.get(key, name.strip().title())


CURRENCY_ALIASES = {
    "usd": "USD",
    "us dollar": "USD",
    "us dollars": "USD",
}


def normalize_currency(value: Any) -> str:
    """Map seed-data variants to ISO 4217 codes.

    Examples:
        normalize_currency(None)        → "USD"
        normalize_currency("us dollar") → "USD"
        normalize_currency("EUR")       → "EUR"
        normalize_currency("dollars")   → "USD"  (unrecognized → default)
    """
    if not value:
        return "USD"
    raw = str(value).strip()
    mapped = CURRENCY_ALIASES.get(raw.lower())
    if mapped:
        return mapped
    upper = raw.upper()
    if len(upper) == 3 and upper.isalpha():
        return upper
    return "USD"


def validate_rate_value(value: Any) -> Decimal | None:
    """Return Decimal for positive values; None for null, zero, or invalid input.

    Examples:
        validate_rate_value("6.75")  → Decimal("6.75")
        validate_rate_value(6.75)    → Decimal("6.75")
        validate_rate_value(None)    → None
        validate_rate_value("0")     → None
        validate_rate_value("-1")    → None
        validate_rate_value("abc")   → None
    """
    if value is None:
        return None
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if not decimal_value.is_finite() or decimal_value <= 0:
        return None
    return decimal_value


def json_safe_value(value: Any) -> Any:
    """Ensure values stored in RawResponse.raw_body are JSON-serializable.

    Examples:
        json_safe_value(Decimal("6.75"))              → "6.75"
        json_safe_value(datetime(2025, 6, 1, 12, 0))  → "2025-06-01T12:00:00"
        json_safe_value(float("nan"))                   → None
    """
    if isinstance(value, Decimal):
        return str(value) if value.is_finite() else None
    if isinstance(value, float) and math.isnan(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def build_raw_body(record: dict[str, Any]) -> dict[str, Any]:
    """Snapshot of source fields stored on RawResponse for replay/debugging.

    Example — input record → stored raw_body JSONB:

        record = {"provider": "Chase", "rate_value": Decimal("6.75"), ...}
        build_raw_body(record)
        → {"provider": "Chase", "rate_value": "6.75", "effective_date": "2025-06-01", ...}
    """
    return {
        "provider": record.get("provider"),
        "rate_type": record.get("rate_type"),
        "rate_value": json_safe_value(record.get("rate_value")),
        "effective_date": str(record.get("effective_date")),
        "ingestion_ts": str(record.get("ingestion_ts")),
        "currency": record.get("currency"),
        "source_url": record.get("source_url"),
    }


def parse_rate_record(record: dict[str, Any]) -> ParsedRate | None:
    """Core parser — webhook validation and HTTP scrape adapter.

    Returns None when provider is missing.

    parse_status outcomes:
        "success" — all required fields + valid rate_value
        "partial" — required fields present but rate_value null/invalid (stored, excluded from marts)
        "failed"  — missing rate_type, effective_date, or ingestion_ts

    Example — success:
        parse_rate_record({
            "provider": "Chase",
            "rate_type": "30yr_fixed_mortgage",
            "rate_value": "6.75",
            "effective_date": "2025-06-01",
            "ingestion_ts": "2025-06-01T12:00:00Z",
            "raw_response_id": "webhook-001",
        })
        → ParsedRate(parse_status="success", external_id="webhook-001", ...)

    Example — partial (bad rate):
        parse_rate_record({..., "rate_value": None, ...})
        → ParsedRate(parse_status="partial", error_message="Invalid or missing rate_value")

    Example — failed (missing fields):
        parse_rate_record({"provider": "Chase", "rate_type": "30yr_fixed_mortgage"})
        → ParsedRate(parse_status="failed", error_message="Missing required fields: ...")
    """
    provider = record.get("provider")
    if not provider:
        return None

    rate_type = record.get("rate_type")
    effective_date = record.get("effective_date")
    ingestion_ts = record.get("ingestion_ts")
    external_id = record.get("raw_response_id") or str(uuid.uuid4())

    missing = [
        name
        for name, value in (
            ("rate_type", rate_type),
            ("effective_date", effective_date),
            ("ingestion_ts", ingestion_ts),
        )
        if not value
    ]
    if missing:
        now = timezone.now()
        return ParsedRate(
            external_id=str(external_id),
            provider_name=normalize_provider_name(str(provider)),
            rate_type=str(rate_type).strip() if rate_type else "unknown",
            rate_value=None,
            effective_date=effective_date or now.date(),
            ingestion_ts=ingestion_ts or now,
            currency=normalize_currency(record.get("currency")),
            source_url=record.get("source_url") or "",
            raw_body=build_raw_body(record),
            parse_status="failed",
            error_message=f"Missing required fields: {', '.join(missing)}",
        )

    rate_value = validate_rate_value(record.get("rate_value"))

    return ParsedRate(
        external_id=str(external_id),
        provider_name=normalize_provider_name(str(provider)),
        rate_type=str(rate_type).strip(),
        rate_value=rate_value,
        effective_date=effective_date,
        ingestion_ts=ingestion_ts,
        currency=normalize_currency(record.get("currency")),
        source_url=record.get("source_url") or "",
        raw_body=build_raw_body(record),
        # Partial records are stored but excluded from read APIs (rate_value IS NOT NULL).
        parse_status="success" if rate_value is not None else "partial",
        error_message="" if rate_value is not None else "Invalid or missing rate_value",
    )


def _record_from_ingest(validated: dict[str, Any]) -> dict[str, Any]:
    """Map DRF serializer output to the flat dict shape expected by parse_rate_record()."""
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
    """Build parsed record from DRF-validated webhook payload.

    Raises InvalidIngestPayloadError when parse_status is "failed" (→ HTTP 400).
    Allows "success" and "partial" through (→ HTTP 201).

    Example:
        parsed_from_ingest({"provider": "Chase", "rate_type": ..., ...})
        → ParsedRate(parse_status="success", ...)

        parsed_from_ingest({"provider": "Chase"})  # missing fields
        → raises InvalidIngestPayloadError
    """
    parsed = parse_rate_record(_record_from_ingest(validated))
    if not parsed or parsed.is_failed:
        raise InvalidIngestPayloadError("Invalid ingest payload")
    return parsed


def parse_scrape_payload(payload: dict[str, Any]) -> ParsedRate | None:
    """Parse HTTP scrape response into a normalized rate record (Adapter pattern).

    Unwraps scraper.fetch_rate_source() output and delegates to parse_rate_record().

    Example — scraper output:
        payload = {
            "source_url": "https://www.chase.com/rates/30yr_fixed_mortgage",
            "status_code": 200,
            "body": {
                "provider": "Chase",
                "rate_type": "30yr_fixed_mortgage",
                "rate_value": "6.75",
                "effective_date": "2025-06-01",
                "ingestion_ts": "2025-06-01T12:00:00Z",
                "raw_response_id": "scrape-001",
            },
        }
        parse_scrape_payload(payload) → ParsedRate(parse_status="success", ...)

    Example — non-dict body (HTML error page, etc.):
        parse_scrape_payload({"body": "<html>..."}) → None
    """
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
    """Normalize date fields on a parsed record to Django-compatible types.

    Called by RateWriter.persist_one() immediately before DB insert.

    Examples:
        effective_date "2025-06-01" (str)  → date(2025, 6, 1)
        ingestion_ts "2025-06-01T12:00:00Z" → aware datetime (UTC)
        naive datetime(2025, 6, 1, 12, 0) → make_aware(..., UTC)

    Returns None when either date cannot be parsed (row skipped by writer).
    """
    effective = parsed.effective_date
    if not isinstance(effective, date):
        effective = parse_date(str(effective))
    ingestion = parsed.ingestion_ts
    if isinstance(ingestion, str):
        ingestion = parse_datetime(ingestion)
    if ingestion and timezone.is_naive(ingestion):
        ingestion = timezone.make_aware(ingestion, dt_timezone.utc)
    if not effective or not ingestion:
        return None
    parsed.effective_date = effective
    parsed.ingestion_ts = ingestion
    return parsed
