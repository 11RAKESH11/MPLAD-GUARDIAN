"""
MPLAD GUARDIAN — Idempotent Alert Generation & Investigation Prioritization (Phase 5)

Generates explainable anomaly alerts with deterministic fingerprints to prevent duplicate alert rows.
"""

from typing import Dict, Any, List, Optional
import hashlib
import datetime

def generate_alert_fingerprint(work_code: str, alert_type: str, model_version: str = "guardian-risk-2.0.0-shadow") -> str:
    """Creates a deterministic, reproducible alert ID."""
    raw = f"{work_code}:{alert_type}:{model_version}"
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10].upper()
    return f"ALT-{h}"

def generate_alerts_for_evaluation(
    eval_result: Dict[str, Any],
    project: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Generates structured alerts for projects with significant analytical anomaly signals.
    """
    alerts = []
    code = eval_result["work_code"]
    risk_level = eval_result["risk_level"]
    overall_risk = eval_result["overall_risk_score"]
    c_score = eval_result["cost_anomaly_score"]
    d_score = eval_result["duplicate_score"]
    p_score = eval_result["progress_gap_score"]
    g_score = eval_result["geographic_score"]
    priority_score = eval_result["priority_score"]
    investigation_priority = eval_result["investigation_priority"]
    explanation = eval_result["explanation_json"]
    model_version = eval_result["model_version"]
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    st = str(project.get("state") or "")
    dist = str(project.get("district") or "")
    work_type = str(project.get("work_type") or project.get("category") or "Project")
    
    # 1. Cost Outlier Alert
    if c_score >= 60.0:
        alert_id = generate_alert_fingerprint(code, "COST_OUTLIER", model_version)
        alerts.append({
            "id": alert_id,
            "work_code": code,
            "alert_type": "COST_OUTLIER",
            "title": f"Cost Outlier Signal: {work_type[:60]}",
            "severity": "CRITICAL" if c_score >= 80.0 else "HIGH",
            "status": "OPEN",
            "state": st,
            "district": dist,
            "evidence": explanation["why_flagged"][0] if explanation["why_flagged"] else "Sanctioned cost is statistically unusual.",
            "impact": f"Sanctioned Amount: ₹{float(project.get('sanctioned_amount') or 0.0):,.0f}",
            "action_recommendation": "Review administrative cost benchmark and itemized rate list.",
            "priority_score": priority_score,
            "impact_level": investigation_priority,
            "created_at": now
        })
        
    # 2. Potential Duplicate Alert
    if d_score >= 65.0:
        alert_id = generate_alert_fingerprint(code, "POTENTIAL_DUPLICATE", model_version)
        alerts.append({
            "id": alert_id,
            "work_code": code,
            "alert_type": "POTENTIAL_DUPLICATE",
            "title": f"Potential Duplicate Work: {work_type[:60]}",
            "severity": "CRITICAL" if d_score >= 80.0 else "HIGH",
            "status": "OPEN",
            "state": st,
            "district": dist,
            "evidence": f"Multi-signal description and financial parity match ({d_score:.0f}%) with peer project in locality.",
            "impact": f"Potential duplicate allocation across {dist}",
            "action_recommendation": "Cross-check site sanction order with existing completed works in locality.",
            "priority_score": priority_score,
            "impact_level": investigation_priority,
            "created_at": now
        })
        
    # 3. Progress Gap Alert
    if p_score >= 50.0:
        alert_id = generate_alert_fingerprint(code, "PROGRESS_GAP", model_version)
        alerts.append({
            "id": alert_id,
            "work_code": code,
            "alert_type": "PROGRESS_GAP",
            "title": f"Operational Progress Gap: {work_type[:60]}",
            "severity": "CRITICAL" if p_score >= 75.0 else "HIGH",
            "status": "OPEN",
            "state": st,
            "district": dist,
            "evidence": explanation["why_flagged"][-1] if explanation["why_flagged"] else "Significant operational progress contradiction.",
            "impact": f"Voucher Expenditure: ₹{float(project.get('expenditure_amount') or 0.0):,.0f}",
            "action_recommendation": "Request milestone verification certificate from Implementing Agency.",
            "priority_score": priority_score,
            "impact_level": investigation_priority,
            "created_at": now
        })
        
    return alerts
