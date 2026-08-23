import time
from functools import wraps
from typing import Any, Callable, Dict, Tuple

_CACHE: Dict[str, Tuple[float, Any]] = {}

def timed_cache(ttl_seconds: float = 60.0):
    """
    High-performance in-memory cache decorator with TTL.
    Instantly returns pre-computed JSON responses in <1ms for analytical aggregations.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            now = time.time()
            if key in _CACHE:
                cached_time, result = _CACHE[key]
                if now - cached_time < ttl_seconds:
                    return result
            result = func(*args, **kwargs)
            _CACHE[key] = (now, result)
            return result
        return wrapper
    return decorator

def clear_cache():
    _CACHE.clear()
