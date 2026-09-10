"""
MPLAD GUARDIAN — Background Jobs API Router (Phase 4.5)

Exposes job management endpoints backed by the durable queue service.
"""

from fastapi import APIRouter, HTTPException, Query
from backend.app.queue_service import enqueue_job, get_job, cancel_job, update_job_progress
from backend.app.database import query_db
import math

router = APIRouter(prefix="/api/v1/jobs", tags=["Background Jobs & AI Processing"])


def _batch_analysis_task(job_id: str):
    """Example heavy AI batch analysis task (idempotent)."""
    from backend.app.queue_service import update_job_progress
    count_row = query_db("SELECT COUNT(*) FROM projects", one=True)
    total = count_row[0] if count_row else 96654  # Process all projects
    batch_size = 5000
    processed = 0

    for offset in range(0, total, batch_size):
        # Simulate batch processing work
        time.sleep(0.5)
        processed = min(offset + batch_size, total)
        update_job_progress(job_id, processed, total)

    return {
        "processed_items": processed,
        "total_items": total,
        "anomalies_detected": 15,
        "duplicate_candidates": 4
    }


@router.post("/analyze/batch")
def start_batch_analysis():
    """Enqueue a batch risk analysis job via the durable queue."""
    job_id = enqueue_job("batch_analysis", _batch_analysis_task)
    return {"job_id": job_id, "status": "QUEUED"}


@router.get("/{job_id}")
def get_job_status(job_id: str):
    """Retrieve the status and progress of a background job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    response = {
        "job_id": job["job_id"],
        "status": job["status"],
        "job_type": job["job_type"],
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at"),
        "failed_at": job.get("failed_at"),
        "attempt": job.get("attempt", 1),
        "result": job.get("result"),
        "error": job.get("error_message"),
    }

    # Include progress if available
    if job.get("progress_current") is not None and job.get("progress_total"):
        response["progress"] = {
            "processed": job["progress_current"],
            "total": job["progress_total"],
            "percent": job.get("percent")
        }

    return response


@router.post("/{job_id}/cancel")
def cancel_background_job(job_id: str):
    """Cancel a queued or running job."""
    success = cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled (already completed, failed, or not found)")
    return {"job_id": job_id, "status": "CANCELLED"}


@router.get("")
def list_jobs(
    status: str = Query("", description="Filter by status: QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """List background jobs with pagination."""
    offset = (page - 1) * limit
    where = "1=1"
    params = []

    if status.strip():
        where = "status = ?"
        params.append(status.strip().upper())

    total = query_db(f"SELECT COUNT(*) FROM background_jobs WHERE {where}", params, one=True)[0]
    rows = query_db(
        f"SELECT * FROM background_jobs WHERE {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        params + [limit, offset]
    )
    total_pages = math.ceil(total / limit) if total > 0 else 1

    return {
        "data": [dict(r) for r in rows],
        "meta": {
            "page": page,
            "page_size": limit,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }
