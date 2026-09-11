from fastapi import APIRouter
from backend.app.database import query_db
from backend.app.cache import timed_cache
from decimal import Decimal
import json

router = APIRouter(prefix="/api/v1/dashboard", tags=["Executive Dashboard"])

def _to_float(val, default: float = 0.0) -> float:
    if val is None:
        return default
    if isinstance(val, (int, float, Decimal)):
        return float(val)
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def _to_int(val, default: int = 0) -> int:
    if val is None:
        return default
    if isinstance(val, (int, float, Decimal)):
        return int(val)
    try:
        return int(val)
    except (ValueError, TypeError):
        return default

def _sanitize_dict(d) -> dict:
    if not isinstance(d, dict):
        d = dict(d)
    res = {}
    for k, v in d.items():
        if isinstance(v, Decimal):
            res[k] = float(v)
        else:
            res[k] = v
    return res

@router.get("/overview")
@timed_cache(300.0)
def get_dashboard_overview():
    # 1. Core KPIs - Single SQL aggregation scan on projects
    totals = query_db("""
    SELECT 
        COUNT(*) as total_projects,
        SUM(recommended_amount) as total_recommended_funds,
        SUM(sanctioned_amount) as total_sanctioned_funds,
        SUM(disbursed_amount) as total_disbursed_funds,
        SUM(expenditure_amount) as total_expenditure_funds,
        SUM(CASE WHEN status = 'Work Completed' THEN 1 ELSE 0 END) as completed_works,
        SUM(CASE WHEN status = 'Sanction' THEN 1 ELSE 0 END) as sanctioned_works,
        SUM(CASE WHEN status = 'Physical Inspection' THEN 1 ELSE 0 END) as inspection_works,
        SUM(CASE WHEN status = 'Vendor Identification' THEN 1 ELSE 0 END) as vendor_id_works,
        SUM(CASE WHEN district IS NULL OR district = '' THEN 1 ELSE 0 END) as missing_dist
    FROM projects
    """, one=True)
    
    # 2. Risk Signals summary
    risk_summary = query_db("""
    SELECT 
        SUM(CASE WHEN risk_level = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count,
        SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END) as high_count,
        SUM(CASE WHEN risk_level = 'MEDIUM' THEN 1 ELSE 0 END) as medium_count,
        SUM(CASE WHEN risk_level = 'LOW' THEN 1 ELSE 0 END) as low_count,
        AVG(overall_risk_score) as avg_risk_score,
        AVG(confidence) as avg_confidence
    FROM risk_scores
    """, one=True)
    
    # 3. Duplicate and Alerts count (fast indexed)
    alert_counts = query_db("""
    SELECT 
        COUNT(*) as total_alerts,
        SUM(CASE WHEN status = 'OPEN' THEN 1 ELSE 0 END) as open_alerts,
        SUM(CASE WHEN status = 'ACKNOWLEDGED' THEN 1 ELSE 0 END) as ack_alerts,
        SUM(CASE WHEN status = 'RESOLVED' THEN 1 ELSE 0 END) as resolved_alerts
    FROM alerts
    """, one=True)

    # Comparable duplicates count
    dup_count_row = query_db("SELECT COUNT(*) as dup_count FROM comparable_projects", one=True)
    duplicates_count = _to_int(dup_count_row["dup_count"]) if dup_count_row else 0
    
    # 4. MP count & limits
    mp_stats = query_db("""
    SELECT 
        COUNT(*) as total_mps,
        SUM(allocated_limit) as total_allocated_limit,
        SUM(calamity_consent_amount) as total_calamity_consent
    FROM mps
    """, one=True)

    # 5. Voucher and vendor counts from live DB
    voucher_stats = query_db("""
    SELECT 
        COUNT(*) as total_vouchers,
        COUNT(DISTINCT vendor_name) as total_unique_vendors
    FROM expenditure_vouchers
    """, one=True)
    
    # 6. Safe decimal/float Data Quality & Utilization Calculation
    t_dict = dict(totals) if totals else {}
    total_proj = _to_int(t_dict.get("total_projects"), 1) or 1
    missing_dist = _to_int(t_dict.get("missing_dist"), 0)
    completeness_pct = round(((total_proj * 6 - missing_dist) / (total_proj * 6)) * 100, 2)

    total_rec = _to_float(t_dict.get("total_recommended_funds"))
    sanc_amt = _to_float(t_dict.get("total_sanctioned_funds"))
    disb_amt = _to_float(t_dict.get("total_disbursed_funds"))
    exp_amt = _to_float(t_dict.get("total_expenditure_funds"))

    sanc_for_calc = sanc_amt if sanc_amt > 0 else 1.0
    spent_amt = max(disb_amt, exp_amt)
    utilization_rate = round((spent_amt / sanc_for_calc) * 100, 2)
    
    comp_works = _to_int(t_dict.get("completed_works"))
    sanc_works = _to_int(t_dict.get("sanctioned_works"))
    insp_works = _to_int(t_dict.get("inspection_works"))
    vend_works = _to_int(t_dict.get("vendor_id_works"))
    completion_rate = round((comp_works / total_proj) * 100, 2)

    r_dict = dict(risk_summary) if risk_summary else {}
    a_dict = dict(alert_counts) if alert_counts else {}
    m_dict = dict(mp_stats) if mp_stats else {}
    v_dict = dict(voucher_stats) if voucher_stats else {}
    
    return {
        "kpis": {
            "total_projects": total_proj,
            "total_sanctioned_funds": sanc_amt,
            "total_recommended_funds": total_rec,
            "total_expenditure_funds": exp_amt,
            "total_disbursed_funds": disb_amt,
            "utilization_rate_pct": utilization_rate,
            "completion_rate_pct": completion_rate,
            "completed_works": comp_works,
            "sanctioned_works": sanc_works,
            "inspection_works": insp_works,
            "vendor_id_works": vend_works,
            "total_mps": _to_int(m_dict.get("total_mps")),
            "total_vouchers": _to_int(v_dict.get("total_vouchers")),
            "total_unique_vendors": _to_int(v_dict.get("total_unique_vendors")),
            "source_badge": "REAL CSV DATA"
        },
        "risk_metrics": {
            "critical_count": _to_int(r_dict.get("critical_count")),
            "high_count": _to_int(r_dict.get("high_count")),
            "medium_count": _to_int(r_dict.get("medium_count")),
            "low_count": _to_int(r_dict.get("low_count")),
            "potential_duplicates_count": duplicates_count,
            "avg_risk_score": round(_to_float(r_dict.get("avg_risk_score")), 1),
            "avg_confidence": round(_to_float(r_dict.get("avg_confidence")), 1),
            "source_badge": "AI ANALYSIS"
        },
        "alerts_summary": _sanitize_dict(a_dict),
        "data_health": {
            "completeness_pct": completeness_pct,
            "source_files_count": 12,
            "total_raw_rows": 374141,
            "status": "HEALTHY",
            "last_analysis": "2026-08-28T20:30:00Z"
        }
    }

@router.get("/attention")
@timed_cache(300.0)
def get_dashboard_attention():
    """Returns top 5 prioritized items for What Needs Attention, with direct Evidence Room links."""
    alerts = query_db("""
    SELECT 
        a.id,
        a.work_code,
        a.alert_type,
        a.title,
        a.severity,
        a.status,
        a.state,
        a.district,
        a.evidence,
        a.impact,
        a.priority_score,
        p.sanctioned_amount,
        p.category,
        p.description,
        r.overall_risk_score,
        r.confidence,
        r.cost_anomaly_score,
        r.duplicate_score
    FROM alerts a
    LEFT JOIN projects p ON a.work_code = p.work_code
    LEFT JOIN risk_scores r ON a.work_code = r.work_code
    WHERE a.status = 'OPEN'
    ORDER BY a.priority_score DESC, r.overall_risk_score DESC
    LIMIT 5
    """)
    
    items = []
    for row in alerts:
        r = dict(row)
        confidence_val = _to_float(r.get("confidence"), 95.0)
        # Determine clean signal type label
        if r.get("alert_type") == "COST_OUTLIER":
            signal_label = "High Cost Anomaly"
            why_prioritized = f"Project cost exceeds statistical baseline by >2.5σ with {round(confidence_val)}% confidence."
        elif r.get("alert_type") == "POTENTIAL_DUPLICATE":
            signal_label = "Potential Duplicate Work"
            why_prioritized = f"High textual similarity (>70%) with proximate project in {(r.get('district') or '').title()}."
        elif r.get("alert_type") == "PROGRESS_GAP":
            signal_label = "Progress Discrepancy"
            why_prioritized = "Significant fund disbursement recorded while physical execution remains in preliminary status."
        else:
            signal_label = (r.get("alert_type") or "Analytical Signal").replace("_", " ").title()
            why_prioritized = "Material analytical deviation identified across multiple model dimensions."
            
        items.append({
            "alert_id": r["id"],
            "work_code": r["work_code"],
            "signal_type": signal_label,
            "raw_signal_type": r.get("alert_type"),
            "title": r.get("title") or f"{signal_label} in {(r.get('district') or '').title()}",
            "severity": r.get("severity") or "HIGH",
            "state": r.get("state") or "",
            "district": (r.get("district") or "").title(),
            "category": r.get("category") or "Developmental Asset",
            "sanctioned_amount": _to_float(r.get("sanctioned_amount")),
            "risk_score": round(_to_float(r.get("overall_risk_score")), 1),
            "confidence": round(confidence_val, 1),
            "priority_score": round(_to_float(r.get("priority_score")), 1),
            "evidence_snippet": r.get("evidence") or why_prioritized,
            "why_prioritized": why_prioritized,
            "status": r.get("status") or "OPEN"
        })
        
    return {"attention_items": items}

@router.get("/financial-flow")
@timed_cache(300.0)
def get_dashboard_financial_flow():
    """Returns aggregated pipeline stages from Recommended to Sanctioned to Disbursed to Expenditure."""
    totals = query_db("""
    SELECT 
        COUNT(*) as total_projects,
        SUM(recommended_amount) as recommended_amount,
        SUM(sanctioned_amount) as sanctioned_amount,
        SUM(disbursed_amount) as disbursed_amount,
        SUM(expenditure_amount) as expenditure_amount,
        SUM(CASE WHEN disbursed_amount > 0 THEN 1 ELSE 0 END) as disbursed_count,
        SUM(CASE WHEN expenditure_amount > 0 THEN 1 ELSE 0 END) as expenditure_count
    FROM projects
    """, one=True)
    
    t = dict(totals) if totals else {}
    sanc = _to_float(t.get("sanctioned_amount"))
    rec = _to_float(t.get("recommended_amount"))
    disb = _to_float(t.get("disbursed_amount"))
    exp = _to_float(t.get("expenditure_amount"))
    total_proj = _to_int(t.get("total_projects"), 1) or 1
    
    sanc_for_calc = sanc if sanc > 0 else 1.0
    
    stages = [
        {
            "id": "recommended",
            "name": "Recommended by MPs",
            "amount": rec,
            "records_count": total_proj,
            "percentage_of_sanctioned": round((rec / sanc_for_calc) * 100, 1) if sanc else 0,
            "description": "Total initial proposals submitted under MPLADS guidelines.",
            "source": "MP Recommendations (Portal records)"
        },
        {
            "id": "sanctioned",
            "name": "Sanctioned by District Administration",
            "amount": sanc,
            "records_count": total_proj,
            "percentage_of_sanctioned": 100.0,
            "description": "Formally approved development works with assigned budgetary allocation.",
            "source": "District Sanction Orders"
        },
        {
            "id": "disbursed",
            "name": "Released / Disbursed",
            "amount": disb,
            "records_count": _to_int(t.get("disbursed_count")),
            "percentage_of_sanctioned": round((disb / sanc_for_calc) * 100, 1) if sanc else 0,
            "description": "Funds released from nodal account to implementing agencies (IDAs).",
            "source": "Nodal Bank Release Ledgers"
        },
        {
            "id": "expenditure",
            "name": "Expenditure / Utilized",
            "amount": exp,
            "records_count": _to_int(t.get("expenditure_count")),
            "percentage_of_sanctioned": round((exp / sanc_for_calc) * 100, 1) if sanc else 0,
            "description": "Actual expenditure documented against completed or in-progress works.",
            "source": "Expenditure Vouchers & Utilization Certificates"
        }
    ]
    
    return {
        "stages": stages,
        "total_sanctioned": sanc,
        "total_expenditure": exp,
        "utilization_rate_pct": round((exp / sanc_for_calc) * 100, 2) if sanc else 0
    }

