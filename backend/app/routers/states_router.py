from fastapi import APIRouter, HTTPException
from backend.app.database import query_db
from backend.app.cache import timed_cache

router = APIRouter(prefix="/api/states", tags=["State & Regional Intelligence"])

@router.get("")
@timed_cache(60.0)
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
    JOIN risk_scores r ON p.work_code = r.work_code
    WHERE p.state != ''
    GROUP BY p.state
    ORDER BY total_projects DESC
    """)
    
    results = []
    for r in rows:
        d = dict(r)
        tot = d["total_projects"] or 1
        sanc = d["total_sanctioned"] or 1.0
        spent = d["total_expenditure"] or 0.0
        d["utilization_pct"] = round((spent / sanc) * 100, 2)
        d["completion_pct"] = round((d["completed_works"] / tot) * 100, 2)
        d["avg_risk_score"] = round(d["avg_risk_score"] or 0, 1)
        results.append(d)
        
    return {"states": results}

@router.get("/{state_name}")
def get_state_detail(state_name: str):
    # State Overview
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
    JOIN risk_scores r ON p.work_code = r.work_code
    WHERE p.state = ?
    GROUP BY p.state
    """, (state_name,), one=True)
    
    if not state_agg:
        raise HTTPException(status_code=404, detail="State not found")
        
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
    JOIN risk_scores r ON p.work_code = r.work_code
    WHERE p.state = ? AND p.district != ''
    GROUP BY p.district
    ORDER BY total_projects DESC
    """, (state_name,))
    
    # Categories in state
    categories = query_db("""
    SELECT p.category, COUNT(*) as count, SUM(p.sanctioned_amount) as total_sanctioned
    FROM projects p
    WHERE p.state = ?
    GROUP BY p.category
    ORDER BY count DESC
    """, (state_name,))
    
    # Top MPs in state
    mps = query_db("""
    SELECT 
        id, name, house, constituency, mp_type, allocated_limit, 
        total_sanctioned_works, total_completed_works, total_sanctioned_amount, total_expenditure_amount, avg_risk_score
    FROM mps
    WHERE state = ?
    ORDER BY total_sanctioned_works DESC
    LIMIT 20
    """, (state_name,))
    
    return {
        "overview": dict(state_agg),
        "districts": [dict(d) for d in districts],
        "categories": [dict(c) for c in categories],
        "mps": [dict(m) for m in mps]
    }
