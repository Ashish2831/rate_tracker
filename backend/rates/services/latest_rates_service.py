"""Cache-aside facade for GET /api/rates/latest."""

from django.core.cache import cache

from rates.api.serializers import LatestRateSerializer
from rates.repositories.rate_repository import RateRepository
from rates.services.cache import latest_cache_key
from rates.services.parser import normalize_provider_name

CACHE_TTL_SECONDS = 60


class LatestRatesCacheService:
    """Facade — cache-aside with epoch invalidation for latest rates read path."""

    def __init__(
        self,
        repository: RateRepository | None = None,
        cache_backend=cache,
        ttl: int = CACHE_TTL_SECONDS,
    ):
        self.repository = repository or RateRepository()
        self.cache = cache_backend
        self.ttl = ttl

    def get_latest(
        self,
        rate_type: str | None = None,
        provider: str | None = None,
    ) -> tuple[list[dict], bool]:
        """Return (serialized rates, cache_hit). Write path never updates cache — epoch bump on ingest."""
        normalized_provider = normalize_provider_name(provider).lower() if provider else None
        cache_key = latest_cache_key(rate_type, normalized_provider, cache_backend=self.cache)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached, True

        rates = self.repository.get_latest_per_provider(rate_type, normalized_provider)
        data = LatestRateSerializer(rates, many=True).data
        self.cache.set(cache_key, data, self.ttl)
        return data, False
