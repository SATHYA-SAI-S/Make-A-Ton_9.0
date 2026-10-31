"""
Redis & In-Memory Caching Layer for Finance & Analytics (P3-T07).
Provides @cached decorator, filter hashing, and event-driven invalidation.
"""
from datetime import date, datetime
from decimal import Decimal
import functools
import hashlib
import json
import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("subscriptiq.analytics.cache")

# Global in-memory cache fallback
_MEMORY_CACHE: Dict[str, Dict[str, Any]] = {}

# Try Redis connection
_REDIS_CLIENT = None
import os
if os.environ.get("USE_REDIS", "false").lower() == "true":
    try:
        import redis
        from backend.app.core.config import settings
        redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
        client = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=0.2, socket_timeout=0.2)
        client.ping()
        _REDIS_CLIENT = client
        logger.info("Connected to Redis cache successfully.")
    except Exception:
        _REDIS_CLIENT = None
        logger.info("Redis unavailable, using high-speed in-memory cache.")
else:
    logger.info("Using high-speed in-memory cache.")


def _json_serializer(obj: Any) -> Any:
    """Helper to serialize Decimal, Date, and DateTime objects."""
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def _generate_cache_key(prefix: str, args: tuple, kwargs: dict) -> str:
    """
    Constructs a deterministic cache key from prefix and sorted arguments.
    Filters out Session, Request, or non-serializable objects.
    """
    clean_kwargs = {}
    for k, v in kwargs.items():
        if k in ("db", "session", "request", "current_user"):
            continue
        if isinstance(v, (date, datetime)):
            clean_kwargs[k] = v.isoformat()
        elif isinstance(v, Decimal):
            clean_kwargs[k] = str(v)
        elif v is not None:
            clean_kwargs[k] = str(v)

    serialized = json.dumps(clean_kwargs, sort_keys=True)
    filter_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]
    return f"subscriptiq:{prefix}:{filter_hash}"


def get_cached_value(key: str) -> Optional[Any]:
    """Retrieves value from Redis or Memory cache."""
    if _REDIS_CLIENT:
        try:
            val = _REDIS_CLIENT.get(key)
            if val:
                return json.loads(val)
        except Exception as e:
            logger.warning(f"Redis get failed: {e}")

    # Check Memory Cache
    entry = _MEMORY_CACHE.get(key)
    if entry:
        now_ts = datetime.now().timestamp()
        if entry["expires_at"] > now_ts:
            return entry["val"]
        else:
            del _MEMORY_CACHE[key]
    return None


def set_cached_value(key: str, value: Any, ttl: int = 300) -> None:
    """Sets value in Redis or Memory cache with expiration."""
    json_str = json.dumps(value, default=_json_serializer)

    if _REDIS_CLIENT:
        try:
            _REDIS_CLIENT.setex(key, ttl, json_str)
            return
        except Exception as e:
            logger.warning(f"Redis set failed: {e}")

    # Fallback to Memory Cache
    now_ts = datetime.now().timestamp()
    _MEMORY_CACHE[key] = {
        "val": json.loads(json_str),
        "expires_at": now_ts + ttl
    }


def invalidate_cache(prefix: Optional[str] = None) -> int:
    """
    Invalidates all cache keys matching a prefix or clears all if prefix is None.
    Returns count of keys deleted.
    """
    count = 0
    pattern = f"subscriptiq:{prefix}:*" if prefix else "subscriptiq:*"

    # Invalidate Redis
    if _REDIS_CLIENT:
        try:
            keys = _REDIS_CLIENT.keys(pattern)
            if keys:
                count += _REDIS_CLIENT.delete(*keys)
        except Exception as e:
            logger.warning(f"Redis invalidate failed: {e}")

    # Invalidate Memory Cache
    keys_to_remove = []
    prefix_filter = f"subscriptiq:{prefix}:" if prefix else "subscriptiq:"
    for k in _MEMORY_CACHE:
        if k.startswith(prefix_filter):
            keys_to_remove.append(k)

    for k in keys_to_remove:
        del _MEMORY_CACHE[k]
        count += 1

    logger.info(f"Invalidated {count} cache keys for prefix '{prefix}'")
    return count


def cached(prefix: str, ttl: int = 300):
    """
    Decorator for caching expensive financial calculations & analytics.
    Automatically handles argument hashing and database parameter exclusion.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = _generate_cache_key(prefix, args, kwargs)
            cached_val = get_cached_value(key)
            if cached_val is not None:
                return cached_val

            result = func(*args, **kwargs)
            set_cached_value(key, result, ttl=ttl)
            return result
        return wrapper
    return decorator


# Automatic Event Invalidation Hooks
def handle_event_invalidation(event) -> None:
    """Invalidates finance and analytics caches when financial data changes."""
    logger.info(f"Received event '{event.event_name}', invalidating caches.")
    invalidate_cache("finance_overview")
    invalidate_cache("finance_kpis")
    invalidate_cache("finance_charts")


# Register event listeners
try:
    from backend.app.shared.events import subscribe
    subscribe("billing.run_completed", handle_event_invalidation)
    subscribe("payment.recorded", handle_event_invalidation)
    subscribe("payment.refunded", handle_event_invalidation)
    subscribe("subscription.updated", handle_event_invalidation)
except ImportError:
    pass
