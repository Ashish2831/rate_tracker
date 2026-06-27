"""Unit tests for ingestion orchestration and date-range defaults."""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from rates.services.exceptions import DuplicateRateError, InvalidIngestPayloadError
from rates.services.ingestion import IngestionService
from rates.services.rate_writer import RateWriter, WriteStats


def test_write_stats_as_dict():
    stats = WriteStats(processed=10, inserted_rates=5)
    assert stats.as_dict() == {
        "processed": 10,
        "inserted_rates": 5,
        "skipped_duplicates": 0,
        "invalid_records": 0,
        "partial_records": 0,
    }


def test_ingest_api_payload_raises_invalid_payload():
    service = IngestionService()
    with pytest.raises(InvalidIngestPayloadError):
        service.ingest_from_api_payload({"provider": "Chase"})


def test_ingest_api_payload_raises_duplicate_rate():
    writer = MagicMock(spec=RateWriter)
    writer.persist_one.return_value = None
    service = IngestionService(writer=writer)

    payload = {
        "provider": "Chase",
        "rate_type": "30yr_fixed_mortgage",
        "rate_value": "6.75",
        "effective_date": "2025-06-01",
        "ingestion_ts": "2025-06-01T12:00:00Z",
        "raw_response_id": "dup-test-001",
    }

    with pytest.raises(DuplicateRateError):
        service.ingest_from_api_payload(payload)


def test_rate_history_service_default_date_range():
    from rates.services.rate_history_service import RateHistoryService

    date_from, date_to = RateHistoryService.resolve_date_range(None, date(2025, 6, 30))
    assert date_to == date(2025, 6, 30)
    assert date_from == date(2025, 5, 31)


def test_create_rate_source_parquet():
    from rates.services.sources import ParquetRateSource, create_rate_source

    source = create_rate_source("/data/rates_seed.parquet")
    assert isinstance(source, ParquetRateSource)


def test_create_rate_source_unsupported():
    from rates.services.sources import create_rate_source

    with pytest.raises(ValueError, match="Unsupported rate source"):
        create_rate_source("/data/rates.csv")
