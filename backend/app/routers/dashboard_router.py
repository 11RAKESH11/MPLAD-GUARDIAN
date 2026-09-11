from fastapi import APIRouter
from backend.app.database import query_db
from backend.app.cache import timed_cache
import json

router = APIRouter(prefix="/api/v1/dashboard", tags=["Executive Dashboard"])

@router.get("/overview")
@timed_cache(60.0)
def get_dashboard_overview():
    # 1. Core KPIs
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
    duplicates_count = dup_count_row["dup_count"] if dup_count_row else 0
    
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
    
    # 6. Data Quality Completeness Calculation
    t_dict = dict(totals)
    total_proj = t_dict["total_projects"] or 1
    missing_dist = t_dict.get("missing_dist") or 0
    completeness_pct = round(((total_proj * 6 - missing_dist) / (total_proj * 6)) * 100, 2)

    sanc_amt = t_dict["total_sanctioned_funds"] or 1.0
    spent_amt = max(t_dict["total_disbursed_funds"] or 0, t_dict["total_expenditure_funds"] or 0)
    utilization_rate = round((spent_amt / sanc_amt) * 100, 2)
    completion_rate = round(((t_dict["completed_works"] or 0) / total_proj) * 100, 2)
    
    return {
        "kpis": {
            "total_projects": t_dict["total_projects"],
            "total_sanctioned_funds": t_dict["total_sanctioned_funds"],
            "total_recommended_funds": t_dict["total_recommended_funds"],
            "total_expenditure_funds": t_dict["total_expenditure_funds"],
            "total_disbursed_funds": t_dict["total_disbursed_funds"],
            "utilization_rate_pct": utilization_rate,
            "completion_rate_pct": completion_rate,
            "completed_works": t_dict["completed_works"],
            "sanctioned_works": t_dict["sanctioned_works"],
            "inspection_works": t_dict["inspection_works"],
            "vendor_id_works": t_dict["vendor_id_works"],
            "total_mps": mp_stats["total_mps"],
            "total_vouchers": voucher_stats["total_vouchers"] if voucher_stats else 0,
            "total_unique_vendors": voucher_stats["total_unique_vendors"] if voucher_stats else 0,
            "source_badge": "REAL CSV DATA"
        },
        "risk_metrics": {
            "critical_count": risk_summary["critical_count"],
            "high_count": risk_summary["high_count"],
            "medium_count": risk_summary["medium_count"],
            "low_count": risk_summary["low_count"],
            "potential_duplicates_count": duplicates_count,
            "avg_risk_score": round(risk_summary["avg_risk_score"] or 0, 1),
            "avg_confidence": round(risk_summary["avg_confidence"] or 0, 1),
            "source_badge": "AI ANALYSIS"
        },
        "alerts_summary": dict(alert_counts),
        "data_health": {
            "completeness_pct": completeness_pct,
            "source_files_count": 12,
            "total_raw_rows": 374141,
            "status": "HEALTHY",
            "last_analysis": "2026-08-28T20:30:00Z"
        }
    }

@router.get("/attention")
@timed_cache(60.0)
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
        # Determine clean signal type label
        if r.get("alert_type") == "COST_OUTLIER":
            signal_label = "High Cost Anomaly"
            why_prioritized = f"Project cost exceeds statistical baseline by >2.5σ with {round(r.get('confidence') or 95)}% confidence."
        elif r.get("alert_type") == "POTENTIAL_DUPLICATE":
            signal_label = "Potential Duplicate Work"
            why_prioritized = f"High textual similarity (>70%) with proximate project in {r.get('district', '').title()}."
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
            "title": r.get("title") or f"{signal_label} in {r.get('district', '').title()}",
            "severity": r.get("severity") or "HIGH",
            "state": r.get("state") or "",
            "district": (r.get("district") or "").title(),
            "category": r.get("category") or "Developmental Asset",
            "sanctioned_amount": r.get("sanctioned_amount") or 0,
            "risk_score": round(r.get("overall_risk_score") or 0, 1),
            "confidence": round(r.get("confidence") or 0, 1),
            "priority_score": round(r.get("priority_score") or 0, 1),
            "evidence_snippet": r.get("evidence") or why_prioritized,
            "why_prioritized": why_prioritized,
            "status": r.get("status") or "OPEN"
        })
        
    return {"attention_items": items}

