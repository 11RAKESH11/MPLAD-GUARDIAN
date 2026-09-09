"""
MPLAD GUARDIAN — Resilient Database Abstraction Layer (Phase 4.5)

Supports dual-mode operation:
  - PostgreSQL (via psycopg2 ThreadedConnectionPool) — production target
  - SQLite (embedded WAL mode) — development & rollback fallback

DATABASE_URL env var determines mode:
  - Starts with 'postgresql://' → PostgreSQL mode
  - Otherwise → SQLite mode (uses DATABASE_PATH)

Design decisions (Phase 4.5.4):
  - psycopg2 chosen over asyncpg: FastAPI routers use sync `def`, not `async def`.
    psycopg2 is battle-tested, widely deployed, and avoids async-to-sync bridging.
  - SQLAlchemy Core was considered but rejected to preserve existing raw SQL queries
    across all routers without a full ORM rewrite.
  - Connection pooling: ThreadedConnectionPool (min=2, max=10) prevents connection-per-request.
  - Query placeholder translation: SQLite uses ?, PostgreSQL uses %s.
    Handled transparently in query_db/execute_db.
"""

import sqlite3
import os
import logging
import atexit
from typing import Any, Optional, Tuple, List, Union
from contextlib import contextmanager

logger = logging.getLogger("mplad.database")

# ─── Configuration ───────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "")
DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "mplad.db"))
DB_POOL_MIN = int(os.getenv("DB_POOL_MIN", "2"))
DB_POOL_MAX = int(os.getenv("DB_POOL_MAX", "10"))
DB_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", "10"))

# ─── Engine Detection ────────────────────────────────────────────────────────
USE_POSTGRES = DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")

# ─── PostgreSQL Connection Pool ──────────────────────────────────────────────
_pg_pool = None

if USE_POSTGRES:
    try:
        import psycopg2
        import psycopg2.pool
        import psycopg2.extras
        _pg_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=DB_POOL_MIN,
            maxconn=DB_POOL_MAX,
            dsn=DATABASE_URL,
            connect_timeout=DB_CONNECT_TIMEOUT,
            options="-c statement_timeout=30000"  # 30s query timeout
        )
        logger.info(f"PostgreSQL pool initialized (min={DB_POOL_MIN}, max={DB_POOL_MAX})")
    except Exception as e:
        logger.error(f"PostgreSQL pool initialization failed: {e}. Falling back to SQLite.")
        USE_POSTGRES = False
        _pg_pool = None

def _shutdown_pool():
    global _pg_pool
    if _pg_pool:
        try:
            _pg_pool.closeall()
            logger.info("PostgreSQL pool closed cleanly.")
        except Exception:
            pass

atexit.register(_shutdown_pool)


# ─── SQLite Connection Factory ───────────────────────────────────────────────
def _get_sqlite_connection():
    conn = sqlite3.connect(DATABASE_PATH, timeout=20.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA cache_size = -64000;")
    conn.execute("PRAGMA temp_store = MEMORY;")
    conn.execute("PRAGMA mmap_size = 30000000000;")
    return conn


# ─── Helper: Translate ? placeholders to %s for PostgreSQL ───────────────────
def _translate_query(query: str) -> str:
    """
    Translates SQLite-style ? placeholders to PostgreSQL %s placeholders.
    Handles quoted strings carefully to avoid false substitutions.
    """
    if not USE_POSTGRES:
        return query
    result = []
    in_single_quote = False
    in_double_quote = False
    for ch in query:
        if ch == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            result.append(ch)
        elif ch == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            result.append(ch)
        elif ch == '?' and not in_single_quote and not in_double_quote:
            result.append('%s')
        else:
            result.append(ch)
    return ''.join(result)


# ─── PostgreSQL Row Wrapper (dict-like, compatible with sqlite3.Row) ─────────
class PgRow(dict):
    """Makes psycopg2 RealDictRow behave like sqlite3.Row for read access."""
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


# ─── Core Query Functions ────────────────────────────────────────────────────
def query_db(query: str, args: Union[tuple, list] = (), one: bool = False):
    """
    Execute a read query and return results.
    Supports both SQLite and PostgreSQL transparently.
    """
    translated = _translate_query(query)

    if USE_POSTGRES and _pg_pool:
        conn = None
        try:
            conn = _pg_pool.getconn()
            import psycopg2.extras
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(translated, tuple(args))
            rows = cur.fetchall()
            cur.close()
            result = [PgRow(r) for r in rows]
            return (result[0] if result else None) if one else result
        except Exception as e:
            logger.error(f"PostgreSQL query error: {e}")
            raise
        finally:
            if conn:
                _pg_pool.putconn(conn)
    else:
        conn = _get_sqlite_connection()
        try:
            cur = conn.cursor()
            cur.execute(query, tuple(args))
            r = cur.fetchall()
            return (r[0] if r else None) if one else r
        finally:
            conn.close()


def execute_db(query: str, args: Union[tuple, list] = ()):
    """
    Execute a write query (INSERT, UPDATE, DELETE).
    Supports both SQLite and PostgreSQL transparently.
    """
    translated = _translate_query(query)

    if USE_POSTGRES and _pg_pool:
        conn = None
        try:
            conn = _pg_pool.getconn()
            cur = conn.cursor()
            cur.execute(translated, tuple(args))
            conn.commit()
            cur.close()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"PostgreSQL execute error: {e}")
            raise
        finally:
            if conn:
                _pg_pool.putconn(conn)
    else:
        conn = _get_sqlite_connection()
        try:
            cur = conn.cursor()
            cur.execute(query, tuple(args))
            conn.commit()
        finally:
            conn.close()


@contextmanager
def get_transaction():
    """
    Context manager for atomic multi-statement transactions.
    Usage:
        with get_transaction() as (conn, cursor):
            cursor.execute(...)
            cursor.execute(...)
        # auto-commits on success, rolls back on exception
    """
    if USE_POSTGRES and _pg_pool:
        conn = _pg_pool.getconn()
        try:
            cur = conn.cursor()
            yield conn, cur
            conn.commit()
            cur.close()
        except Exception:
            conn.rollback()
            raise
        finally:
            _pg_pool.putconn(conn)
    else:
        conn = _get_sqlite_connection()
        try:
            cur = conn.cursor()
            yield conn, cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def get_db():
    """FastAPI dependency for database connections (legacy compatibility)."""
    if USE_POSTGRES and _pg_pool:
        conn = _pg_pool.getconn()
        try:
            yield conn
        finally:
            _pg_pool.putconn(conn)
    else:
        conn = _get_sqlite_connection()
        try:
            yield conn
        finally:
            conn.close()


def get_engine_info() -> dict:
    """Returns current database engine configuration for health checks."""
    return {
        "engine": "postgresql" if USE_POSTGRES else "sqlite",
        "database_url": DATABASE_URL[:30] + "..." if USE_POSTGRES and len(DATABASE_URL) > 30 else ("sqlite:" + DATABASE_PATH),
        "pool_min": DB_POOL_MIN if USE_POSTGRES else "N/A",
        "pool_max": DB_POOL_MAX if USE_POSTGRES else "N/A",
        "connect_timeout": DB_CONNECT_TIMEOUT if USE_POSTGRES else 20,
    }

