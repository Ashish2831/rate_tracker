"""Repository — encapsulates ORM queries for rate reads and existence checks (DIP)."""

from datetime import date, datetime

from django.db.models import QuerySet

from rates.models import Rate, RawResponse


class RateRepository:
    """Encapsulates ORM access for rate reads and bulk deduplication lookups."""

    def get_latest_per_provider(
        self,
        rate_type: str | None = None,
        normalized_provider: str | None = None,
    ) -> list[Rate]:
        """One row per (provider, rate_type) — latest effective_date then ingestion_ts."""
        queryset = Rate.objects.select_related("provider").filter(rate_value__isnull=False)
        if rate_type:
            queryset = queryset.filter(rate_type=rate_type)
        if normalized_provider:
            queryset = queryset.filter(provider__normalized_name=normalized_provider)
        # PostgreSQL DISTINCT ON requires matching ORDER BY prefix.
        return list(
            queryset.order_by("provider_id", "rate_type", "-effective_date", "-ingestion_ts").distinct(
                "provider_id", "rate_type"
            )
        )

    def get_filter_options(self) -> tuple[list[str], list[str]]:
        """Distinct provider names and rate types for dashboard filter dropdowns."""
        providers = list(
            Rate.objects.filter(rate_value__isnull=False)
            .values_list("provider__name", flat=True)
            .distinct()
            .order_by("provider__name")
        )
        rate_types = list(
            Rate.objects.filter(rate_value__isnull=False)
            .values_list("rate_type", flat=True)
            .distinct()
            .order_by("rate_type")
        )
        return providers, rate_types

    def get_latest_effective_date(self, normalized_provider: str, rate_type: str) -> date | None:
        """Most recent effective_date for a provider/rate_type — anchors history charts."""
        return (
            Rate.objects.filter(
                provider__normalized_name=normalized_provider,
                rate_type=rate_type,
                rate_value__isnull=False,
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
    ) -> QuerySet[Rate]:
        return (
            Rate.objects.select_related("provider")
            .filter(
                provider__normalized_name=normalized_provider,
                rate_type=rate_type,
                effective_date__gte=date_from,
                effective_date__lte=date_to,
                rate_value__isnull=False,
            )
            .order_by("effective_date", "ingestion_ts")
        )

    def get_ingested_in_window(
        self,
        window_start: datetime,
        window_end: datetime,
        normalized_provider: str | None = None,
        rate_type: str | None = None,
    ) -> QuerySet[Rate]:
        """Rates whose ingestion_ts falls in [window_start, window_end)."""
        queryset = Rate.objects.select_related("provider").filter(
            ingestion_ts__gte=window_start,
            ingestion_ts__lt=window_end,
        )
        if normalized_provider:
            queryset = queryset.filter(provider__normalized_name=normalized_provider)
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
