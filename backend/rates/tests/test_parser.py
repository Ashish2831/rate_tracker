"""Unit tests for parser normalization and partial-record handling."""

from decimal import Decimal

from rates.services.parser import normalize_provider_name, parse_rate_record, validate_rate_value


def test_normalize_provider_name_handles_casing():
    assert normalize_provider_name("hsbc") == "HSBC"
    assert normalize_provider_name("HSBC") == "HSBC"
    assert normalize_provider_name("Chase") == "Chase"


def test_validate_rate_value_rejects_invalid():
    assert validate_rate_value(None) is None
    assert validate_rate_value(0) is None
    assert validate_rate_value(-1.5) is None
    assert validate_rate_value(float("nan")) is None
    assert validate_rate_value(5.25) == Decimal("5.25")


def test_parse_rate_record_partial_on_null_value():
    record = {
        "provider": "Chase",
        "rate_type": "30yr_fixed_mortgage",
        "rate_value": None,
        "effective_date": "2025-01-01",
        "ingestion_ts": "2025-01-01T00:00:00",
        "raw_response_id": "partial-001",
        "source_url": "https://chase.com",
        "currency": "USD",
    }
    parsed = parse_rate_record(record)
    assert parsed is not None
    assert parsed.parse_status == "partial"


def test_parse_rate_record_failed_on_missing_required_fields():
    record = {
        "provider": "Chase",
        "rate_type": None,
        "rate_value": "6.75",
        "effective_date": "2025-01-01",
        "ingestion_ts": "2025-01-01T00:00:00",
        "raw_response_id": "failed-001",
    }
    parsed = parse_rate_record(record)
    assert parsed is not None
    assert parsed.parse_status == "failed"
    assert "rate_type" in parsed.error_message
