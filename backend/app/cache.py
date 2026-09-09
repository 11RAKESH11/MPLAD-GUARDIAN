"""
MPLAD GUARDIAN — Hybrid Cache Layer (Phase 4.5)

Strategy:
  1. If Redis is available → use Redis with versioned keys and TTL
  2. If Redis is down → fall back to local in-process TTL dictionary
  3. Never crash. Never serve stale data beyond TTL.

TTL Decisions (Phase 4.5.18):
  - Dashboard overview: 120s (frequently accessed, moderate staleness OK)
  - State/District analytics: 300s (aggregated, changes infrequently)
  - Risk summary: 60s (important to reflect recent updates quickly)
  - Map data: 300s (expensive aggregation, acceptable staleness)

Cache Key Design (Phase 4.5.19):
  - Keys include function name + arguments hash for uniqueness
  - Format: "mplad:{func_name}:{args_hash}"
  - Different query parameters → different cache entries
"""

import time
import hashlib
import logging
from functools import wraps
from typing import Any, Callable, Dict, Tuple

from backend.app import redis_client

logger = logging.getLogger("mplad.cache")

# ─── Local In-Memory Fallback Cache ──────────────────────────────────────────
_LOCAL_CACHE: Dict[str, Tuple[float, float, Any]] = {}  # key → (timestamp, ttl, value)


def _build_cache_key(func_name: str, args, kwargs) -> str:
    """Build a deterministic, namespaced cache key."""
    raw = f"{func_name}:{str(args)}:{str(sorted(kwargs.items()) if kwargs else '')}"
    key_hash = hashlib.md5(raw.encode()).hexdigest()[:12]
    return f"mplad:{func_name}:{key_hash}"


def timed_cache(ttl_seconds: float = 60.0):
    """
    Hybrid cache decorator with Redis + local fallback.
    Instantly returns pre-computed JSON responses in <1ms for analytical aggregations.
    Falls back to local dict cache if Redis is unavailable.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = _build_cache_key(func.__name__, args, kwargs)
            now = time.time()

            # ─── Try Redis First ────────────────────────────────
            if redis_client.is_available():
                cached = redis_client.get_cached(key)
                if cached is not None:
                    return cached
                # Cache miss → compute and store
                result = func(*args, **kwargs)
                redis_client.set_cached(key, result, ttl_seconds=int(ttl_seconds))
                return result

            # ─── Fall back to Local Cache ───────────────────────
            if key in _LOCAL_CACHE:
                cached_time, cached_ttl, cached_result = _LOCAL_CACHE[key]
                if now - cached_time < cached_ttl:
                    return cached_result

            result = func(*args, **kwargs)
            _LOCAL_CACHE[key] = (now, ttl_seconds, result)
            return result

        return wrapper
    return decorator


def clear_cache():
    """Clear both Redis and local cache entries."""
    _LOCAL_CACHE.clear()
    redis_client.invalidate_dashboard()
    logger.info("All caches cleared (Redis + local).")


def invalidate_on_mutation():
    """
    Call after data mutations (alert status change, ingestion, risk recalc)
    to invalidate stale analytics cache.
    """
    _LOCAL_CACHE.clear()
    redis_client.invalidate_dashboard()
    logger.info("Cache invalidated after data mutation.")
