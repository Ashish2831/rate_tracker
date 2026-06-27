import logging
import uuid
from typing import Any, Callable

from django.db import transaction

from rates.models import Rate
from rates.services.cache import invalidate_all_rate_caches
from rates.services.exceptions import DuplicateRateError, InvalidIngestPayloadError
from rates.services.parser import parse_rate_record
from rates.services.rate_writer import RateWriter, WriteStats
from rates.services.sources import ParquetRateSource, RateRecordSource

logger = logging.getLogger("rates.ingestion")


class IngestionService:
    """Orchestrator — coordinates source iteration, writing, logging, and cache invalidation (SRP)."""

    def __init__(
        self,
        job_id: str | None = None,
        writer: RateWriter | None = None,
        source_factory: Callable[[str], RateRecordSource] | None = None,
        cache_invalidator: Callable[[], None] | None = None,
    ):
        self.job_id = job_id or str(uuid.uuid4())
        self.writer = writer or RateWriter()
        self._source_factory = source_factory or (lambda path: ParquetRateSource(path))
        self._invalidate_caches = cache_invalidator or invalidate_all_rate_caches
        self.stats = WriteStats()

    def log_start(self, source: str) -> None:
        logger.info(
            "Ingestion job started",
            extra={"event": "ingestion_start", "job_id": self.job_id, "source": source},
        )

    def log_end(self) -> None:
        logger.info(
            "Ingestion job completed",
            extra={"event": "ingestion_end", "job_id": self.job_id, **self.stats.as_dict()},
        )

    def log_error(self, error: str) -> None:
        logger.error(
            "Ingestion job failed",
            extra={"event": "ingestion_error", "job_id": self.job_id, "error": error},
        )

    def ingest_from_source(self, source: RateRecordSource) -> dict[str, int]:
        for batch in source.iter_batches():
            with transaction.atomic():
                self.writer.bulk_persist(batch, self.stats)
        self._invalidate_caches()
        return self.stats.as_dict()

    def ingest_from_parquet(self, path: str) -> dict[str, int]:
        self.log_start(path)
        try:
            source = self._source_factory(path)
            stats = self.ingest_from_source(source)
            self.log_end()
            return stats
        except Exception as exc:
            self.log_error(str(exc))
            raise

    def ingest_from_api_payload(self, payload: dict[str, Any]) -> Rate:
        parsed = parse_rate_record(payload)
        if not parsed:
            raise InvalidIngestPayloadError("Invalid ingest payload")

        rate = self.writer.persist_one(parsed, self.stats)
        if not rate:
            raise DuplicateRateError("Duplicate record — idempotent no-op")

        self._invalidate_caches()
        return rate
