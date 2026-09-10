import sqlite3
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException
from backend.app.database import query_db
from backend.app.cache import timed_cache

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics & Map"])

STATE_CODE_MAP = {
  'Uttar Pradesh': 'UP', 'Gujarat': 'GJ', 'Madhya Pradesh': 'MP', 'Bihar': 'BR',
  'Tamil Nadu': 'TN', 'West Bengal': 'WB', 'Odisha': 'OD', 'Jharkhand': 'JH',
  'Punjab': 'PB', 'Telangana': 'TS', 'Kerala': 'KL', 'Karnataka': 'KA',
  'Andhra Pradesh': 'AP', 'Rajasthan': 'RJ', 'Maharashtra': 'MH', 'Assam': 'AS',
  'Haryana': 'HR', 'Chhattisgarh': 'CG', 'Himachal Pradesh': 'HP', 'Uttarakhand': 'UK',
  'Jammu And Kashmir': 'JK', 'Delhi': 'DL', 'Goa': 'GA', 'Tripura': 'TR',
  'Meghalaya': 'ML', 'Manipur': 'MN', 'Nagaland': 'NL', 'Arunachal Pradesh': 'AR',
  'Mizoram': 'MZ', 'Sikkim': 'SK', 'Puducherry': 'PY', 'Chandigarh': 'CH',
  'Ladakh': 'LA', 'Andaman And Nicobar Islands': 'AN',
  'Dadra And Nagar Haveli And Daman And Diu': 'DN', 'Lakshadweep': 'LD'
}

STATE_ALIASES = {
    'Andaman & Nicobar Islands': 'Andaman And Nicobar Islands',
    'Andaman & Nicobar': 'Andaman And Nicobar Islands',
    'Andaman and Nicobar': 'Andaman And Nicobar Islands',
    'Dadra and Nagar Haveli and Daman and Diu': 'The Dadra And Nagar Haveli And Daman And Diu',
    'Dadra & Nagar Haveli & Daman & Diu': 'The Dadra And Nagar Haveli And Daman And Diu',
    'Dadra And Nagar Haveli And Daman And Diu': 'The Dadra And Nagar Haveli And Daman And Diu',
    'Orissa': 'Odisha',
    'Pondicherry': 'Puducherry',
    'Uttaranchal': 'Uttarakhand'
}

