import logging
import uuid
from datetime import datetime
from typing import Any, Iterable

import pyarrow.parquet as pq
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from rates.models import Provider, Rate, RawResponse
from rates.services.cache import invalidate_all_rate_caches, invalidate_latest_cache
from rates.services.parser import normalize_provider_name, parse_rate_record

logger = logging.getLogger("rates.ingestion")

BATCH_SIZE = 10000


class IngestionService:
    def __init__(self, job_id: str | None = None):
        self.job_id = job_id or str(uuid.uuid4())
        self.stats = {
            "processed": 0,
            "inserted_rates": 0,
            "skipped_duplicates": 0,
            "invalid_records": 0,
            "partial_records": 0,
        }
        self._provider_cache: dict[str, Provider] = {}

    def log_start(self, source: str) -> None:
        logger.info(
            "Ingestion job started",
            extra={"event": "ingestion_start", "job_id": self.job_id, "source": source},
        )

    def log_end(self) -> None:
        logger.info(
            "Ingestion job completed",
            extra={"event": "ingestion_end", "job_id": self.job_id, **self.stats},
        )

    def log_error(self, error: str) -> None:
        logger.error(
            "Ingestion job failed",
            extra={"event": "ingestion_error", "job_id": self.job_id, "error": error},
        )

    def _get_or_create_provider(self, name: str) -> Provider:
        normalized = normalize_provider_name(name)
        key = normalized.lower()
        if key in self._provider_cache:
            return self._provider_cache[key]
        provider, _ = Provider.objects.get_or_create(
            normalized_name=key,
            defaults={"name": normalized},
        )
        self._provider_cache[key] = provider
        return provider

    def _coerce_dates(self, parsed: dict[str, Any]) -> dict[str, Any] | None:
        effective = parsed["effective_date"]
        if not isinstance(effective, datetime):
            effective = parse_date(str(effective))
        ingestion = parsed["ingestion_ts"]
        if isinstance(ingestion, str):
            ingestion = parse_datetime(ingestion)
        if ingestion and timezone.is_naive(ingestion):
            ingestion = timezone.make_aware(ingestion, timezone.utc)
        if not effective or not ingestion:
            return None
        parsed["effective_date"] = effective
        parsed["ingestion_ts"] = ingestion
        return parsed

    @transaction.atomic
    def ingest_parsed_record(self, parsed: dict[str, Any]) -> Rate | None:
        parsed = self._coerce_dates(parsed)
        if not parsed:
            self.stats["invalid_records"] += 1
            return None

        provider = self._get_or_create_provider(parsed["provider_name"])

        raw_response, created = RawResponse.objects.get_or_create(
            external_id=parsed["external_id"],
            defaults={
                "source_url": parsed["source_url"] or "https://seed.local/parquet",
                "raw_body": parsed["raw_body"],
                "fetched_at": parsed["ingestion_ts"],
                "parse_status": parsed["parse_status"],
                "error_message": parsed["error_message"],
            },
        )
        if not created:
            self.stats["skipped_duplicates"] += 1
            return None

        if parsed["parse_status"] == "partial":
            self.stats["partial_records"] += 1

        rate, rate_created = Rate.objects.get_or_create(
            provider=provider,
            rate_type=parsed["rate_type"],
            effective_date=parsed["effective_date"],
            ingestion_ts=parsed["ingestion_ts"],
            defaults={
                "rate_value": parsed["rate_value"],
                "currency": parsed["currency"],
                "raw_response": raw_response,
            },
        )
        if rate_created:
            self.stats["inserted_rates"] += 1
        else:
            self.stats["skipped_duplicates"] += 1
        self.stats["processed"] += 1
        return rate

    def ingest_records(self, records: Iterable[dict[str, Any]]) -> dict[str, int]:
        for record in records:
            parsed = parse_rate_record(record)
            if not parsed:
                self.stats["invalid_records"] += 1
                continue
            self.ingest_parsed_record(parsed)
        invalidate_all_rate_caches()
        return self.stats

    def _bulk_ingest_batch(self, records: list[dict[str, Any]]) -> None:
        existing_raw_ids = set(
            RawResponse.objects.filter(
                external_id__in=[r["external_id"] for r in records]
            ).values_list("external_id", flat=True)
        )

        raw_to_create: list[RawResponse] = []
        rates_to_create: list[Rate] = []
        seen_external: set[str] = set()

        for record in records:
            parsed = parse_rate_record(record)
            if not parsed:
                self.stats["invalid_records"] += 1
                continue

            parsed = self._coerce_dates(parsed)
            if not parsed:
                self.stats["invalid_records"] += 1
                continue

            external_id = parsed["external_id"]
            if external_id in existing_raw_ids or external_id in seen_external:
                self.stats["skipped_duplicates"] += 1
                continue
            seen_external.add(external_id)

            if parsed["parse_status"] == "partial":
                self.stats["partial_records"] += 1

            provider = self._get_or_create_provider(parsed["provider_name"])
            raw = RawResponse(
                external_id=external_id,
                source_url=parsed["source_url"] or "https://seed.local/parquet",
                raw_body=parsed["raw_body"],
                fetched_at=parsed["ingestion_ts"],
                parse_status=parsed["parse_status"],
                error_message=parsed["error_message"],
            )
            raw_to_create.append(raw)
            rates_to_create.append(
                Rate(
                    provider=provider,
                    rate_type=parsed["rate_type"],
                    rate_value=parsed["rate_value"],
                    effective_date=parsed["effective_date"],
                    ingestion_ts=parsed["ingestion_ts"],
                    currency=parsed["currency"],
                    raw_response_id=raw.id,
                )
            )
            self.stats["processed"] += 1

        if raw_to_create:
            RawResponse.objects.bulk_create(raw_to_create, ignore_conflicts=True)
            created_rates = Rate.objects.bulk_create(rates_to_create, ignore_conflicts=True)
            self.stats["inserted_rates"] += len(created_rates)

    def ingest_from_parquet(self, path: str) -> dict[str, int]:
        self.log_start(path)
        try:
            parquet_file = pq.ParquetFile(path)
            for batch in parquet_file.iter_batches(batch_size=BATCH_SIZE):
                df = batch.to_pandas()
                df = df.sort_values("ingestion_ts").drop_duplicates(
                    subset=["provider", "rate_type", "effective_date"],
                    keep="last",
                )
                records = df.to_dict(orient="records")
                with transaction.atomic():
                    self._bulk_ingest_batch(records)
            invalidate_all_rate_caches()
            self.log_end()
            return self.stats
        except Exception as exc:
            self.log_error(str(exc))
            raise

    def ingest_from_api_payload(self, payload: dict[str, Any]) -> Rate:
        parsed = parse_rate_record(payload)
        if not parsed:
            raise ValueError("Invalid ingest payload")
        rate = self.ingest_parsed_record(parsed)
        if not rate:
            raise ValueError("Duplicate record — idempotent no-op")
        invalidate_latest_cache(parsed["rate_type"])
        return rate
