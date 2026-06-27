"""Repository — encapsulates ORM queries for rate reads and existence checks (DIP)."""

from datetime import date

from django.db.models import QuerySet

from rates.models import Rate, RawResponse


class RateRepository:
    """Encapsulates ORM access for rate reads and bulk deduplication lookups."""

    def get_latest_per_provider(self, rate_type: str | None = None) -> list[Rate]:
        """One row per (provider, rate_type) — latest effective_date then ingestion_ts."""
        queryset = Rate.objects.select_related("provider").filter(rate_value__isnull=False)
        if rate_type:
            queryset = queryset.filter(rate_type=rate_type)
        # PostgreSQL DISTINCT ON requires matching ORDER BY prefix.
        return list(
            queryset.order_by("provider_id", "rate_type", "-effective_date", "-ingestion_ts").distinct(
                "provider_id", "rate_type"
            )
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

    def existing_external_ids(self, external_ids: list[str]) -> set[str]:
        """Batch lookup for bulk ingest deduplication."""
        if not external_ids:
            return set()
        return set(
            RawResponse.objects.filter(external_id__in=external_ids).values_list("external_id", flat=True)
        )
