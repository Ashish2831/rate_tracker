import logging

from celery import shared_task
from django.conf import settings

from rates.services.ingestion import IngestionService

logger = logging.getLogger("rates.tasks")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_scheduled_ingestion(self):
    """Scheduled ingestion task — re-processes seed file for demo purposes."""
    job_id = self.request.id or "scheduled"
    service = IngestionService(job_id=job_id)
    path = settings.SEED_PARQUET_PATH
    logger.info(
        "Scheduled ingestion triggered",
        extra={"event": "scheduled_ingestion_start", "job_id": job_id, "path": path},
    )
    try:
        stats = service.ingest_from_parquet(path)
        logger.info(
            "Scheduled ingestion finished",
            extra={"event": "scheduled_ingestion_end", "job_id": job_id, **stats},
        )
        return stats
    except Exception as exc:
        logger.error(
            "Scheduled ingestion failed",
            extra={"event": "scheduled_ingestion_error", "job_id": job_id, "error": str(exc)},
        )
        raise self.retry(exc=exc)
