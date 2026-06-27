"""Redis cache keys and invalidation for latest-rates responses."""

from django.core.cache import cache

LATEST_CACHE_PREFIX = "rates:latest"


def latest_cache_key(rate_type: str | None = None) -> str:
    return f"{LATEST_CACHE_PREFIX}:{rate_type or 'all'}"


def invalidate_rate_caches() -> None:
    """Clear all latest-rate cache entries after any ingest."""
    cache.delete_pattern(f"{LATEST_CACHE_PREFIX}:*")
