"""
MPLAD GUARDIAN — Redis Client with Graceful Degradation (Phase 4.5)

If Redis is unavailable, the application continues to function
using direct database queries. No crash, no unhandled exception.

Design decision (Phase 4.5.22):
  RQ (Redis Queue) chosen over Celery/ARQ/Dramatiq because:
  - Simplest dependency footprint (only redis + rq)
  - Native Python, no broker abstraction layer
  - Perfect fit for the current synchronous FastAPI + psycopg2 architecture
  - Bounded retry and failure handling built-in
  - Celery is overpowered for this workload
"""

import os
import json
import logging
from typing import Any, Optional

logger = logging.getLogger("mplad.redis")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_CONNECT_TIMEOUT = int(os.getenv("REDIS_CONNECT_TIMEOUT", "3"))
REDIS_SOCKET_TIMEOUT = int(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))

_redis_client = None
_redis_available = False


def _init_redis():
    """Initialize Redis connection pool. Safe to call multiple times."""
    global _redis_client, _redis_available
    try:
        import redis
        _redis_client = redis.Redis.from_url(
            REDIS_URL,
            socket_connect_timeout=REDIS_CONNECT_TIMEOUT,
            socket_timeout=REDIS_SOCKET_TIMEOUT,
            decode_responses=True,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        # Lightweight connectivity test
        _redis_client.ping()
        _redis_available = True
        logger.info(f"Redis connected: {REDIS_URL}")
    except Exception as e:
        _redis_available = False
        _redis_client = None
        logger.warning(f"Redis unavailable ({e}). Application will continue without Redis caching.")


# Attempt connection on import
_init_redis()


def is_available() -> bool:
    """Check if Redis is currently reachable."""
    global _redis_available
    if not _redis_client:
        return False
    try:
        _redis_client.ping()
        _redis_available = True
        return True
    except Exception:
        _redis_available = False
        return False


def get_cached(key: str) -> Optional[Any]:
    """
    Retrieve a cached value from Redis.
    Returns None if Redis is unavailable or key doesn't exist.
    Never raises.
    """
    if not _redis_client or not _redis_available:
        return None
    try:
        raw = _redis_client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as e:
        logger.warning(f"Redis GET failed for key '{key}': {e}")
        return None


def set_cached(key: str, value: Any, ttl_seconds: int = 120) -> bool:
    """
    Store a value in Redis with TTL.
    Returns True on success, False if Redis unavailable.
    Never raises.
    """
    if not _redis_client or not _redis_available:
        return False
    try:
        serialized = json.dumps(value, default=str)
        _redis_client.setex(key, ttl_seconds, serialized)
        return True
    except Exception as e:
        logger.warning(f"Redis SET failed for key '{key}': {e}")
        return False


def invalidate(pattern: str) -> int:
    """
    Invalidate cache entries matching a pattern (e.g., 'dashboard:*').
    Returns count of deleted keys. 0 if Redis unavailable.
    Never raises.
    """
    if not _redis_client or not _redis_available:
        return 0
    try:
        keys = _redis_client.keys(pattern)
        if keys:
            return _redis_client.delete(*keys)
        return 0
    except Exception as e:
        logger.warning(f"Redis invalidation failed for pattern '{pattern}': {e}")
        return 0


def invalidate_dashboard():
    """Invalidate all dashboard-related cache entries."""
    invalidate("dashboard:*")
    invalidate("state:*")
    invalidate("analytics:*")
    invalidate("risk:*")


def get_redis_info() -> dict:
    """Returns Redis status for health checks."""
    return {
        "redis_url": REDIS_URL.split("@")[-1] if "@" in REDIS_URL else REDIS_URL,
        "available": is_available(),
        "mode": "redis" if _redis_available else "in-memory-fallback",
    }
