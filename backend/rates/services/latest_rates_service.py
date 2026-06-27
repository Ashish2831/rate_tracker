from typing import Callable

from django.core.cache import cache

from rates.api.serializers import LatestRateSerializer
from rates.models import Rate
from rates.repositories.rate_repository import RateRepository
from rates.services.cache import latest_cache_key

CACHE_TTL_SECONDS = 60


class LatestRatesCacheService:
    """Facade — cache-aside pattern for latest rates read path (SRP)."""

    def __init__(
        self,
        repository: RateRepository | None = None,
        cache_backend=cache,
        ttl: int = CACHE_TTL_SECONDS,
    ):
        self.repository = repository or RateRepository()
        self.cache = cache_backend
        self.ttl = ttl

    @staticmethod
    def serialize_rates(rates: list[Rate]) -> list[dict]:
        return LatestRateSerializer(
            [
                {
                    "provider": rate.provider.name,
                    "rate_type": rate.rate_type,
                    "rate_value": rate.rate_value,
                    "effective_date": rate.effective_date,
                    "ingestion_ts": rate.ingestion_ts,
                    "currency": rate.currency,
                }
                for rate in rates
            ],
            many=True,
        ).data

    def get_latest(self, rate_type: str | None = None) -> tuple[list[dict], bool]:
        cache_key = latest_cache_key(rate_type)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached, True

        rates = self.repository.get_latest_per_provider(rate_type)
        data = self.serialize_rates(rates)
        self.cache.set(cache_key, data, self.ttl)
        return data, False
