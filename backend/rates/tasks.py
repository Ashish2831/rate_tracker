"""Celery Beat task — re-processes seed parquet on a 15-minute schedule."""

import logging

from celery import shared_task
from django.conf import settings

from rates.services.ingestion import IngestionService

logger = logging.getLogger("rates.tasks")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_scheduled_ingestion(self):
    """Scheduled ingestion task — re-processes seed file idempotently."""
    service = IngestionService(job_id=self.request.id or "scheduled")
    try:
        return service.ingest_from_parquet(settings.SEED_PARQUET_PATH)
    except Exception as exc:
        logger.error(
            "Scheduled ingestion failed",
            extra={"event": "scheduled_ingestion_error", "job_id": service.job_id, "error": str(exc)},
        )
        raise self.retry(exc=exc)