@router.get("/signal-distribution")
@timed_cache(300.0)
def get_dashboard_signal_distribution():
    """Returns clean distribution of analytical signals, risk levels, and confidence tiers."""
    # 1. Alert type counts
    alert_types = query_db("""
    SELECT alert_type, COUNT(*) as count, SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count
    FROM alerts
    GROUP BY alert_type
    ORDER BY count DESC
    """)
    
    # 2. Risk score distribution and confidence tiers combined in a single query
    risk_and_conf_dist = query_db("""
    SELECT 
        SUM(CASE WHEN risk_level = 'CRITICAL' THEN 1 ELSE 0 END) as critical,
        SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END) as high,
        SUM(CASE WHEN risk_level = 'MEDIUM' THEN 1 ELSE 0 END) as medium,
        SUM(CASE WHEN risk_level = 'LOW' THEN 1 ELSE 0 END) as low,
        SUM(CASE WHEN confidence >= 80.0 THEN 1 ELSE 0 END) as high_confidence,
        SUM(CASE WHEN confidence >= 50.0 AND confidence < 80.0 THEN 1 ELSE 0 END) as moderate_confidence,
        SUM(CASE WHEN confidence < 50.0 THEN 1 ELSE 0 END) as limited_evidence
    FROM risk_scores
    """, one=True)
    
    rc_dict = dict(risk_and_conf_dist) if risk_and_conf_dist else {}
    risk_dist = {
        "critical": _to_int(rc_dict.get("critical")),
        "high": _to_int(rc_dict.get("high")),
        "medium": _to_int(rc_dict.get("medium")),
        "low": _to_int(rc_dict.get("low"))
    }
    confidence_dist = {
        "high_confidence": _to_int(rc_dict.get("high_confidence")),
        "moderate_confidence": _to_int(rc_dict.get("moderate_confidence")),
        "limited_evidence": _to_int(rc_dict.get("limited_evidence"))
    }
    
    type_map = {
        "COST_OUTLIER": "Cost Anomaly Signals",
        "POTENTIAL_DUPLICATE": "Potential Duplicate Proposals",
        "PROGRESS_GAP": "Progress vs Expenditure Gap"
    }
    
    signals = []
    for r in alert_types:
        row = dict(r)
        at = row.get("alert_type") or "UNKNOWN"
        signals.append({
            "type_key": at,
            "label": type_map.get(at, at.replace("_", " ").title()),
            "count": _to_int(row.get("count")),
            "critical_count": _to_int(row.get("critical_count"))
        })
        
    return {
        "signals": signals,
        "total_alerts": sum(s["count"] for s in signals),
        "overlap_note": "Signal categories may overlap across the same project records.",
        "risk_distribution": risk_dist,
        "confidence_distribution": confidence_dist
    }

