from fastapi import APIRouter, Query, Depends, HTTPException
from backend.app.database import query_db
from backend.app.auth import require_role
import math

router = APIRouter(prefix="/api/v1/audit-logs", tags=["System Audit Trail & Governance Logs"])

@router.get("")
def list_audit_logs(
    action: str = Query("", description="Filter by action type"),
    username: str = Query("", description="Filter by username"),
    target_type: str = Query("", description="Filter by target type e.g. ALERT, PROJECT, SYSTEM"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=5, le=200),
    current_user: dict = Depends(require_role(["ADMIN"]))
):
    offset = (page - 1) * limit
    where_clauses = ["1=1"]
    params = []
    
    if action.strip():
        where_clauses.append("action LIKE ?")
        params.append(f"%{action.strip()}%")
        
    if username.strip():
        where_clauses.append("username = ?")
        params.append(username.strip())
        
    if target_type.strip():
        where_clauses.append("target_type = ?")
        params.append(target_type.strip().upper())
        
    where_sql = " AND ".join(where_clauses)
    
    total_count = query_db(f"SELECT COUNT(*) FROM audit_logs WHERE {where_sql}", params, one=True)[0]
    
    logs = query_db(f"""
    SELECT id, user_id, username, user_role, action, target_type, target_id, previous_state, new_state, notes, created_at
    FROM audit_logs 
    WHERE {where_sql} 
    ORDER BY created_at DESC 
    LIMIT ? OFFSET ?
    """, params + [limit, offset])
    
    total_pages = math.ceil(total_count / limit) if total_count > 0 else 1
    
    return {
        "logs": [dict(l) for l in logs],
        "pagination": {
            "page": page,
            "limit": limit,
            "total_records": total_count,
            "total_pages": total_pages
        },
        "viewer_info": {
            "requested_by": current_user["username"],
            "role": current_user["role"]
        }
    }
