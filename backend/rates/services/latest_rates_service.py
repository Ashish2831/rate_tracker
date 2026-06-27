"""Cache-aside facade for GET /api/rates/latest."""

from django.core.cache import cache

from rates.api.serializers import LatestRateSerializer
from rates.repositories.rate_repository import RateRepository
from rates.services.cache import latest_cache_key

CACHE_TTL_SECONDS = 60


class LatestRatesCacheService:
    """Facade — cache-aside pattern for latest rates read path."""

    def __init__(
        self,
        repository: RateRepository | None = None,
        cache_backend=cache,
        ttl: int = CACHE_TTL_SECONDS,
    ):
        self.repository = repository or RateRepository()
        self.cache = cache_backend
        self.ttl = ttl

    def get_latest(self, rate_type: str | None = None) -> tuple[list[dict], bool]:
        cache_key = latest_cache_key(rate_type)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached, True

        rates = self.repository.get_latest_per_provider(rate_type)
        data = LatestRateSerializer(rates, many=True).data
        self.cache.set(cache_key, data, self.ttl)
        return data, False
