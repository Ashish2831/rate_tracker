from django.core.cache import cache


LATEST_CACHE_PREFIX = "rates:latest"
HISTORY_CACHE_PREFIX = "rates:history"


def latest_cache_key(rate_type: str | None = None) -> str:
    return f"{LATEST_CACHE_PREFIX}:{rate_type or 'all'}"


def history_cache_key(provider: str, rate_type: str, date_from: str, date_to: str, page: int) -> str:
    return f"{HISTORY_CACHE_PREFIX}:{provider}:{rate_type}:{date_from}:{date_to}:{page}"


def invalidate_latest_cache(rate_type: str | None = None) -> None:
    if rate_type:
        cache.delete(latest_cache_key(rate_type))
    cache.delete(latest_cache_key(None))


def invalidate_all_rate_caches() -> None:
    cache.delete_pattern(f"{LATEST_CACHE_PREFIX}:*")
    cache.delete_pattern(f"{HISTORY_CACHE_PREFIX}:*")
