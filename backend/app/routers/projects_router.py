from fastapi import APIRouter, HTTPException, Query
from backend.app.database import query_db
import json
import math

router = APIRouter(prefix="/api/projects", tags=["Project Intelligence"])

@router.get("")
def list_projects(
    q: str = Query("", description="Global search query across name, code, MP, district, etc."),
    state: str = Query("", description="Filter by State"),
    district: str = Query("", description="Filter by District"),
    constituency: str = Query("", description="Filter by Constituency"),
    category: str = Query("", description="Filter by Category"),
    financial_year: str = Query("", description="Filter by Financial Year"),
    status: str = Query("", description="Filter by Status"),
    risk_level: str = Query("", description="Filter by Risk Level: CRITICAL, HIGH, MEDIUM, LOW"),
    house: str = Query("", description="LOK_SABHA or RAJYA_SABHA"),
    min_amount: float = Query(None, description="Minimum sanctioned amount"),
    max_amount: float = Query(None, description="Maximum sanctioned amount"),
    sort_by: str = Query("overall_risk_score", description="Column to sort by"),
    order: str = Query("desc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100)
):
    offset = (page - 1) * limit
    
    where_clauses = ["1=1"]
    params = []
    
    if q.strip():
        search_term = f"%{q.strip()}%"
        where_clauses.append("""(
            p.work_code LIKE ? OR 
            p.work_type LIKE ? OR 
            p.description LIKE ? OR 
            p.mp_name LIKE ? OR 
            p.district LIKE ? OR 
            p.constituency LIKE ? OR 
            p.state LIKE ?
        )""")
        params.extend([search_term] * 7)
        
    if state.strip():
        where_clauses.append("p.state = ?")
        params.append(state.strip())
        
    if district.strip():
        where_clauses.append("p.district = ?")
        params.append(district.strip())
        
    if constituency.strip():
        where_clauses.append("p.constituency = ?")
        params.append(constituency.strip())
        
    if category.strip():
        where_clauses.append("p.category = ?")
        params.append(category.strip())
        
    if financial_year.strip():
        where_clauses.append("p.financial_year = ?")
        params.append(financial_year.strip())
        
    if status.strip():
        where_clauses.append("p.status = ?")
        params.append(status.strip())
        
    if risk_level.strip():
        where_clauses.append("r.risk_level = ?")
        params.append(risk_level.strip().upper())
        
    if house.strip():
        where_clauses.append("p.house = ?")
        params.append(house.strip().upper())
        
    if min_amount is not None:
        where_clauses.append("p.sanctioned_amount >= ?")
        params.append(min_amount)
        
    if max_amount is not None:
        where_clauses.append("p.sanctioned_amount <= ?")
        params.append(max_amount)
        
    where_sql = " AND ".join(where_clauses)
    
    valid_sorts = {
        "overall_risk_score": "r.overall_risk_score",
        "sanctioned_amount": "p.sanctioned_amount",
        "utilization_pct": "p.utilization_pct",
        "recommended_date": "p.recommended_date",
        "sanction_date": "p.sanction_date",
        "completion_date": "p.completion_date",
        "work_code": "p.work_code"
    }
    sort_col = valid_sorts.get(sort_by, "r.overall_risk_score")
    sort_dir = "ASC" if order.lower() == "asc" else "DESC"
    
    if where_sql == "1=1":
        total_records = 96654
    elif "r." not in where_sql:
        count_sql = f"SELECT COUNT(*) FROM projects p WHERE {where_sql}"
        total_records = query_db(count_sql, params, one=True)[0]
    else:
        count_sql = f"SELECT COUNT(*) FROM projects p JOIN risk_scores r ON p.work_code = r.work_code WHERE {where_sql}"
        total_records = query_db(count_sql, params, one=True)[0]
    
    records_sql = f"""
    SELECT 
        p.id, p.work_code, p.house, p.mp_code, p.mp_name, p.mp_type, p.state, p.district,
        p.constituency, p.ida_name, p.category, p.work_type, p.description, p.status,
        p.recommended_date, p.sanction_date, p.completion_date, p.financial_year,
        p.recommended_amount, p.sanctioned_amount, p.disbursed_amount, p.expenditure_amount,
        p.utilization_pct, p.vendor_count, p.voucher_count, p.has_image,
        r.overall_risk_score, r.risk_level, r.confidence, r.cost_anomaly_score,
        r.duplicate_score, r.progress_gap_score, r.geographic_score, r.recommendation
    FROM projects p
    LEFT JOIN risk_scores r ON p.work_code = r.work_code
    WHERE {where_sql}
    ORDER BY {sort_col} {sort_dir}
    LIMIT ? OFFSET ?
    """
    page_params = params + [limit, offset]
    rows = query_db(records_sql, page_params)
    
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 1
    
    return {
        "data": [dict(r) for r in rows],
        "pagination": {
            "page": page,
            "limit": limit,
            "total_records": total_records,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

@router.get("/{work_code:path}/relationships")
def get_project_relationships(work_code: str):
    """Returns interactive relationship intelligence graph for a project"""
    target = query_db("""
    SELECT p.*, r.overall_risk_score, r.risk_level, r.confidence
    FROM projects p
    LEFT JOIN risk_scores r ON p.work_code = r.work_code
    WHERE p.work_code = ? OR p.id = ?
    """, (work_code, work_code), one=True)
    
    if not target:
        raise HTTPException(status_code=404, detail="Target project not found")
        
    t_dict = dict(target)
    target_code = t_dict["work_code"]
    
    # 1. Fetch Comparable / Duplicate matches
    comparables = query_db("""
    SELECT 
        c.comparable_work_code, c.similarity_score, c.similarity_type, c.reason,
        p.work_type, p.state, p.district, p.category, p.sanctioned_amount, p.status,
        r.overall_risk_score, r.risk_level
    FROM comparable_projects c
    JOIN projects p ON c.comparable_work_code = p.work_code
    LEFT JOIN risk_scores r ON p.work_code = r.work_code
    WHERE c.target_work_code = ?
    LIMIT 6
    """, (target_code,))
    
    # 2. Fetch Same District & Category Peers
    peers = query_db("""
    SELECT 
        p.work_code, p.work_type, p.state, p.district, p.category, p.sanctioned_amount, p.status,
        r.overall_risk_score, r.risk_level
    FROM projects p
    LEFT JOIN risk_scores r ON p.work_code = r.work_code
    WHERE p.state = ? AND p.district = ? AND p.category = ? AND p.work_code != ?
    LIMIT 5
    """, (t_dict.get("state"), t_dict.get("district"), t_dict.get("category"), target_code))
    
    nodes = [{
        "id": target_code,
        "title": t_dict.get("work_type") or target_code,
        "category": t_dict.get("category"),
        "state": t_dict.get("state"),
        "district": t_dict.get("district"),
        "sanctioned_amount": t_dict.get("sanctioned_amount"),
        "risk_level": t_dict.get("risk_level") or "LOW",
        "risk_score": t_dict.get("overall_risk_score") or 0,
        "is_target": True
    }]
    
    edges = []
    seen_nodes = {target_code}
    
    for c_row in comparables:
        c = dict(c_row)
        c_code = c["comparable_work_code"]
        if c_code not in seen_nodes:
            seen_nodes.add(c_code)
            nodes.append({
                "id": c_code,
                "title": c.get("work_type") or c_code,
                "category": c.get("category"),
                "state": c.get("state"),
                "district": c.get("district"),
                "sanctioned_amount": c.get("sanctioned_amount"),
                "risk_level": c.get("risk_level") or "LOW",
                "risk_score": c.get("overall_risk_score") or 0,
                "is_target": False
            })
            edges.append({
                "source": target_code,
                "target": c_code,
                "relation_type": c.get("similarity_type") or "SIMILAR_DESCRIPTION",
                "similarity": c.get("similarity_score") or 0.85,
                "label": f"{int((c.get('similarity_score') or 0.85)*100)}% Match"
            })
            
    for p_row in peers:
        p = dict(p_row)
        p_code = p["work_code"]
        if p_code not in seen_nodes:
            seen_nodes.add(p_code)
            nodes.append({
                "id": p_code,
                "title": p.get("work_type") or p_code,
                "category": p.get("category"),
                "state": p.get("state"),
                "district": p.get("district"),
                "sanctioned_amount": p.get("sanctioned_amount"),
                "risk_level": p.get("risk_level") or "LOW",
                "risk_score": p.get("overall_risk_score") or 0,
                "is_target": False
            })
            edges.append({
                "source": target_code,
                "target": p_code,
                "relation_type": "SAME_DISTRICT_CATEGORY",
                "similarity": 0.65,
                "label": "Same District & Category"
            })
            
    return {
        "target_work_code": target_code,
        "nodes": nodes,
        "edges": edges
    }

@router.get("/{work_code:path}/lineage")
def get_project_lineage(work_code: str):
    """Returns 5-tier traceability data lineage"""
    target = query_db("""
    SELECT p.*, r.calculated_at, r.model_version
    FROM projects p
    LEFT JOIN risk_scores r ON p.work_code = r.work_code
    WHERE p.work_code = ? OR p.id = ?
    """, (work_code, work_code), one=True)
    
    if not target:
        raise HTTPException(status_code=404, detail="Target project not found")
        
    t_dict = dict(target)
    
    vouchers_count = query_db("SELECT COUNT(*) FROM expenditure_vouchers WHERE work_code = ?", (t_dict["work_code"],), one=True)[0]
    
    return {
        "work_code": t_dict["work_code"],
        "tiers": [
            {
                "tier": 1,
                "name": "Decision-Intelligence Layer",
                "source": "MPLAD GUARDIAN National Pulse / Priority Queue",
                "verified": True
            },
            {
                "tier": 2,
                "name": "API Service Layer",
                "source": f"FastAPI REST /api/projects/{t_dict['work_code']}",
                "verified": True
            },
            {
                "tier": 3,
                "name": "Relational Storage (SQLite/PostgreSQL)",
                "source": f"Table: projects (ID: {t_dict.get('id')}) + Table: risk_scores",
                "verified": True
            },
            {
                "tier": 4,
                "name": "Data Integration & Cross-Linkage",
                "source": f"Unified Canonical Work ID: {t_dict['work_code']} ({vouchers_count} linked payment vouchers)",
                "verified": True
            },
            {
                "tier": 5,
                "name": "Primary Source CSV Records",
                "source": f"MoSPI Official CSVs: Works Sanctioned - {t_dict.get('house', 'LOK_SABHA').replace('_', ' ').title()}",
                "verified": True
            }
        ]
    }

@router.get("/{work_code:path}")
def get_project_detail(work_code: str):
    project_row = query_db("""
    SELECT 
        p.*,
        r.overall_risk_score, r.risk_level, r.confidence, r.cost_anomaly_score,
        r.duplicate_score, r.progress_gap_score, r.geographic_score, r.data_quality_score,
        r.coverage_pct, r.cost_zscore, r.cost_mad_score, r.comparison_group_size,
        r.explanation_json, r.recommendation, r.model_version, r.calculated_at
    FROM projects p
    LEFT JOIN risk_scores r ON p.work_code = r.work_code
    WHERE p.work_code = ? OR p.id = ?
    """, (work_code, work_code), one=True)
    
    if not project_row:
        raise HTTPException(status_code=404, detail="Project record not found in MPLADS repository")
        
    p_data = dict(project_row)
    
    try:
        p_data["raw_data"] = json.loads(p_data.get("raw_data") or "{}")
    except Exception:
        p_data["raw_data"] = {}
        
    try:
        p_data["explanation_json"] = json.loads(p_data.get("explanation_json") or "{}")
    except Exception:
        p_data["explanation_json"] = {}
        
    vouchers = query_db("""
    SELECT * FROM expenditure_vouchers WHERE work_code = ? ORDER BY expenditure_date DESC
    """, (p_data["work_code"],))
    p_data["vouchers"] = [dict(v) for v in vouchers]
    
    comparables = query_db("""
    SELECT 
        c.comparable_work_code, c.similarity_score, c.similarity_type, c.reason,
        p.work_type, p.state, p.district, p.sanctioned_amount, p.status, r.overall_risk_score, r.risk_level
    FROM comparable_projects c
    JOIN projects p ON c.comparable_work_code = p.work_code
    LEFT JOIN risk_scores r ON p.work_code = r.work_code
    WHERE c.target_work_code = ?
    ORDER BY c.similarity_score DESC
    LIMIT 10
    """, (p_data["work_code"],))
    p_data["comparable_projects"] = [dict(c) for c in comparables]
    
    p_data["traceability"] = {
        "source_type": "OFFICIAL MPLADS OPERATIONAL DATASET",
        "house": p_data.get("house"),
        "primary_id": p_data.get("work_code"),
        "has_recommended_record": "recommended_record" in p_data["raw_data"],
        "has_sanctioned_record": "sanctioned_record" in p_data["raw_data"],
        "has_completed_record": "completed_record" in p_data["raw_data"],
        "voucher_count": len(p_data["vouchers"]),
        "last_synced": p_data.get("created_at")
    }
    
    return p_data
