import re
import uuid
from decimal import Decimal, InvalidOperation
from typing import Any

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
    key = re.sub(r"\s+", " ", name.strip().lower())
    return PROVIDER_ALIASES.get(key, name.strip().title())


def validate_rate_value(value: Any) -> Decimal | None:
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
    return {
        "provider": record.get("provider"),
        "rate_type": record.get("rate_type"),
        "rate_value": record.get("rate_value"),
        "effective_date": str(record.get("effective_date")),
        "ingestion_ts": str(record.get("ingestion_ts")),
        "currency": record.get("currency"),
        "source_url": record.get("source_url"),
    }


def parse_rate_record(record: dict[str, Any]) -> dict[str, Any] | None:
    provider = record.get("provider")
    rate_type = record.get("rate_type")
    effective_date = record.get("effective_date")
    ingestion_ts = record.get("ingestion_ts")

    if not provider or not rate_type or not effective_date or not ingestion_ts:
        return None

    rate_value = validate_rate_value(record.get("rate_value"))
    external_id = record.get("raw_response_id") or str(uuid.uuid4())

    return {
        "external_id": str(external_id),
        "provider_name": normalize_provider_name(str(provider)),
        "rate_type": str(rate_type).strip(),
        "rate_value": rate_value,
        "effective_date": effective_date,
        "ingestion_ts": ingestion_ts,
        "currency": (record.get("currency") or "USD").upper(),
        "source_url": record.get("source_url") or "",
        "raw_body": build_raw_body(record),
        "parse_status": "success" if rate_value is not None else "partial",
        "error_message": "" if rate_value is not None else "Invalid or missing rate_value",
    }
