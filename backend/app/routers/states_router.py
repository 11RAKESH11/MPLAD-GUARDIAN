from fastapi import APIRouter, HTTPException
from backend.app.database import query_db
from backend.app.cache import timed_cache
from decimal import Decimal

router = APIRouter(prefix="/api/v1/states", tags=["State & Regional Intelligence"])

def _f(v, default=0.0):
    """Safe float conversion from PostgreSQL Decimal or None."""
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default

def _i(v, default=0):
    """Safe int conversion."""
    if v is None:
        return default
    try:
        return int(v)
    except (TypeError, ValueError):
        return default

@router.get("")
@timed_cache(300.0)
def list_states():
    rows = query_db("""
    SELECT
        p.state,
        COUNT(*) as total_projects,
        COUNT(DISTINCT p.district) as total_districts,
        COUNT(DISTINCT p.constituency) as total_constituencies,
        COUNT(DISTINCT p.mp_name) as total_mps,
        SUM(p.recommended_amount) as total_recommended,
        SUM(p.sanctioned_amount) as total_sanctioned,
        SUM(p.expenditure_amount) as total_expenditure,
        SUM(CASE WHEN p.status = 'Work Completed' THEN 1 ELSE 0 END) as completed_works,
        SUM(CASE WHEN r.risk_level IN ('CRITICAL', 'HIGH') THEN 1 ELSE 0 END) as high_risk_count,
        AVG(r.overall_risk_score) as avg_risk_score
    FROM projects p
    LEFT JOIN risk_scores r ON p.work_code = r.work_code
    WHERE p.state IS NOT NULL AND p.state != ''
    GROUP BY p.state
    ORDER BY COUNT(*) DESC
    """)

    results = []
    for row in rows:
        d = dict(row)
        tot = _i(d.get("total_projects")) or 1
        sanc = _f(d.get("total_sanctioned")) or 1.0
        spent = _f(d.get("total_expenditure"))
        completed = _i(d.get("completed_works"))

        d["total_projects"] = tot
        d["total_districts"] = _i(d.get("total_districts"))
        d["total_constituencies"] = _i(d.get("total_constituencies"))
        d["total_mps"] = _i(d.get("total_mps"))
        d["total_recommended"] = _f(d.get("total_recommended"))
        d["total_sanctioned"] = sanc
        d["total_expenditure"] = spent
        d["completed_works"] = completed
        d["high_risk_count"] = _i(d.get("high_risk_count"))
        d["avg_risk_score"] = round(_f(d.get("avg_risk_score")), 1)
        d["utilization_pct"] = round((spent / sanc) * 100, 2)
        d["completion_pct"] = round((completed / tot) * 100, 2)
        results.append(d)

    return {"states": results}


@router.get("/{state_name}")
def get_state_detail(state_name: str):
    state_agg = query_db("""
    SELECT
        p.state,
        COUNT(*) as total_projects,
        COUNT(DISTINCT p.district) as total_districts,
        COUNT(DISTINCT p.constituency) as total_constituencies,
        COUNT(DISTINCT p.mp_name) as total_mps,
        SUM(p.recommended_amount) as total_recommended,
        SUM(p.sanctioned_amount) as total_sanctioned,
        SUM(p.disbursed_amount) as total_disbursed,
        SUM(p.expenditure_amount) as total_expenditure,
        SUM(CASE WHEN p.status = 'Work Completed' THEN 1 ELSE 0 END) as completed_works,
        SUM(CASE WHEN r.risk_level = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count,
        SUM(CASE WHEN r.risk_level = 'HIGH' THEN 1 ELSE 0 END) as high_count,
        SUM(CASE WHEN r.risk_level = 'MEDIUM' THEN 1 ELSE 0 END) as medium_count,
        SUM(CASE WHEN r.risk_level = 'LOW' THEN 1 ELSE 0 END) as low_count,
        AVG(r.overall_risk_score) as avg_risk_score
    FROM projects p
    LEFT JOIN risk_scores r ON p.work_code = r.work_code
    WHERE p.state = ?
    GROUP BY p.state
    """, (state_name,), one=True)

    if not state_agg:
        raise HTTPException(status_code=404, detail="State not found")

    overview = dict(state_agg)
    # Safe-cast all numerics
    for k in ("total_recommended", "total_sanctioned", "total_disbursed", "total_expenditure", "avg_risk_score"):
        overview[k] = _f(overview.get(k))
    for k in ("total_projects", "total_districts", "total_constituencies", "total_mps",
               "completed_works", "critical_count", "high_count", "medium_count", "low_count"):
        overview[k] = _i(overview.get(k))

    # Districts breakdown
    districts = query_db("""
    SELECT
        p.district,
        COUNT(*) as total_projects,
        SUM(p.sanctioned_amount) as total_sanctioned,
        SUM(p.expenditure_amount) as total_expenditure,
        SUM(CASE WHEN p.status = 'Work Completed' THEN 1 ELSE 0 END) as completed_works,
        SUM(CASE WHEN r.risk_level IN ('CRITICAL', 'HIGH') THEN 1 ELSE 0 END) as high_risk_count,
        AVG(r.overall_risk_score) as avg_risk_score
    FROM projects p
    LEFT JOIN risk_scores r ON p.work_code = r.work_code
    WHERE p.state = ? AND p.district IS NOT NULL AND p.district != ''
    GROUP BY p.district
    ORDER BY COUNT(*) DESC
    """, (state_name,))

    districts_out = []
    for row in districts:
        d = dict(row)
        d["total_projects"] = _i(d.get("total_projects"))
        d["total_sanctioned"] = _f(d.get("total_sanctioned"))
        d["total_expenditure"] = _f(d.get("total_expenditure"))
        d["completed_works"] = _i(d.get("completed_works"))
        d["high_risk_count"] = _i(d.get("high_risk_count"))
        d["avg_risk_score"] = round(_f(d.get("avg_risk_score")), 1)
        districts_out.append(d)

    # Categories in state
    categories = query_db("""
    SELECT p.category, COUNT(*) as count, SUM(p.sanctioned_amount) as total_sanctioned
    FROM projects p
    WHERE p.state = ?
    GROUP BY p.category
    ORDER BY COUNT(*) DESC
    """, (state_name,))

    categories_out = []
    for row in categories:
        d = dict(row)
        d["count"] = _i(d.get("count"))
        d["total_sanctioned"] = _f(d.get("total_sanctioned"))
        categories_out.append(d)

    # Top MPs in state
    mps = query_db("""
    SELECT
        id, name, house, constituency, mp_type, allocated_limit,
        total_sanctioned_works, total_completed_works, total_sanctioned_amount,
        total_expenditure_amount, avg_risk_score
    FROM mps
    WHERE state = ?
    ORDER BY total_sanctioned_works DESC
    LIMIT 20
    """, (state_name,))

    mps_out = []
    for row in mps:
        d = dict(row)
        d["allocated_limit"] = _f(d.get("allocated_limit"))
        d["total_sanctioned_amount"] = _f(d.get("total_sanctioned_amount"))
        d["total_expenditure_amount"] = _f(d.get("total_expenditure_amount"))
        d["avg_risk_score"] = _f(d.get("avg_risk_score"))
        d["total_sanctioned_works"] = _i(d.get("total_sanctioned_works"))
        d["total_completed_works"] = _i(d.get("total_completed_works"))
        mps_out.append(d)

    return {
        "overview": overview,
        "districts": districts_out,
        "categories": categories_out,
        "mps": mps_out
    }
