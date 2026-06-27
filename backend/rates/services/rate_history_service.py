from datetime import date, timedelta

from django.utils import timezone
from django.utils.dateparse import parse_date

from rates.repositories.rate_repository import RateRepository
from rates.services.parser import normalize_provider_name


class RateHistoryService:
    """SRP — history query orchestration with date-range defaults."""

    def __init__(self, repository: RateRepository | None = None):
        self.repository = repository or RateRepository()

    @staticmethod
    def resolve_date_range(
        date_from: str | date | None,
        date_to: str | date | None,
        default_days: int = 30,
    ) -> tuple[date, date]:
        if date_to:
            resolved_to = parse_date(date_to) if isinstance(date_to, str) else date_to
        else:
            resolved_to = timezone.now().date()

        if date_from:
            resolved_from = parse_date(date_from) if isinstance(date_from, str) else date_from
        else:
            resolved_from = resolved_to - timedelta(days=default_days)

        return resolved_from, resolved_to

    def get_history(
        self,
        provider: str,
        rate_type: str,
        date_from: str | date | None = None,
        date_to: str | date | None = None,
    ):
        normalized = normalize_provider_name(provider).lower()
        resolved_from, resolved_to = self.resolve_date_range(date_from, date_to)
        return self.repository.get_history(normalized, rate_type, resolved_from, resolved_to)
