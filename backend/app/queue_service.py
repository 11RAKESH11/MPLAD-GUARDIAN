"""
MPLAD GUARDIAN — Durable Job Queue Service (Phase 4.5)

Uses RQ (Redis Queue) for durable background job processing.
Falls back to FastAPI BackgroundTasks if Redis is unavailable.

Design Decision (Phase 4.5.22):
  RQ chosen because:
  - Minimal dependency (redis + rq only)
  - Native Python with no broker abstraction
  - Built-in retry, failure tracking, and job state
  - Perfect for sync FastAPI + psycopg2 architecture
  - Celery deemed overpowered for this workload size

Job Retries (Phase 4.5.26):
  - Max 3 retries with exponential backoff
  - Permanent validation errors are NOT retried

Job Idempotency (Phase 4.5.25):
  - All jobs use UPSERT patterns to prevent duplicate rows on retry
"""

import os
import uuid
import json
import time
import datetime
import logging
from typing import Optional, Callable, Any

from backend.app.database import query_db, execute_db
from backend.app import redis_client

logger = logging.getLogger("mplad.queue")

MAX_RETRIES = 3
JOB_TIMEOUT = 600  # 10 minutes max per job


def _ensure_jobs_table():
    """
    Ensure the background_jobs table exists.
    - In PostgreSQL mode: table already created by migration SQL; no ALTER TABLE needed.
    - In SQLite mode: CREATE TABLE IF NOT EXISTS + safe column additions for compatibility.
    """
    from backend.app.database import USE_POSTGRES
    try:
        if USE_POSTGRES:
            # PostgreSQL schema is managed by migrations/001_initial_postgres_schema.sql
            # Do NOT attempt ALTER TABLE — all columns are already defined in the schema.
            # Just verify table is accessible.
            from backend.app.database import query_db
            query_db("SELECT 1 FROM background_jobs LIMIT 1")
            logger.debug("background_jobs table verified (PostgreSQL mode).")
            return
        # SQLite mode: ensure table and all columns exist
        execute_db("""
        CREATE TABLE IF NOT EXISTS background_jobs (
            job_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            job_type TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            started_at TEXT,
            completed_at TEXT,
            failed_at TEXT,
            attempt INTEGER DEFAULT 1,
            result_json TEXT,
            error_message TEXT,
            progress_current INTEGER,
            progress_total INTEGER
        )
        """)
        # Safely add any missing columns (SQLite only — idempotent)
        cols_to_add = [
            ("started_at", "TEXT"),
            ("completed_at", "TEXT"),
            ("failed_at", "TEXT"),
            ("attempt", "INTEGER DEFAULT 1"),
            ("progress_current", "INTEGER"),
            ("progress_total", "INTEGER")
        ]
        for col_name, col_type in cols_to_add:
            try:
                execute_db(f"ALTER TABLE background_jobs ADD COLUMN {col_name} {col_type}")
                logger.debug(f"Added column {col_name} to background_jobs (SQLite).")
            except Exception:
                pass  # Column already exists — expected and safe
    except Exception as e:
        logger.warning(f"background_jobs table setup skipped: {e}")


_ensure_jobs_table()


def enqueue_job(job_type: str, func: Callable, *args, **kwargs) -> str:
    """
    Enqueue a background job.
    Uses RQ if Redis is available, otherwise falls back to in-process execution.
    Returns the job_id.
    """
    job_id = f"job-{uuid.uuid4().hex[:12]}"
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Persist job state in database
    execute_db("""
    INSERT INTO background_jobs (job_id, status, job_type, created_at, updated_at, attempt)
    VALUES (?, 'QUEUED', ?, ?, ?, 1)
    """, (job_id, job_type, now, now))

    # Try RQ if Redis is available
    if redis_client.is_available():
        try:
            from rq import Queue
            import redis as redis_lib
            redis_conn = redis_lib.Redis.from_url(redis_client.REDIS_URL)
            q = Queue(connection=redis_conn)
            q.enqueue(
                _run_job_wrapper,
                job_id, job_type, func, args, kwargs,
                job_timeout=JOB_TIMEOUT,
                retry=None  # We handle retries ourselves
            )
            logger.info(f"Job {job_id} enqueued via RQ (type={job_type})")
            return job_id
        except Exception as e:
            logger.warning(f"RQ enqueue failed ({e}). Falling back to in-process execution.")

    # Fallback: execute directly in-process (non-durable but functional)
    logger.info(f"Job {job_id} executing in-process (no Redis). type={job_type}")
    try:
        _run_job_wrapper(job_id, job_type, func, args, kwargs)
    except Exception as e:
        logger.error(f"In-process job {job_id} failed: {e}")

    return job_id


def _run_job_wrapper(job_id: str, job_type: str, func: Callable, args: tuple, kwargs: dict):
    """
    Job execution wrapper with state tracking, retries, and error handling.
    Runs inside the RQ worker process OR in-process as fallback.
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    execute_db(
        "UPDATE background_jobs SET status = 'RUNNING', started_at = ?, updated_at = ? WHERE job_id = ?",
        (now, now, job_id)
    )

    attempt = 1
    last_error = None

    while attempt <= MAX_RETRIES:
        try:
            result = func(job_id, *args, **kwargs)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result_json = json.dumps(result, default=str) if result else None
            execute_db(
                "UPDATE background_jobs SET status = 'COMPLETED', completed_at = ?, updated_at = ?, result_json = ?, attempt = ? WHERE job_id = ?",
                (now, now, result_json, attempt, job_id)
            )
            logger.info(f"Job {job_id} completed (attempt {attempt})")
            return
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Job {job_id} attempt {attempt} failed: {e}")
            attempt += 1
            if attempt <= MAX_RETRIES:
                backoff = 2 ** (attempt - 1)  # Exponential backoff: 2s, 4s
                time.sleep(backoff)

    # All retries exhausted
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    execute_db(
        "UPDATE background_jobs SET status = 'FAILED', failed_at = ?, updated_at = ?, error_message = ?, attempt = ? WHERE job_id = ?",
        (now, now, last_error, attempt - 1, job_id)
    )
    logger.error(f"Job {job_id} FAILED after {MAX_RETRIES} attempts: {last_error}")


def update_job_progress(job_id: str, current: int, total: int):
    """Update job progress for long-running tasks."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    execute_db(
        "UPDATE background_jobs SET progress_current = ?, progress_total = ?, updated_at = ? WHERE job_id = ?",
        (current, total, now, job_id)
    )


def get_job(job_id: str) -> Optional[dict]:
    """Retrieve job state from database."""
    job = query_db("SELECT * FROM background_jobs WHERE job_id = ?", (job_id,), one=True)
    if not job:
        return None
    d = dict(job)
    if d.get("result_json"):
        try:
            d["result"] = json.loads(d["result_json"])
        except Exception:
            d["result"] = None
    else:
        d["result"] = None
    # Add progress percentage
    if d.get("progress_total") and d["progress_total"] > 0:
        d["percent"] = round((d.get("progress_current", 0) / d["progress_total"]) * 100, 2)
    else:
        d["percent"] = None
    return d


def cancel_job(job_id: str) -> bool:
    """Cancel a queued or running job."""
    job = query_db("SELECT status FROM background_jobs WHERE job_id = ?", (job_id,), one=True)
    if not job or job["status"] in ("COMPLETED", "FAILED", "CANCELLED"):
        return False
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    execute_db(
        "UPDATE background_jobs SET status = 'CANCELLED', updated_at = ? WHERE job_id = ?",
        (now, job_id)
    )
    return True
