"""Persistence layer — writes parsed records to RawResponse + Rate with idempotency."""

from dataclasses import dataclass

from django.db import transaction

from rates.models import Provider, Rate, RawResponse
from rates.repositories.rate_repository import RateRepository
from rates.services.parser import coerce_parsed_dates, normalize_provider_name, parse_rate_record
from rates.services.parsed_rate import ParsedRate


@dataclass
class WriteStats:
    """Counters returned after each ingest job for observability."""

    processed: int = 0
    inserted_rates: int = 0
    skipped_duplicates: int = 0
    invalid_records: int = 0
    partial_records: int = 0
    failed_records: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "processed": self.processed,
            "inserted_rates": self.inserted_rates,
            "skipped_duplicates": self.skipped_duplicates,
            "invalid_records": self.invalid_records,
            "partial_records": self.partial_records,
            "failed_records": self.failed_records,
        }


class ProviderResolver:
    """In-memory cache + get_or_create for provider rows during bulk loads.
    
    This class is used to resolve provider names to Provider objects during bulk loads and webhook ingestion.
    """

    def __init__(self):
        self._cache: dict[str, Provider] = {}

    def resolve(self, name: str) -> Provider:
        """Return existing Provider row or create one keyed by normalized_name."""
        normalized = normalize_provider_name(name)
        key = normalized.lower()
        if key in self._cache:
            return self._cache[key]
        provider, _ = Provider.objects.get_or_create(
            normalized_name=key,
            defaults={"name": normalized},
        )
        self._cache[key] = provider
        return provider


class RateWriter:
    """Persists parsed records via single-row (webhook) or bulk (parquet) paths.
    
    This class is used to persist parsed records via single-row (webhook) or bulk (parquet) paths.
    """

    # Default source URL for parquet ingestion, this is a placeholder for the actual source URL
    DEFAULT_SOURCE_URL = "https://seed.local/parquet"

    def __init__(
        self,
        repository: RateRepository | None = None,
        provider_resolver: ProviderResolver | None = None,
    ):
        self.repository = repository or RateRepository()
        self.provider_resolver = provider_resolver or ProviderResolver()

    def _raw_response_defaults(self, parsed: ParsedRate) -> dict:
        raw = self._build_raw_response(parsed)
        return {
            "source_url": raw.source_url,
            "raw_body": raw.raw_body,
            "fetched_at": raw.fetched_at,
            "parse_status": raw.parse_status,
            "error_message": raw.error_message,
        }

    def _build_raw_response(self, parsed: ParsedRate) -> RawResponse:
        return RawResponse(
            external_id=parsed.external_id,
            source_url=parsed.source_url or self.DEFAULT_SOURCE_URL,
            raw_body=parsed.raw_body,
            fetched_at=parsed.ingestion_ts,
            parse_status=parsed.parse_status,
            error_message=parsed.error_message,
        )

    def _build_rate(self, parsed: ParsedRate, provider: Provider, raw: RawResponse) -> Rate:
        return Rate(
            provider=provider,
            rate_type=parsed.rate_type,
            rate_value=parsed.rate_value,
            effective_date=parsed.effective_date,
            ingestion_ts=parsed.ingestion_ts,
            currency=parsed.currency,
            raw_response_id=raw.id,
        )

    def _track_parse_status(self, parsed: ParsedRate, stats: WriteStats) -> None:
        if parsed.is_partial:
            stats.partial_records += 1
        elif parsed.is_failed:
            stats.failed_records += 1

    @transaction.atomic
    def persist_one(self, parsed: ParsedRate, stats: WriteStats) -> Rate | None:
        """Webhook path — get_or_create on external_id for idempotent ingest.
        
        This method is used to persist a single parsed record via webhook ingestion.
        """

        parsed = coerce_parsed_dates(parsed) # Coerce the parsed dates to Django-compatible types
        if not parsed:
            stats.invalid_records += 1
            return None

        provider = self.provider_resolver.resolve(parsed.provider_name)
        raw_response, created = RawResponse.objects.get_or_create(
            external_id=parsed.external_id,
            defaults=self._raw_response_defaults(parsed),
        )
        if not created:
            stats.skipped_duplicates += 1
            return None

        self._track_parse_status(parsed, stats)
        rate, rate_created = Rate.objects.get_or_create(
            provider=provider,
            rate_type=parsed.rate_type,
            effective_date=parsed.effective_date,
            ingestion_ts=parsed.ingestion_ts,
            defaults={
                "rate_value": parsed.rate_value,
                "currency": parsed.currency,
                "raw_response": raw_response,
            },
        )
        if rate_created:
            stats.inserted_rates += 1
        else:
            stats.skipped_duplicates += 1
        stats.processed += 1
        return rate

    def bulk_persist(self, records: list[dict], stats: WriteStats) -> None:
        """Parquet path — pre-filter duplicates, then bulk_create with ignore_conflicts."""
        parsed_records: list[ParsedRate] = []
        for record in records:
            parsed = parse_rate_record(record)
            if not parsed:
                stats.invalid_records += 1
                continue
            parsed = coerce_parsed_dates(parsed)
            if not parsed:
                stats.invalid_records += 1
                continue
            parsed_records.append(parsed)

        if not parsed_records:
            return

        existing_ids = self.repository.existing_external_ids(
            [parsed.external_id for parsed in parsed_records]
        )
        raw_to_create: list[RawResponse] = []
        rates_to_create: list[Rate] = []
        seen_external: set[str] = set()

        for parsed in parsed_records:
            external_id = parsed.external_id
            # Skip DB hits and within-batch duplicates before building ORM objects.
            if external_id in existing_ids or external_id in seen_external:
                stats.skipped_duplicates += 1
                continue
            seen_external.add(external_id)

            self._track_parse_status(parsed, stats)
            provider = self.provider_resolver.resolve(parsed.provider_name)
            raw = self._build_raw_response(parsed)
            raw_to_create.append(raw)
            rates_to_create.append(self._build_rate(parsed, provider, raw))
            stats.processed += 1

        if raw_to_create:
            # RawResponse rows must exist before Rate FK assignment in bulk path.
            RawResponse.objects.bulk_create(raw_to_create, ignore_conflicts=True)
            created_rates = Rate.objects.bulk_create(rates_to_create, ignore_conflicts=True)
            stats.inserted_rates += len(created_rates)
