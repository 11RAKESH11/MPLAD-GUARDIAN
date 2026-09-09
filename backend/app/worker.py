"""
MPLAD GUARDIAN — Standalone RQ Worker Daemon (Phase 4.5)

Runs as a separate process/container consuming jobs from the Redis-backed queue.
Designed to be launched as:
    python -m backend.app.worker

In Docker Compose, this runs as the 'worker' service.
"""

import os
import sys
import logging

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WORKER] %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("mplad.worker")


def main():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    try:
        import redis
        from rq import Worker, Queue

        redis_conn = redis.Redis.from_url(redis_url)
        redis_conn.ping()
        logger.info(f"Worker connected to Redis: {redis_url}")

        queues = [Queue(connection=redis_conn)]
        worker = Worker(queues, connection=redis_conn)
        logger.info("RQ Worker started. Listening for jobs...")
        worker.work()
    except ImportError as e:
        logger.error(f"RQ library not installed or incompatible. Run: pip install rq. Detail: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Worker startup failed: {e}")
        logger.info("Worker will retry in 10 seconds...")
        import time
        time.sleep(10)
        main()  # Simple retry loop


if __name__ == "__main__":
    main()
