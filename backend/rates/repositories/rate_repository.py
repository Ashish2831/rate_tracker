"""Repository — reads from dbt marts; raw idempotency checks on rates_rawresponse."""

from datetime import date, datetime

from django.db.models import QuerySet

from rates.models import MartLatestRate, MartRate, RawResponse


class RateRepository:
    """Encapsulates ORM access for mart reads and bulk deduplication lookups."""

    def get_latest_per_provider(
        self,
        rate_type: str | None = None,
        normalized_provider: str | None = None,
    ) -> list[MartLatestRate]:
        """One row per (provider, rate_type) from dbt mart_latest_rates."""
        queryset = MartLatestRate.objects.all()
        if rate_type:
            queryset = queryset.filter(rate_type=rate_type)
        if normalized_provider:
            queryset = queryset.filter(normalized_name=normalized_provider)
        return list(queryset.order_by("provider_name", "rate_type"))

    def get_filter_options(self) -> tuple[list[str], list[str]]:
        """Distinct provider names and rate types from mart_rates."""
        providers = list(
            MartRate.objects.values_list("provider_name", flat=True)
            .distinct()
            .order_by("provider_name")
        )
        rate_types = list(
            MartRate.objects.values_list("rate_type", flat=True).distinct().order_by("rate_type")
        )
        return providers, rate_types

    def get_latest_effective_date(self, normalized_provider: str, rate_type: str) -> date | None:
        """Most recent effective_date for a provider/rate_type — anchors history charts."""
        return (
            MartRate.objects.filter(
                normalized_name=normalized_provider,
                rate_type=rate_type,
            )
            .order_by("-effective_date")
            .values_list("effective_date", flat=True)
            .first()
        )

    def get_history(
        self,
        normalized_provider: str,
        rate_type: str,
        date_from: date,
        date_to: date,
    ) -> QuerySet[MartRate]:
        return (
            MartRate.objects.filter(
                normalized_name=normalized_provider,
                rate_type=rate_type,
                effective_date__gte=date_from,
                effective_date__lte=date_to,
            )
            .order_by("effective_date", "ingestion_ts")
        )

    def get_ingested_in_window(
        self,
        window_start: datetime,
        window_end: datetime,
        normalized_provider: str | None = None,
        rate_type: str | None = None,
    ) -> QuerySet[MartRate]:
        """Rates whose ingestion_ts falls in [window_start, window_end)."""
        queryset = MartRate.objects.filter(
            ingestion_ts__gte=window_start,
            ingestion_ts__lt=window_end,
        )
        if normalized_provider:
            queryset = queryset.filter(normalized_name=normalized_provider)
        if rate_type:
            queryset = queryset.filter(rate_type=rate_type)
        return queryset.order_by("-ingestion_ts")

    def existing_external_ids(self, external_ids: list[str]) -> set[str]:
        """Batch lookup for bulk ingest deduplication."""
        if not external_ids:
            return set()
        return set(
            RawResponse.objects.filter(external_id__in=external_ids).values_list("external_id", flat=True)
        )