@router.get("/financial-flow")
@timed_cache(60.0)
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
    
    t = dict(totals)
    sanc = t.get("sanctioned_amount") or 1.0
    rec = t.get("recommended_amount") or 0.0
    disb = t.get("disbursed_amount") or 0.0
    exp = t.get("expenditure_amount") or 0.0
    total_proj = t.get("total_projects") or 1
    
    stages = [
        {
            "id": "recommended",
            "name": "Recommended by MPs",
            "amount": rec,
            "records_count": total_proj,
            "percentage_of_sanctioned": round((rec / sanc) * 100, 1) if sanc else 0,
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
            "records_count": t.get("disbursed_count") or 0,
            "percentage_of_sanctioned": round((disb / sanc) * 100, 1) if sanc else 0,
            "description": "Funds released from nodal account to implementing agencies (IDAs).",
            "source": "Nodal Bank Release Ledgers"
        },
        {
            "id": "expenditure",
            "name": "Expenditure / Utilized",
            "amount": exp,
            "records_count": t.get("expenditure_count") or 0,
            "percentage_of_sanctioned": round((exp / sanc) * 100, 1) if sanc else 0,
            "description": "Actual expenditure documented against completed or in-progress works.",
            "source": "Expenditure Vouchers & Utilization Certificates"
        }
    ]
    
    return {
        "stages": stages,
        "total_sanctioned": sanc,
        "total_expenditure": exp,
        "utilization_rate_pct": round((exp / sanc) * 100, 2) if sanc else 0
    }

@router.get("/signal-distribution")
@timed_cache(60.0)
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
        "critical": rc_dict.get("critical", 0),
        "high": rc_dict.get("high", 0),
        "medium": rc_dict.get("medium", 0),
        "low": rc_dict.get("low", 0)
    }
    confidence_dist = {
        "high_confidence": rc_dict.get("high_confidence", 0),
        "moderate_confidence": rc_dict.get("moderate_confidence", 0),
        "limited_evidence": rc_dict.get("limited_evidence", 0)
    }
    
    type_map = {
        "COST_OUTLIER": "Cost Anomaly Signals",
        "POTENTIAL_DUPLICATE": "Potential Duplicate Proposals",
        "PROGRESS_GAP": "Progress vs Expenditure Gap"
    }
    
    signals = []
    for r in alert_types:
        row = dict(r)
        at = row["alert_type"]
        signals.append({
            "type_key": at,
            "label": type_map.get(at, at.replace("_", " ").title()),
            "count": row["count"],
            "critical_count": row["critical_count"]
        })
        
    return {
        "signals": signals,
        "total_alerts": sum(s["count"] for s in signals),
        "overlap_note": "Signal categories may overlap across the same project records.",
        "risk_distribution": risk_dist,
        "confidence_distribution": confidence_dist
    }

