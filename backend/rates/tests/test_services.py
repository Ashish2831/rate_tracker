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
    }


def test_coerce_fetched_at_makes_naive_datetime_aware():
    from datetime import datetime

    from rates.services.rate_writer import _coerce_fetched_at

    naive = datetime(2025, 6, 1, 12, 0, 0)
    aware = _coerce_fetched_at(naive)

    assert aware is not None
    assert aware.tzinfo is not None


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


def test_rate_history_service_anchors_to_latest_data(mocker):
    from rates.services.rate_history_service import RateHistoryService

    repo = mocker.Mock()
    repo.get_latest_effective_date.return_value = date(2024, 9, 25)
    repo.get_history.return_value = []

    service = RateHistoryService(repository=repo)
    service.get_history("HSBC", "15yr_fixed_mortgage")

    repo.get_history.assert_called_once_with("hsbc", "15yr_fixed_mortgage", date(2024, 8, 26), date(2024, 9, 25))


def test_ingested_rates_service_resolve_window_defaults():
    from datetime import datetime, timedelta

    from django.utils import timezone

    from rates.services.ingested_rates_service import IngestedRatesService

    window_from, window_to = IngestedRatesService.resolve_window(None, None, default_hours=24)

    assert window_to is not None
    assert window_from is not None
    assert window_to - window_from == timedelta(hours=24)
    assert abs((timezone.now() - window_to).total_seconds()) < 5


def test_ingested_rates_service_resolve_window_invalid():
    from rates.services.ingested_rates_service import IngestedRatesService

    with pytest.raises(ValueError, match="Invalid datetime"):
        IngestedRatesService.resolve_window("not-a-datetime", None)


def test_create_rate_source_parquet():
    from rates.services.sources import HttpRateSource, ParquetRateSource, create_rate_source

    source = create_rate_source("/data/rates_seed.parquet")
    assert isinstance(source, ParquetRateSource)


def test_create_rate_source_http():
    from rates.services.sources import HttpRateSource, create_rate_source

    source = create_rate_source("https://example.com/rates.json")
    assert isinstance(source, HttpRateSource)
    assert source.url == "https://example.com/rates.json"


def test_http_rate_source_yields_parsed_record(mocker):
    from rates.services.sources import HttpRateSource

    mocker.patch(
        "rates.services.sources.fetch_rate_source",
        return_value={
            "source_url": "https://example.com/rates.json",
            "body": {
                "provider": "Chase",
                "rate_type": "30yr_fixed_mortgage",
                "rate_value": 6.75,
                "effective_date": "2025-06-01",
                "ingestion_ts": "2025-06-01T12:00:00Z",
                "raw_response_id": "http-001",
            },
        },
    )
    source = HttpRateSource("https://example.com/rates.json")
    batches = list(source.iter_batches())
    assert len(batches) == 1
    assert batches[0][0]["provider"] == "Chase"


def test_http_rate_source_raises_on_unparseable_payload(mocker):
    from rates.services.sources import HttpRateSource

    mocker.patch(
        "rates.services.sources.fetch_rate_source",
        return_value={
            "source_url": "https://example.com/rates.json",
            "status_code": 200,
            "body": {"raw_text": "not json"},
        },
    )
    source = HttpRateSource("https://example.com/rates.json")

    with pytest.raises(InvalidIngestPayloadError, match="Could not parse rate record"):
        list(source.iter_batches())


def test_create_rate_source_unsupported():
    from rates.services.sources import create_rate_source

    with pytest.raises(ValueError, match="Unsupported rate source"):
        create_rate_source("/data/rates.csv")


def test_latest_cache_key_includes_epoch(mocker):
    from rates.services import cache as cache_mod

    mocker.patch.object(cache_mod, "get_cache_epoch", return_value=3)
    assert cache_mod.latest_cache_key("30yr_fixed_mortgage") == "rates:latest:3:all:30yr_fixed_mortgage"
    assert cache_mod.latest_cache_key() == "rates:latest:3:all:all"
    assert cache_mod.latest_cache_key("30yr_fixed_mortgage", "chase") == "rates:latest:3:chase:30yr_fixed_mortgage"


def test_invalidate_rate_caches_increments_epoch():
    from rates.services.cache import LATEST_CACHE_EPOCH_KEY, get_cache_epoch, invalidate_rate_caches

    mock_cache = MagicMock()
    mock_cache.get.return_value = 2

    invalidate_rate_caches(cache_backend=mock_cache)
    mock_cache.incr.assert_called_once_with(LATEST_CACHE_EPOCH_KEY)


def test_invalidate_rate_caches_seeds_epoch_when_missing():
    from rates.services.cache import LATEST_CACHE_EPOCH_KEY, invalidate_rate_caches

    mock_cache = MagicMock()
    mock_cache.incr.side_effect = ValueError("Key not found")

    invalidate_rate_caches(cache_backend=mock_cache)
    mock_cache.set.assert_called_once_with(LATEST_CACHE_EPOCH_KEY, 1, timeout=None)


def test_get_cache_epoch_defaults_to_zero():
    from rates.services.cache import get_cache_epoch

    mock_cache = MagicMock()
    mock_cache.get.return_value = None
    assert get_cache_epoch(cache_backend=mock_cache) == 0
