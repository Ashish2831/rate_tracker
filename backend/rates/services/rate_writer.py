"""Persistence layer — raw-only writes (Option B); transforms live in dbt marts."""

import uuid
from dataclasses import dataclass
from datetime import timezone as dt_timezone
from typing import Any

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from rates.models import RawResponse
from rates.repositories.rate_repository import RateRepository
from rates.services.parser import coerce_parsed_dates, json_safe_value
from rates.services.parsed_rate import ParsedRate

DEFAULT_SOURCE_URL = "https://seed.local/parquet"


@dataclass
class WriteStats:
    """Counters returned after each ingest job for observability."""

    processed: int = 0
    inserted_rates: int = 0
    skipped_duplicates: int = 0
    invalid_records: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "processed": self.processed,
            "inserted_rates": self.inserted_rates,
            "skipped_duplicates": self.skipped_duplicates,
            "invalid_records": self.invalid_records,
        }


def _json_safe_record(record: dict[str, Any]) -> dict[str, Any]:
    return {key: json_safe_value(val) for key, val in record.items()}


def _coerce_fetched_at(value: Any):
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        parsed = value
    else:
        parsed = parse_datetime(str(value))
    if parsed and timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, dt_timezone.utc)
    return parsed


class RateWriter:
    """Persists raw payloads only — dbt builds provider/rate marts downstream."""

    def __init__(self, repository: RateRepository | None = None):
        self.repository = repository or RateRepository()

    def _raw_response_defaults(self, parsed: ParsedRate) -> dict:
        return {
            "source_url": parsed.source_url or DEFAULT_SOURCE_URL,
            "raw_body": parsed.raw_body,
            "fetched_at": parsed.ingestion_ts,
            "parse_status": parsed.parse_status,
            "error_message": parsed.error_message,
        }

    def _raw_from_parquet_record(self, record: dict[str, Any]) -> RawResponse | None:
        provider = record.get("provider")
        if not provider:
            return None

        external_id = record.get("raw_response_id") or str(uuid.uuid4())
        fetched_at = _coerce_fetched_at(record.get("ingestion_ts")) or timezone.now()

        return RawResponse(
            external_id=str(external_id),
            source_url=record.get("source_url") or DEFAULT_SOURCE_URL,
            raw_body=_json_safe_record(record),
            fetched_at=fetched_at,
            parse_status=RawResponse.ParseStatus.SUCCESS,
            error_message="",
        )

    @transaction.atomic
    def persist_one(self, parsed: ParsedRate, stats: WriteStats) -> RawResponse | None:
        """Webhook path — validate via parser, persist raw only, idempotent on external_id."""

        parsed = coerce_parsed_dates(parsed)
        if not parsed:
            stats.invalid_records += 1
            return None

        raw_response, created = RawResponse.objects.get_or_create(
            external_id=parsed.external_id,
            defaults=self._raw_response_defaults(parsed),
        )
        if not created:
            stats.skipped_duplicates += 1
            return None

        stats.inserted_rates += 1
        stats.processed += 1
        return raw_response

    def bulk_persist(self, records: list[dict], stats: WriteStats) -> None:
        """Parquet path — store full rows in raw_body; dedupe/parse happens in dbt."""

        existing_ids = self.repository.existing_external_ids(
            [str(record.get("raw_response_id") or "") for record in records if record.get("raw_response_id")]
        )
        raw_to_create: list[RawResponse] = []
        seen_external: set[str] = set()

        for record in records:
            raw = self._raw_from_parquet_record(record)
            if not raw:
                stats.invalid_records += 1
                continue

            external_id = raw.external_id
            if external_id in existing_ids or external_id in seen_external:
                stats.skipped_duplicates += 1
                continue
            seen_external.add(external_id)

            raw_to_create.append(raw)
            stats.processed += 1

        if raw_to_create:
            RawResponse.objects.bulk_create(raw_to_create, ignore_conflicts=True)
            stats.inserted_rates += len(raw_to_create)
