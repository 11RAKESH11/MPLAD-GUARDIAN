from fastapi import APIRouter, HTTPException, Query, Depends, Body
from backend.app.database import query_db, execute_db
from backend.app.auth import get_current_user
from pydantic import BaseModel
from typing import Optional
import datetime
import json
import math

router = APIRouter(prefix="/api/alerts", tags=["Alert Management Center"])

class UpdateAlertStatusRequest(BaseModel):
    status: str # OPEN, UNDER_REVIEW, EVIDENCE_REQUESTED, VALIDATED, NOT_SUBSTANTIATED, RESOLVED, CLOSED
    resolution_notes: str = ""
    assigned_to: Optional[str] = None

@router.get("")
def list_alerts(
    status: str = Query("", description="Filter by status: OPEN, UNDER_REVIEW, EVIDENCE_REQUESTED, VALIDATED, NOT_SUBSTANTIATED, RESOLVED, CLOSED"),
    severity: str = Query("", description="Filter by severity: CRITICAL, HIGH, MEDIUM, LOW"),
    alert_type: str = Query("", description="Filter by alert type: COST_ANOMALY, POSSIBLE_DUPLICATE, PROGRESS_GAP"),
    state: str = Query("", description="Filter by state"),
    district: str = Query("", description="Filter by district"),
    q: str = Query("", description="Search term across title, work_code, district, evidence"),
    sort_by: str = Query("priority", description="Sort by priority or date"),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100)
):
    offset = (page - 1) * limit
    where_clauses = ["1=1"]
    params = []
    
    if status.strip():
        where_clauses.append("a.status = ?")
        params.append(status.strip().upper())
        
    if severity.strip():
        where_clauses.append("a.severity = ?")
        params.append(severity.strip().upper())
        
    if alert_type.strip():
        where_clauses.append("a.alert_type = ?")
        params.append(alert_type.strip().upper())
        
    if state.strip():
        where_clauses.append("a.state = ?")
        params.append(state.strip())

    if district.strip():
        where_clauses.append("a.district = ?")
        params.append(district.strip())
        
    if q.strip():
        search_term = f"%{q.strip()}%"
        where_clauses.append("(a.title LIKE ? OR a.work_code LIKE ? OR a.district LIKE ? OR a.evidence LIKE ?)")
        params.extend([search_term] * 4)
        
    where_sql = " AND ".join(where_clauses)
    
    count_sql = f"SELECT COUNT(*) FROM alerts a WHERE {where_sql}"
    total_records = query_db(count_sql, params, one=True)[0]
    
    # Priority ranking sort
    if sort_by == "date":
        order_sql = "a.created_at DESC"
    else:
        order_sql = """
        COALESCE(a.priority_score, 0) DESC,
        CASE a.severity 
            WHEN 'CRITICAL' THEN 1 
            WHEN 'HIGH' THEN 2 
            WHEN 'MEDIUM' THEN 3 
            WHEN 'LOW' THEN 4 
        END,
        a.created_at DESC
        """

    records_sql = f"""
    SELECT 
        a.*,
        p.id as project_id, p.sanctioned_amount, p.expenditure_amount, p.mp_name, p.category, p.status as project_status,
        r.overall_risk_score, r.confidence, r.cost_anomaly_score, r.duplicate_score, r.progress_gap_score,
        r.explanation_json
    FROM alerts a
    LEFT JOIN projects p ON a.work_code = p.work_code
    LEFT JOIN risk_scores r ON a.work_code = r.work_code
    WHERE {where_sql}
    ORDER BY {order_sql}
    LIMIT ? OFFSET ?
    """
    rows = query_db(records_sql, params + [limit, offset])
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 1
    
    # Summary stats across all alerts
    summary = query_db("""
    SELECT 
        COUNT(*) as total_alerts,
        SUM(CASE WHEN status = 'OPEN' THEN 1 ELSE 0 END) as open_count,
        SUM(CASE WHEN status IN ('UNDER_REVIEW', 'EVIDENCE_REQUESTED') THEN 1 ELSE 0 END) as in_review_count,
        SUM(CASE WHEN status IN ('RESOLVED', 'VALIDATED', 'CLOSED') THEN 1 ELSE 0 END) as resolved_count,
        SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count,
        SUM(CASE WHEN severity = 'HIGH' THEN 1 ELSE 0 END) as high_count,
        SUM(CASE WHEN severity = 'MEDIUM' THEN 1 ELSE 0 END) as medium_count
    FROM alerts
    """, one=True)

    formatted_rows = []
    for r in rows:
        d = dict(r)
        if isinstance(d.get("explanation_json"), str):
            try:
                d["explanation_json"] = json.loads(d["explanation_json"])
            except:
                pass
        formatted_rows.append(d)

    return {
        "data": formatted_rows,
        "summary": dict(summary) if summary else {},
        "pagination": {
            "page": page,
            "limit": limit,
            "total_records": total_records,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

@router.get("/{alert_id}/evidence")
def get_alert_evidence(alert_id: str):
    """Flagship Evidence Room data payload for investigation"""
    alert = query_db("""
    SELECT 
        a.*,
        p.id as project_id, p.sanctioned_amount, p.expenditure_amount, p.disbursed_amount,
        p.recommended_amount, p.mp_name, p.category, p.work_type, p.financial_year,
        p.description as project_description, p.status as project_status, p.ida_name,
        p.constituency, p.raw_data,
        r.overall_risk_score, r.risk_level, r.confidence, r.cost_anomaly_score,
        r.duplicate_score, r.progress_gap_score, r.geographic_score, r.data_quality_score,
        r.cost_zscore, r.cost_mad_score, r.comparison_group_size, r.explanation_json,
        r.recommendation, r.model_version, r.calculated_at
    FROM alerts a
    LEFT JOIN projects p ON a.work_code = p.work_code
    LEFT JOIN risk_scores r ON a.work_code = r.work_code
    WHERE a.id = ? OR a.work_code = ?
    """, (alert_id, alert_id), one=True)
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert record not found")
        
    a_dict = dict(alert)
    
    try:
        a_dict["raw_data"] = json.loads(a_dict.get("raw_data") or "{}")
    except:
        a_dict["raw_data"] = {}
        
    try:
        a_dict["explanation_json"] = json.loads(a_dict.get("explanation_json") or "{}")
    except:
        a_dict["explanation_json"] = {}
        
    # Fetch Comparables
    comparables = query_db("""
    SELECT 
        c.comparable_work_code, c.similarity_score, c.similarity_type, c.reason,
        p.work_type, p.state, p.district, p.sanctioned_amount, p.status, r.overall_risk_score, r.risk_level
    FROM comparable_projects c
    JOIN projects p ON c.comparable_work_code = p.work_code
    LEFT JOIN risk_scores r ON p.work_code = r.work_code
    WHERE c.target_work_code = ?
    ORDER BY c.similarity_score DESC
    LIMIT 6
    """, (a_dict["work_code"],))
    
    # Fetch Vouchers
    vouchers = query_db("""
    SELECT * FROM expenditure_vouchers WHERE work_code = ? ORDER BY expenditure_date DESC LIMIT 10
    """, (a_dict["work_code"],))
    
    # Fetch Audit History for this signal
    audit_history = query_db("""
    SELECT * FROM audit_logs WHERE target_id = ? OR target_id = ? ORDER BY created_at DESC LIMIT 10
    """, (alert_id, a_dict["work_code"]))
    
    # Peer Distribution Calculation
    category = a_dict.get("category") or ""
    state = a_dict.get("state") or ""
    
    peer_stats = query_db("""
    SELECT 
        COUNT(*) as peer_count,
        AVG(sanctioned_amount) as peer_avg,
        MIN(sanctioned_amount) as peer_min,
        MAX(sanctioned_amount) as peer_max
    FROM projects
    WHERE category = ? AND state = ? AND sanctioned_amount > 0
    """, (category, state), one=True)
    
    p_stat = dict(peer_stats) if peer_stats else {}
    
    # Recommended Review Checklist
    checklist = [
        {"id": "c1", "step": "Review Administrative Approval & Technical Sanction documents for scope changes", "done": False},
        {"id": "c2", "step": f"Verify estimate alignment with State PWD Schedule of Rates (SOR) in {state}", "done": False},
        {"id": "c3", "step": "Cross-reference contractor voucher lineage against physically completed measurements", "done": False},
        {"id": "c4", "step": "Confirm non-duplication with State/Panchayat funded schemes at identical GPS site", "done": False}
    ]

    return {
        "alert": a_dict,
        "comparables": [dict(c) for c in comparables],
        "vouchers": [dict(v) for v in vouchers],
        "audit_history": [dict(au) for au in audit_history],
        "peer_benchmark": {
            "peer_count": p_stat.get("peer_count", 0),
            "peer_avg_cost": p_stat.get("peer_avg", 0),
            "peer_min_cost": p_stat.get("peer_min", 0),
            "peer_max_cost": p_stat.get("peer_max", 0),
            "current_cost": a_dict.get("sanctioned_amount", 0),
            "z_score": a_dict.get("cost_zscore", 0),
            "mad_score": a_dict.get("cost_mad_score", 0)
        },
        "recommended_checklist": checklist,
        "lineage": {
            "tier_1_dashboard": "National Risk Command Center / Pulse",
            "tier_2_api": f"/api/alerts/{alert_id}",
            "tier_3_db_table": "alerts JOIN projects JOIN risk_scores",
            "tier_4_normalized_id": a_dict.get("work_code"),
            "tier_5_source_file": "Works Sanctioned / Recommended official CSVs"
        },
        "disclaimer": "This analytical signal identifies a statistical or documentation pattern that warrants human oversight review. It does not establish legal culpability or assert fraud."
    }

@router.get("/{alert_id}")
def get_alert_detail(alert_id: str):
    alert = query_db("""
    SELECT 
        a.*,
        p.id as project_id, p.sanctioned_amount, p.expenditure_amount, p.mp_name, p.category,
        p.description as project_description, p.status as project_status,
        r.overall_risk_score, r.confidence, r.explanation_json
    FROM alerts a
    LEFT JOIN projects p ON a.work_code = p.work_code
    LEFT JOIN risk_scores r ON a.work_code = r.work_code
    WHERE a.id = ?
    """, (alert_id,), one=True)
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert record not found")
        
    return dict(alert)

@router.post("/{alert_id}/status")
def update_alert_status(
    alert_id: str,
    req: UpdateAlertStatusRequest,
    current_user: dict = Depends(get_current_user)
):
    alert = query_db("SELECT * FROM alerts WHERE id = ?", (alert_id,), one=True)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert record not found")
        
    old_status = alert["status"]
    new_status = req.status.upper()
    valid_statuses = ["OPEN", "UNDER_REVIEW", "EVIDENCE_REQUESTED", "VALIDATED", "NOT_SUBSTANTIATED", "RESOLVED", "CLOSED", "ACKNOWLEDGED"]
    
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status value. Must be one of {valid_statuses}")
        
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_name = current_user.get("full_name") or current_user.get("username", "Analyst")
    user_id = current_user.get("id", "usr-analyst")
    user_role = current_user.get("role", "ANALYST")
    assigned = req.assigned_to or user_name
    
    execute_db("""
    UPDATE alerts 
    SET status = ?, 
        assigned_to = ?,
        resolution_notes = COALESCE(?, resolution_notes),
        acknowledged_by = CASE WHEN ? IN ('UNDER_REVIEW', 'ACKNOWLEDGED') AND acknowledged_by IS NULL THEN ? ELSE acknowledged_by END,
        acknowledged_at = CASE WHEN ? IN ('UNDER_REVIEW', 'ACKNOWLEDGED') AND acknowledged_at IS NULL THEN ? ELSE acknowledged_at END,
        resolved_by = CASE WHEN ? IN ('RESOLVED', 'CLOSED', 'VALIDATED', 'NOT_SUBSTANTIATED') THEN ? ELSE resolved_by END,
        resolved_at = CASE WHEN ? IN ('RESOLVED', 'CLOSED', 'VALIDATED', 'NOT_SUBSTANTIATED') THEN ? ELSE resolved_at END
    WHERE id = ?
    """, (
        new_status, assigned, req.resolution_notes,
        new_status, user_name, new_status, now_str,
        new_status, user_name, new_status, now_str,
        alert_id
    ))
    
    # Record in audit log
    execute_db("""
    INSERT INTO audit_logs (user_id, username, user_role, action, target_type, target_id, previous_state, new_state, notes, created_at)
    VALUES (?, ?, ?, 'ALERT_STATUS_UPDATE', 'ALERT', ?, ?, ?, ?, ?)
    """, (
        user_id, user_name, user_role,
        alert_id, old_status, new_status,
        req.resolution_notes or f"Updated status from {old_status} to {new_status}",
        now_str
    ))
    
    return {
        "success": True,
        "alert_id": alert_id,
        "previous_status": old_status,
        "new_status": new_status,
        "updated_by": user_name,
        "updated_at": now_str
    }