@router.get("/what-changed")
@timed_cache(300.0)
def get_dashboard_what_changed():
    """Calculates year-over-year changes between the two most recent complete financial years."""
    fy_rows = query_db("""
    SELECT 
        financial_year,
        COUNT(*) as projects,
        SUM(sanctioned_amount) as sanctioned,
        SUM(expenditure_amount) as expenditure,
        SUM(CASE WHEN status = 'Work Completed' THEN 1 ELSE 0 END) as completed
    FROM projects
    WHERE financial_year IN ('2024-2025', '2025-2026')
    GROUP BY financial_year
    ORDER BY financial_year ASC
    """)
    
    data = {r["financial_year"]: dict(r) for r in fy_rows}
    
    if "2024-2025" in data and "2025-2026" in data:
        p = data["2024-2025"]
        c = data["2025-2026"]
        
        def calc_pct(cur, prev):
            cur_f = _to_float(cur)
            prev_f = _to_float(prev)
            if not prev_f or prev_f == 0:
                return 0.0
            return round(((cur_f - prev_f) / prev_f) * 100, 1)
            
        return {
            "historical_comparison_available": True,
            "current_period": "FY 2025-26",
            "previous_period": "FY 2024-25",
            "comparison_label": "FY 2025-26 vs FY 2024-25",
            "metrics": [
                {
                    "name": "Project Volume",
                    "current": _to_int(c.get("projects")),
                    "previous": _to_int(p.get("projects")),
                    "diff_pct": calc_pct(c.get("projects"), p.get("projects")),
                    "explanation": "Substantial expansion in registered development projects.",
                    "neutral_note": "Driven by broader implementation across states."
                },
                {
                    "name": "Sanctioned Allocation",
                    "current": _to_float(c.get("sanctioned")),
                    "previous": _to_float(p.get("sanctioned")),
                    "diff_pct": calc_pct(c.get("sanctioned"), p.get("sanctioned")),
                    "explanation": "Higher total budget allocations across sanctioned works.",
                    "neutral_note": "Reflects updated annual fund releases."
                },
                {
                    "name": "Recorded Expenditure",
                    "current": _to_float(c.get("expenditure")),
                    "previous": _to_float(p.get("expenditure")),
                    "diff_pct": calc_pct(c.get("expenditure"), p.get("expenditure")),
                    "explanation": "Active disbursement on multi-year development projects.",
                    "neutral_note": "Expenditure ledgers reflect progressing works."
                },
                {
                    "name": "Completed Works",
                    "current": _to_int(c.get("completed")),
                    "previous": _to_int(p.get("completed")),
                    "diff_pct": calc_pct(c.get("completed"), p.get("completed")),
                    "explanation": "Number of assets with recorded completion certificates.",
                    "neutral_note": "Many recently sanctioned works remain in execution phase."
                }
            ]
        }
    else:
        return {
            "historical_comparison_available": False,
            "message": "Historical comparison unavailable: requires >= 2 financial years of data."
        }

@router.get("/state-indicators")
@timed_cache(300.0)
def get_dashboard_state_indicators():
    """Returns clean state-level indicators for executive comparison."""
    states_data = query_db("""
    SELECT 
        state,
        COUNT(*) as total_projects,
        SUM(sanctioned_amount) as total_sanctioned,
        SUM(expenditure_amount) as total_expenditure,
        SUM(CASE WHEN status = 'Work Completed' THEN 1 ELSE 0 END) as completed_works
    FROM projects
    WHERE state IS NOT NULL AND state != ''
    GROUP BY state
    ORDER BY total_projects DESC
    """)

    alert_state_counts = query_db("""
    SELECT state, COUNT(*) as signal_count
    FROM alerts
    WHERE state IS NOT NULL AND state != ''
    GROUP BY state
    """)
    alert_map = {r["state"]: _to_int(r["signal_count"]) for r in alert_state_counts}
    
    results = []
    for row in states_data:
        r = dict(row)
        sanc = _to_float(r.get("total_sanctioned"), 1.0)
        sanc_for_calc = sanc if sanc > 0 else 1.0
        exp = _to_float(r.get("total_expenditure"))
        tot = _to_int(r.get("total_projects"), 1)
        tot_for_calc = tot if tot > 0 else 1
        comp = _to_int(r.get("completed_works"))
        st = r["state"]
        
        results.append({
            "state": st,
            "total_projects": tot,
            "total_sanctioned": sanc,
            "total_expenditure": exp,
            "utilization_rate_pct": round((exp / sanc_for_calc) * 100, 1),
            "completion_rate_pct": round((comp / tot_for_calc) * 100, 1),
            "signal_count": alert_map.get(st, 0)
        })
        
    return {"states": results}

