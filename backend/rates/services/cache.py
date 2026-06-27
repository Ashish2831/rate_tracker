"""Redis cache keys and epoch-based invalidation for latest-rates responses."""

from django.core.cache import cache

LATEST_CACHE_PREFIX = "rates:latest"
LATEST_CACHE_EPOCH_KEY = f"{LATEST_CACHE_PREFIX}:epoch"


def get_cache_epoch(cache_backend=cache) -> int:
    """Current cache epoch — embedded in every latest-rates key."""
    epoch = cache_backend.get(LATEST_CACHE_EPOCH_KEY)
    return 0 if epoch is None else int(epoch)


def latest_cache_key(rate_type: str | None = None, cache_backend=cache) -> str:
    """Key includes epoch so invalidation is O(1) via INCR instead of delete_pattern."""
    epoch = get_cache_epoch(cache_backend)
    return f"{LATEST_CACHE_PREFIX}:{epoch}:{rate_type or 'all'}"


def invalidate_rate_caches(cache_backend=cache) -> None:
    """Bump epoch — existing entries become stale and expire via TTL."""
    try:
        cache_backend.incr(LATEST_CACHE_EPOCH_KEY)
    except ValueError:
        # Epoch key missing on first invalidation.
        cache_backend.set(LATEST_CACHE_EPOCH_KEY, 1, timeout=None)
