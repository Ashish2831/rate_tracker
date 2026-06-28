"""Ingestion orchestrator — raw load in Django, transforms via dbt, cache invalidation."""

import logging
import uuid
from typing import Any, Callable

from django.conf import settings
from django.db import transaction

from rates.models import RawResponse
from rates.services.cache import invalidate_rate_caches
from rates.services.dbt_runner import DbtRunError, DbtRunner
from rates.services.exceptions import DuplicateRateError, InvalidIngestPayloadError
from rates.services.mart_bootstrap import marts_exist
from rates.services.parser import parsed_from_ingest
from rates.services.rate_writer import RateWriter, WriteStats
from rates.services.sources import RateRecordSource, create_rate_source

logger = logging.getLogger("rates.ingestion")


class IngestionService:
    """Orchestrator — raw ingest, dbt mart refresh, logging, cache invalidation."""

    def __init__(
        self,
        job_id: str | None = None,
        writer: RateWriter | None = None,
        source_factory: Callable[[str], RateRecordSource] | None = None,
        cache_invalidator: Callable[[], None] | None = None,
        dbt_runner: DbtRunner | None = None,
    ):
        self.job_id = job_id or str(uuid.uuid4())
        self.writer = writer or RateWriter()
        self._source_factory = source_factory or create_rate_source
        self._invalidate_caches = cache_invalidator or invalidate_rate_caches
        self._dbt_runner = dbt_runner or DbtRunner()
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

    def _marts_exist(self) -> bool:
        return marts_exist()

    def _refresh_marts(self) -> None:
        if not settings.DBT_RUN_AFTER_INGEST:
            return
        full_refresh = not self._marts_exist()
        try:
            self._dbt_runner.run_marts(full_refresh=full_refresh)
        except DbtRunError as exc:
            logger.error(
                "dbt mart refresh failed after ingest",
                extra={"event": "dbt_refresh_error", "job_id": self.job_id, "error": str(exc)},
            )
            raise

    def ingest_from_source(self, source: RateRecordSource) -> dict[str, int]:
        """Iterate source batches inside transactions; dbt refresh + cache bust at end."""
        for batch in source.iter_batches():
            with transaction.atomic():
                self.writer.bulk_persist(batch, self.stats)
        self._refresh_marts()
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

    def ingest_from_api_payload(self, payload: dict[str, Any]) -> RawResponse:
        """Webhook path — validate, persist raw, refresh marts, raise on duplicate."""
        parsed = parsed_from_ingest(payload)
        raw = self.writer.persist_one(parsed, self.stats)
        if not raw:
            raise DuplicateRateError("Duplicate record — idempotent no-op")

        self._refresh_marts()
        self._invalidate_caches()
        return raw