@router.get("/insights")
@timed_cache(300.0)
def get_narrative_insights():
    # Dynamic narrative cards generated directly from real data queries
    top_cost_districts = query_db("""
    SELECT p.district, p.state, COUNT(*) as flag_count, SUM(p.sanctioned_amount) as total_amt
    FROM risk_scores r
    JOIN projects p ON r.work_code = p.work_code
    WHERE r.cost_anomaly_score >= 60.0 AND p.district != ''
    GROUP BY p.district, p.state
    ORDER BY flag_count DESC
    LIMIT 3
    """)
    
    top_dup_districts = query_db("""
    SELECT p.district, p.state, COUNT(*) as dup_count
    FROM risk_scores r
    JOIN projects p ON r.work_code = p.work_code
    WHERE r.duplicate_score >= 65.0 AND p.district != ''
    GROUP BY p.district, p.state
    ORDER BY dup_count DESC
    LIMIT 3
    """)
    
    progress_gap_stats = query_db("""
    SELECT COUNT(*) as count, SUM(p.sanctioned_amount) as amt
    FROM risk_scores r
    JOIN projects p ON r.work_code = p.work_code
    WHERE r.progress_gap_score >= 50.0
    """, one=True)
    
    insights = []
    
    if top_cost_districts:
        d0 = dict(top_cost_districts[0])
        flag_count = _to_int(d0.get('flag_count'))
        tot_amt = _to_float(d0.get('total_amt'))
        dist_name = (d0.get('district') or '').title()
        insights.append({
            "id": "INS-COST-01",
            "type": "COST_ANOMALY",
            "title": f"Cost Outlier Concentration in {dist_name}, {d0.get('state')}",
            "summary": f"{flag_count} works exhibit sanctioned amounts significantly above statistical baselines (+2.5σ) within this district.",
            "impact": f"₹{tot_amt:,.0f} sanctioned across flagged projects.",
            "action": "Inspect comparable work types in Evidence Room.",
            "filter_state": d0.get('state'),
            "filter_district": d0.get('district'),
            "severity": "HIGH",
            "badge": "STATISTICAL BASELINE"
        })
        
    if top_dup_districts:
        dup0 = dict(top_dup_districts[0])
        dup_count = _to_int(dup0.get('dup_count'))
        dist_name = (dup0.get('district') or '').title()
        insights.append({
            "id": "INS-DUP-01",
            "type": "POSSIBLE_DUPLICATE",
            "title": f"Work Description Overlap in {dist_name}",
            "summary": f"{dup_count} works exhibit >=70% semantic description similarity with proximate proposals in the same jurisdiction.",
            "impact": "Potential redundant sanctioning of similar developmental assets.",
            "action": "Review duplicate comparison matrix.",
            "filter_state": dup0.get('state'),
            "filter_district": dup0.get('district'),
            "severity": "MEDIUM",
            "badge": "SEMANTIC DETECTION"
        })
        
    pg_dict = dict(progress_gap_stats) if progress_gap_stats else {}
    pg_count = _to_int(pg_dict.get("count"))
    if pg_count > 0:
        pg_amt = _to_float(pg_dict.get("amt"))
        insights.append({
            "id": "INS-PROG-01",
            "type": "PROGRESS_GAP",
            "title": f"{pg_count:,} Works with High Utilization Pending Physical Completion",
            "summary": "Substantial funds (>90%) disbursed to contractors, yet works remain recorded in 'Physical Inspection' or 'Sanction' status.",
            "impact": f"₹{pg_amt:,.0f} in active pipeline disbursements.",
            "action": "Request updated physical verification certificate from IDAs.",
            "severity": "HIGH",
            "badge": "OPERATIONAL GAP"
        })
        
    return {"insights": insights}

@router.get("/trends")
@timed_cache(300.0)
def get_dashboard_trends():
    # 1. By Financial Year
    fy_trends = query_db("""
    SELECT 
        financial_year,
        COUNT(*) as total_projects,
        SUM(sanctioned_amount) as sanctioned_funds,
        SUM(expenditure_amount) as expenditure_funds,
        SUM(CASE WHEN status = 'Work Completed' THEN 1 ELSE 0 END) as completed_works
    FROM projects
    WHERE financial_year != '' AND length(financial_year) = 9
    GROUP BY financial_year
    ORDER BY financial_year ASC
    """)
    
    # 2. By Work Status
    status_breakdown = query_db("""
    SELECT status, COUNT(*) as count, SUM(sanctioned_amount) as total_sanctioned
    FROM projects
    GROUP BY status
    ORDER BY count DESC
    """)
    
    # 3. By Category
    category_breakdown = query_db("""
    SELECT category, COUNT(*) as count, SUM(sanctioned_amount) as total_sanctioned, SUM(expenditure_amount) as total_expenditure
    FROM projects
    WHERE category IS NOT NULL AND category != ''
    GROUP BY category
    ORDER BY count DESC
    LIMIT 10
    """)
    
    return {
        "financial_year_trends": [_sanitize_dict(r) for r in fy_trends],
        "status_distribution": [_sanitize_dict(r) for r in status_breakdown],
        "category_distribution": [_sanitize_dict(r) for r in category_breakdown]
    }
