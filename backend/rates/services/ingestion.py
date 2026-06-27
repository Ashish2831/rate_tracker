"""Ingestion orchestrator — coordinates source iteration, persistence, and cache invalidation."""

import logging
import uuid
from typing import Any, Callable

from django.db import transaction

from rates.models import Rate
from rates.services.cache import invalidate_rate_caches
from rates.services.exceptions import DuplicateRateError
from rates.services.parser import parsed_from_ingest
from rates.services.rate_writer import RateWriter, WriteStats
from rates.services.sources import RateRecordSource, create_rate_source

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
        self._source_factory = source_factory or create_rate_source
        self._invalidate_caches = cache_invalidator or invalidate_rate_caches
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
        """Iterate source batches inside transactions; invalidate cache once at the end."""
        for batch in source.iter_batches():
            with transaction.atomic():
                self.writer.bulk_persist(batch, self.stats)
        self._invalidate_caches()
        return self.stats.as_dict()

    def ingest_from_path(self, path: str) -> dict[str, int]:
        """Ingest from a parquet path or HTTP(S) URL (factory selects source strategy)."""
        self.log_start(path)
        try:
            source = self._source_factory(path)
            stats = self.ingest_from_source(source)
            self.log_end()
            return stats
        except Exception as exc:
            self.log_error(str(exc))
            raise

    def ingest_from_parquet(self, path: str) -> dict[str, int]:
        """Backward-compatible alias for ingest_from_path."""
        return self.ingest_from_path(path)

    def ingest_from_api_payload(self, payload: dict[str, Any]) -> Rate:
        """Webhook path — single record, raises DuplicateRateError on idempotent re-post."""
        parsed = parsed_from_ingest(payload)
        rate = self.writer.persist_one(parsed, self.stats)
        if not rate:
            raise DuplicateRateError("Duplicate record — idempotent no-op")

        self._invalidate_caches()
        return rate