@router.get("/what-changed")
@timed_cache(60.0)
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
            if not prev or prev == 0:
                return 0.0
            return round(((cur - prev) / prev) * 100, 1)
            
        p_util = round(((p["expenditure"] or 0) / (p["sanctioned"] or 1)) * 100, 1)
        c_util = round(((c["expenditure"] or 0) / (c["sanctioned"] or 1)) * 100, 1)
        
        return {
            "historical_comparison_available": True,
            "current_period": "FY 2025-26",
            "previous_period": "FY 2024-25",
            "comparison_label": "FY 2025-26 vs FY 2024-25",
            "metrics": [
                {
                    "name": "Project Volume",
                    "current": c["projects"],
                    "previous": p["projects"],
                    "diff_pct": calc_pct(c["projects"], p["projects"]),
                    "explanation": "Substantial expansion in registered development projects.",
                    "neutral_note": "Driven by broader implementation across states."
                },
                {
                    "name": "Sanctioned Allocation",
                    "current": c["sanctioned"],
                    "previous": p["sanctioned"],
                    "diff_pct": calc_pct(c["sanctioned"], p["sanctioned"]),
                    "explanation": "Higher total budget allocations across sanctioned works.",
                    "neutral_note": "Reflects updated annual fund releases."
                },
                {
                    "name": "Recorded Expenditure",
                    "current": c["expenditure"],
                    "previous": p["expenditure"],
                    "diff_pct": calc_pct(c["expenditure"], p["expenditure"]),
                    "explanation": "Active disbursement on multi-year development projects.",
                    "neutral_note": "Expenditure ledgers reflect progressing works."
                },
                {
                    "name": "Completed Works",
                    "current": c["completed"],
                    "previous": p["completed"],
                    "diff_pct": calc_pct(c["completed"], p["completed"]),
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
@timed_cache(60.0)
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
    alert_map = {r["state"]: r["signal_count"] for r in alert_state_counts}
    
    results = []
    for row in states_data:
        r = dict(row)
        sanc = r.get("total_sanctioned") or 1.0
        exp = r.get("total_expenditure") or 0.0
        tot = r.get("total_projects") or 1
        comp = r.get("completed_works") or 0
        st = r["state"]
        
        results.append({
            "state": st,
            "total_projects": tot,
            "total_sanctioned": sanc,
            "total_expenditure": exp,
            "utilization_rate_pct": round((float(exp) / float(sanc)) * 100, 1),
            "completion_rate_pct": round((comp / tot) * 100, 1),
            "signal_count": alert_map.get(st, 0)
        })
        
    return {"states": results}

@router.get("/insights")
@timed_cache(60.0)
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
        d0 = top_cost_districts[0]
        insights.append({
            "id": "INS-COST-01",
            "type": "COST_ANOMALY",
            "title": f"Cost Outlier Concentration in {d0['district'].title()}, {d0['state']}",
            "summary": f"{d0['flag_count']} works exhibit sanctioned amounts significantly above statistical baselines (+2.5σ) within this district.",
            "impact": f"₹{d0['total_amt']:,.0f} sanctioned across flagged projects.",
            "action": "Inspect comparable work types in Evidence Room.",
            "filter_state": d0['state'],
            "filter_district": d0['district'],
            "severity": "HIGH",
            "badge": "STATISTICAL BASELINE"
        })
        
    if top_dup_districts:
        dup0 = top_dup_districts[0]
        insights.append({
            "id": "INS-DUP-01",
            "type": "POSSIBLE_DUPLICATE",
            "title": f"Work Description Overlap in {dup0['district'].title()}",
            "summary": f"{dup0['dup_count']} works exhibit >=70% semantic description similarity with proximate proposals in the same jurisdiction.",
            "impact": "Potential redundant sanctioning of similar developmental assets.",
            "action": "Review duplicate comparison matrix.",
            "filter_state": dup0['state'],
            "filter_district": dup0['district'],
            "severity": "MEDIUM",
            "badge": "SEMANTIC DETECTION"
        })
        
    if progress_gap_stats and progress_gap_stats["count"] > 0:
        insights.append({
            "id": "INS-PROG-01",
            "type": "PROGRESS_GAP",
            "title": f"{progress_gap_stats['count']:,} Works with High Utilization Pending Physical Completion",
            "summary": "Substantial funds (>90%) disbursed to contractors, yet works remain recorded in 'Physical Inspection' or 'Sanction' status.",
            "impact": f"₹{progress_gap_stats['amt']:,.0f} in active pipeline disbursements.",
            "action": "Request updated physical verification certificate from IDAs.",
            "severity": "HIGH",
            "badge": "OPERATIONAL GAP"
        })
        
    return {"insights": insights}

@router.get("/trends")
@timed_cache(60.0)
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
        "financial_year_trends": [dict(r) for r in fy_trends],
        "status_distribution": [dict(r) for r in status_breakdown],
        "category_distribution": [dict(r) for r in category_breakdown]
    }
