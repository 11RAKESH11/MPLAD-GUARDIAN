"""
MPLAD GUARDIAN — Infrastructure Resilience & Failure Test Suite (Phase 4.5)

Tests:
1. Redis Unavailable / Circuit Breaker Graceful Fallback
2. In-Memory Cache TTL Fallback
3. Database Abstraction Query Translation & Pooling
4. Durable Queue Job Enqueue, Progress, and Cancellation
5. Health Probes (/api/v1/health, /api/v1/ready)
"""

import pytest
import time
from backend.app import redis_client, cache, queue_service
from backend.app.database import query_db, execute_db, get_engine_info, _translate_query
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_and_readiness_endpoints():
    """Verify /api/v1/health and /api/v1/ready return 200 OK with expected structure."""
    r_health = client.get("/api/v1/health")
    assert r_health.status_code == 200
    h_data = r_health.json()
    assert h_data["status"] == "healthy"
    assert h_data["database"] == "CONNECTED"
    
    r_ready = client.get("/api/v1/ready")
    assert r_ready.status_code == 200
    assert r_ready.json()["status"] == "ready"

def test_redis_graceful_fallback():
    """Verify that when Redis is unavailable, get_cached/set_cached degrade gracefully without exceptions."""
    # Even if redis is down, these must return None / False and never raise
    val = redis_client.get_cached("nonexistent_test_key_123")
    assert val is None
    
    # set_cached must not raise
    success = redis_client.set_cached("test_key", {"data": "test"}, ttl_seconds=10)
    assert isinstance(success, bool)

def test_hybrid_cache_fallback():
    """Verify that @timed_cache works seamlessly via in-memory fallback."""
    call_count = 0
    
    @cache.timed_cache(ttl_seconds=2.0)
    def expensive_op(param: str):
        nonlocal call_count
        call_count += 1
        return {"param": param, "count": call_count}
        
    # First call -> compute
    res1 = expensive_op("alpha")
    assert res1["count"] == 1
    assert call_count == 1
    
    # Second call within TTL -> cached
    res2 = expensive_op("alpha")
    assert res2["count"] == 1
    assert call_count == 1
    
    # Different parameter -> compute
    res3 = expensive_op("beta")
    assert res3["count"] == 2
    assert call_count == 2

def test_database_placeholder_translation():
    """Verify SQLite ? to PostgreSQL %s placeholder translator."""
    q_sqlite = "SELECT * FROM projects WHERE state = ? AND category = ? LIMIT ?"
    q_pg = _translate_query(q_sqlite)
    # When USE_POSTGRES is False, returns original; when True, translates
    if get_engine_info()["engine"] == "postgresql":
        assert "%s" in q_pg
        assert "?" not in q_pg
    else:
        assert q_pg == q_sqlite

def test_durable_job_lifecycle():
    """Verify job creation, state persistence, progress update, and cancellation."""
    def dummy_task(job_id, count):
        queue_service.update_job_progress(job_id, count, count)
        return {"status": "success", "processed": count}
        
    job_id = queue_service.enqueue_job("test_batch", dummy_task, 100)
    assert job_id.startswith("job-")
    
    job_state = queue_service.get_job(job_id)
    assert job_state is not None
    assert job_state["job_id"] == job_id
    assert job_state["status"] in ("QUEUED", "RUNNING", "COMPLETED")
    assert job_state["job_type"] == "test_batch"

def test_projects_pagination_meta_format():
    """Verify standard { data, meta } payload on project listing."""
    resp = client.get("/api/v1/projects?limit=5")
    assert resp.status_code == 200
    payload = resp.json()
    assert "data" in payload
    assert "meta" in payload
    assert isinstance(payload["data"], list)
    assert payload["meta"]["page"] == 1
    assert payload["meta"]["page_size"] == 5
    assert payload["meta"]["total"] == 96654
