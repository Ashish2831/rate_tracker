"""Ingested-rates query service — 24-hour window defaults and provider normalization."""

from datetime import datetime, timedelta

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from rates.repositories.rate_repository import RateRepository
from rates.services.parser import normalize_provider_name


class IngestedRatesService:
    """SRP — ingested-window query orchestration with rolling 24h default."""

    def __init__(self, repository: RateRepository | None = None):
        self.repository = repository or RateRepository()

    @staticmethod
    def resolve_window(
        window_from: str | datetime | None,
        window_to: str | datetime | None,
        default_hours: int = 24,
    ) -> tuple[datetime, datetime]:
        """Default to the last 24 hours when ?from/?to are omitted."""
        if window_to:
            resolved_to = parse_datetime(window_to) if isinstance(window_to, str) else window_to
        else:
            resolved_to = timezone.now()

        if window_from:
            resolved_from = parse_datetime(window_from) if isinstance(window_from, str) else window_from
        else:
            resolved_from = resolved_to - timedelta(hours=default_hours)

        if resolved_from is None or resolved_to is None:
            raise ValueError("Invalid datetime for ingestion window.")

        return resolved_from, resolved_to

    def get_ingested(
        self,
        window_from: str | datetime | None = None,
        window_to: str | datetime | None = None,
        provider: str | None = None,
        rate_type: str | None = None,
    ):
        window_start, window_end = self.resolve_window(window_from, window_to)
        normalized = normalize_provider_name(provider).lower() if provider else None
        return self.repository.get_ingested_in_window(
            window_start, window_end, normalized, rate_type
        )
