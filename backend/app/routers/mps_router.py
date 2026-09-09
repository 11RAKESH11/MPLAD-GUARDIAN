from fastapi import APIRouter, HTTPException, Query
from backend.app.database import query_db
import math

router = APIRouter(prefix="/api/v1/mps", tags=["Parliamentarian Intelligence Dossiers"])

@router.get("")
def list_mps(
    q: str = Query("", description="Search MP by name, state, or constituency"),
    house: str = Query("", description="LOK_SABHA or RAJYA_SABHA"),
    state: str = Query("", description="Filter by state"),
    sort_by: str = Query("total_sanctioned_works", description="Sort by total_sanctioned_works, allocated_limit, total_expenditure_amount, avg_risk_score"),
    order: str = Query("desc", description="asc or desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100)
):
    offset = (page - 1) * limit
    where_clauses = ["1=1"]
    params = []
    
    if q.strip():
        search_term = f"%{q.strip()}%"
        where_clauses.append("(name LIKE ? OR state LIKE ? OR constituency LIKE ?)")
        params.extend([search_term, search_term, search_term])
        
    if house.strip():
        where_clauses.append("house = ?")
        params.append(house.strip().upper())
        
    if state.strip():
        where_clauses.append("state = ?")
        params.append(state.strip())
        
    where_sql = " AND ".join(where_clauses)
    
    valid_sorts = {
        "total_sanctioned_works": "total_sanctioned_works",
        "total_recommended_works": "total_recommended_works",
        "total_completed_works": "total_completed_works",
        "allocated_limit": "allocated_limit",
        "total_sanctioned_amount": "total_sanctioned_amount",
        "total_expenditure_amount": "total_expenditure_amount",
        "avg_risk_score": "avg_risk_score",
        "name": "name"
    }
    sort_col = valid_sorts.get(sort_by, "total_sanctioned_works")
    sort_dir = "ASC" if order.lower() == "asc" else "DESC"
    
    count_sql = f"SELECT COUNT(*) FROM mps WHERE {where_sql}"
    total_records = query_db(count_sql, params, one=True)[0]
    
    records_sql = f"""
    SELECT * FROM mps
    WHERE {where_sql}
    ORDER BY {sort_col} {sort_dir}
    LIMIT ? OFFSET ?
    """
    rows = query_db(records_sql, params + [limit, offset])
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 1
    
    return {
        "data": [dict(r) for r in rows],
        "meta": {
            "page": page,
            "page_size": limit,
            "total": total_records,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

@router.get("/{mp_id}")
def get_mp_detail(mp_id: str):
    mp = query_db("SELECT * FROM mps WHERE id = ? OR name = ?", (mp_id, mp_id), one=True)
    if not mp:
        raise HTTPException(status_code=404, detail="MP record not found")
        
    mp_data = dict(mp)
    
    # Fetch projects sponsored by this MP
    projects = query_db("""
    SELECT 
        p.id, p.work_code, p.work_type, p.state, p.district, p.category, p.status,
        p.recommended_amount, p.sanctioned_amount, p.expenditure_amount, p.utilization_pct,
        p.recommended_date, p.sanction_date, p.completion_date,
        r.overall_risk_score, r.risk_level
    FROM projects p
    LEFT JOIN risk_scores r ON p.work_code = r.work_code
    WHERE p.mp_name = ?
    ORDER BY p.sanction_date DESC
    LIMIT 100
    """, (mp_data["name"],))
    
    # Category portfolio breakdown
    cat_breakdown = query_db("""
    SELECT category, COUNT(*) as count, SUM(sanctioned_amount) as total_sanctioned
    FROM projects
    WHERE mp_name = ?
    GROUP BY category
    ORDER BY count DESC
    """, (mp_data["name"],))
    
    mp_data["projects"] = [dict(p) for p in projects]
    mp_data["category_portfolio"] = [dict(c) for c in cat_breakdown]
    
    return mp_data