@router.get("/map")
@timed_cache(ttl_seconds=300.0)
def get_analytics_map_data(
    year: Optional[str] = Query(None, description="Financial year filter e.g. 2025-2026"),
    state: Optional[str] = Query(None, description="Filter by state name"),
    district: Optional[str] = Query(None, description="Filter by district"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by project status"),
    riskLevel: Optional[str] = Query(None, description="Filter by risk level: CRITICAL, HIGH, MEDIUM, LOW")
):
    has_filter = any([
        year and isinstance(year, str),
        state and isinstance(state, str),
        district and isinstance(district, str),
        category and isinstance(category, str),
        status and isinstance(status, str),
        riskLevel and isinstance(riskLevel, str)
    ])

    if not has_filter:
        # Ultra-fast covering index path for default national overview (~30ms)
        proj_rows = query_db("""
        SELECT 
            state,
            COUNT(*) as project_count,
            SUM(sanctioned_amount) as sanctioned_amount,
            SUM(expenditure_amount) as utilized_amount,
            SUM(CASE WHEN status = 'Work Completed' THEN 1 ELSE 0 END) as completed_works
        FROM projects
        WHERE state != ''
        GROUP BY state
        ORDER BY project_count DESC
        """)

        risk_rows = query_db("""
        SELECT 
            p.state,
            SUM(CASE WHEN r.risk_level = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count,
            SUM(CASE WHEN r.risk_level = 'HIGH' THEN 1 ELSE 0 END) as high_count,
            SUM(CASE WHEN r.risk_level = 'MEDIUM' THEN 1 ELSE 0 END) as medium_count,
            SUM(CASE WHEN r.risk_level = 'LOW' THEN 1 ELSE 0 END) as low_count,
            AVG(r.overall_risk_score) as avg_risk_score
        FROM risk_scores r
        JOIN projects p ON r.work_code = p.work_code
        WHERE p.state != ''
        GROUP BY p.state
        """)

        risk_dict = {r["state"]: dict(r) for r in risk_rows}

        states_data = []
        tot_proj = 0
        tot_sanc = 0.0
        tot_util = 0.0
        tot_comp = 0
        tot_sig = 0

        for r in proj_rows:
            d = dict(r)
            st_name = d["state"]
            cnt = d["project_count"] or 1
            sanc = float(d["sanctioned_amount"] or 0.0)
            util = float(d["utilized_amount"] or 0.0)
            comp = d["completed_works"] or 0

            rk = risk_dict.get(st_name, {})
            crit = rk.get("critical_count") or 0
            high = rk.get("high_count") or 0
            med = rk.get("medium_count") or 0
            low = rk.get("low_count") or 0
            signals = crit + high

            comp_rate = round((comp / cnt) * 100, 1)
            util_rate = round((util / sanc) * 100, 1) if sanc > 0 else 0.0
            signal_density = round((signals / cnt) * 100, 2)

            tot_proj += d["project_count"]
            tot_sanc += sanc
            tot_util += util
            tot_comp += comp
            tot_sig += signals

            norm_st = st_name
            if norm_st == 'The Dadra And Nagar Haveli And Daman And Diu':
                norm_st = 'Dadra And Nagar Haveli And Daman And Diu'

            states_data.append({
                "state": norm_st,
                "rawState": st_name,
                "code": STATE_CODE_MAP.get(norm_st, STATE_CODE_MAP.get(st_name, st_name[:2].upper())),
                "projectCount": d["project_count"],
                "sanctionedAmount": sanc,
                "utilizedAmount": util,
                "completionRate": comp_rate,
                "utilizationRate": util_rate,
                "riskSignals": signals,
                "signalDensity": signal_density,
                "criticalCount": crit,
                "highCount": high,
                "mediumCount": med,
                "lowCount": low,
                "avgRiskScore": round(rk.get("avg_risk_score") or 0, 1),
                "completedWorks": comp
            })

        nat_comp_rate = round((tot_comp / tot_proj) * 100, 1) if tot_proj > 0 else 0.0
        nat_util_rate = round((tot_util / tot_sanc) * 100, 1) if tot_sanc > 0 else 0.0
        nat_signal_density = round((tot_sig / tot_proj) * 100, 2) if tot_proj > 0 else 0.0

        return {
            "states": states_data,
            "national": {
                "totalProjects": tot_proj,
                "totalStates": len(states_data),
                "sanctionedAmount": tot_sanc,
                "utilizedAmount": tot_util,
                "completionRate": nat_comp_rate,
                "utilizationRate": nat_util_rate,
                "riskSignals": tot_sig,
                "signalDensity": nat_signal_density
            },
            "disclaimer": "Aggregated State & District geographic representation — not exact GPS coordinates."
        }

    # Filtered query path
    where_clauses = ["p.state != ''"]
    params = []

    if year and isinstance(year, str):
        where_clauses.append("p.financial_year = ?")
        params.append(year)
    if state and isinstance(state, str):
        canon_state = STATE_ALIASES.get(state, state)
        where_clauses.append("(p.state = ? OR p.state = ?)")
        params.extend([state, canon_state])
    if district and isinstance(district, str):
        where_clauses.append("p.district = ?")
        params.append(district)
    if category and isinstance(category, str):
        where_clauses.append("p.category = ?")
        params.append(category)
    if status and isinstance(status, str):
        where_clauses.append("p.status = ?")
        params.append(status)
    if riskLevel and isinstance(riskLevel, str):
        where_clauses.append("r.risk_level = ?")
        params.append(riskLevel.upper())

    where_sql = " AND ".join(where_clauses)

    query = f"""
    SELECT 
        p.state,
        COUNT(*) as project_count,
        SUM(p.sanctioned_amount) as sanctioned_amount,
        SUM(p.expenditure_amount) as utilized_amount,
        SUM(CASE WHEN r.risk_level = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count,
        SUM(CASE WHEN r.risk_level = 'HIGH' THEN 1 ELSE 0 END) as high_count,
        SUM(CASE WHEN r.risk_level = 'MEDIUM' THEN 1 ELSE 0 END) as medium_count,
        SUM(CASE WHEN r.risk_level = 'LOW' THEN 1 ELSE 0 END) as low_count,
        AVG(r.overall_risk_score) as avg_risk_score,
        SUM(CASE WHEN p.status = 'Work Completed' THEN 1 ELSE 0 END) as completed_works
    FROM projects p
    JOIN risk_scores r ON p.work_code = r.work_code
    WHERE {where_sql}
    GROUP BY p.state
    ORDER BY project_count DESC
    """

    state_rows = query_db(query, tuple(params))

    states_data = []
    tot_proj = 0
    tot_sanc = 0.0
    tot_util = 0.0
    tot_comp = 0
    tot_sig = 0

    for r in state_rows:
        d = dict(r)
        cnt = d["project_count"] or 1
        sanc = float(d["sanctioned_amount"] or 0.0)
        util = float(d["utilized_amount"] or 0.0)
        comp = d["completed_works"] or 0
        crit = d["critical_count"] or 0
        high = d["high_count"] or 0
        med = d["medium_count"] or 0
        low = d["low_count"] or 0
        signals = crit + high

        comp_rate = round((comp / cnt) * 100, 1)
        util_rate = round((util / sanc) * 100, 1) if sanc > 0 else 0.0
        signal_density = round((signals / cnt) * 100, 2)

        tot_proj += d["project_count"]
        tot_sanc += sanc
        tot_util += util
        tot_comp += comp
        tot_sig += signals

        st_name = d["state"]
        if st_name == 'The Dadra And Nagar Haveli And Daman And Diu':
            st_name = 'Dadra And Nagar Haveli And Daman And Diu'

        states_data.append({
            "state": st_name,
            "rawState": d["state"],
            "code": STATE_CODE_MAP.get(st_name, STATE_CODE_MAP.get(d["state"], d["state"][:2].upper())),
            "projectCount": d["project_count"],
            "sanctionedAmount": sanc,
            "utilizedAmount": util,
            "completionRate": comp_rate,
            "utilizationRate": util_rate,
            "riskSignals": signals,
            "signalDensity": signal_density,
            "criticalCount": crit,
            "highCount": high,
            "mediumCount": med,
            "lowCount": low,
            "avgRiskScore": round(d["avg_risk_score"] or 0, 1),
            "completedWorks": comp
        })

    nat_comp_rate = round((tot_comp / tot_proj) * 100, 1) if tot_proj > 0 else 0.0
    nat_util_rate = round((tot_util / tot_sanc) * 100, 1) if tot_sanc > 0 else 0.0
    nat_signal_density = round((tot_sig / tot_proj) * 100, 2) if tot_proj > 0 else 0.0

    return {
        "states": states_data,
        "national": {
            "totalProjects": tot_proj,
            "totalStates": len(states_data),
            "sanctionedAmount": tot_sanc,
            "utilizedAmount": tot_util,
            "completionRate": nat_comp_rate,
            "utilizationRate": nat_util_rate,
            "riskSignals": tot_sig,
            "signalDensity": nat_signal_density
        },
        "disclaimer": "Aggregated State & District geographic representation — not exact GPS coordinates."
    }

@router.get("/map/state/{state}")
@timed_cache(ttl_seconds=300.0)
def get_state_map_details(state: str):
    lookup_states = [state]
    canon = STATE_ALIASES.get(state)
    if canon and canon not in lookup_states:
        lookup_states.append(canon)
    if state == 'Dadra And Nagar Haveli And Daman And Diu':
        lookup_states.append('The Dadra And Nagar Haveli And Daman And Diu')

    placeholders = ",".join(["?"] * len(lookup_states))

    # Fast covering district queries
    dist_rows = query_db(f"""
    SELECT 
        district,
        COUNT(*) as project_count,
        SUM(sanctioned_amount) as sanctioned_amount,
        SUM(expenditure_amount) as utilized_amount,
        SUM(CASE WHEN status = 'Work Completed' THEN 1 ELSE 0 END) as completed_works
    FROM projects
    WHERE state IN ({placeholders}) AND district != ''
    GROUP BY district
    ORDER BY project_count DESC
    """, tuple(lookup_states))

    risk_dist_rows = query_db(f"""
    SELECT 
        district,
        SUM(CASE WHEN risk_level = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count,
        SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END) as high_count
    FROM risk_scores
    WHERE state IN ({placeholders}) AND district != ''
    GROUP BY district
    """, tuple(lookup_states))

    risk_map = {r["district"]: (r["critical_count"] or 0) + (r["high_count"] or 0) for r in risk_dist_rows}

    cat_rows = query_db(f"""
    SELECT 
        category,
        COUNT(*) as count,
        SUM(sanctioned_amount) as total_sanctioned
    FROM projects
    WHERE state IN ({placeholders}) AND category != ''
    GROUP BY category
    ORDER BY count DESC
    LIMIT 6
    """, tuple(lookup_states))

    districts = []
    for r in dist_rows:
        d = dict(r)
        cnt = d["project_count"] or 1
        sanc = d["sanctioned_amount"] or 0.0
        util = d["utilized_amount"] or 0.0
        comp = d["completed_works"] or 0
        signals = risk_map.get(d["district"], 0)
        signal_density = round((signals / cnt) * 100, 2)

        districts.append({
            "district": d["district"],
            "projectCount": d["project_count"],
            "sanctionedAmount": sanc,
            "utilizedAmount": util,
            "completionRate": round((comp / cnt) * 100, 1),
            "utilizationRate": round((util / sanc) * 100, 1) if sanc > 0 else 0.0,
            "riskSignals": signals,
            "signalDensity": signal_density
        })

    categories = []
    for r in cat_rows:
        categories.append({
            "category": r["category"],
            "count": r["count"],
            "sanctionedAmount": r["total_sanctioned"] or 0.0
        })

    norm_state_name = state
    if norm_state_name == 'The Dadra And Nagar Haveli And Daman And Diu':
        norm_state_name = 'Dadra And Nagar Haveli And Daman And Diu'

    return {
        "state": norm_state_name,
        "code": STATE_CODE_MAP.get(norm_state_name, STATE_CODE_MAP.get(state, state[:2].upper())),
        "districts": districts,
        "categories": categories,
        "disclaimer": "District-level aggregation — not exact project GPS location."
    }
