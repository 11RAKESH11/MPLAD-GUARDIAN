"""
MPLAD GUARDIAN — Explicit Progress Gap & Operational Integrity Rule Engine (Phase 5)

Evaluates explicit deterministic lifecycle rules (R1 to R8) against verified project data.
Only activates a rule when all requisite source fields exist.
"""

from typing import Dict, Any, List, Optional
import datetime

class ProgressRuleEngine:
    def __init__(self):
        self.rules_definitions = {
            "R1": {"name": "High Utilization on Incomplete Work", "weight": 40.0, "severity": "HIGH"},
            "R2": {"name": "Aging Work with Delayed Completion", "weight": 25.0, "severity": "MEDIUM"},
            "R3": {"name": "Disbursement Exceeds Administrative Sanction", "weight": 35.0, "severity": "HIGH"},
            "R4": {"name": "Voucher Expenditure Exceeds Sanctioned Limit", "weight": 35.0, "severity": "HIGH"},
            "R5": {"name": "Completed Status with Zero/Negligible Disbursement", "weight": 20.0, "severity": "MEDIUM"},
            "R6": {"name": "Temporal Anomaly (Completion Precedes Sanction)", "weight": 50.0, "severity": "CRITICAL"},
            "R7": {"name": "Anomalous Future Completion Timestamp", "weight": 25.0, "severity": "MEDIUM"},
            "R8": {"name": "Negative Financial Accounting Anomaly", "weight": 50.0, "severity": "CRITICAL"}
        }

    def evaluate(self, project: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates project against all 8 deterministic progress and lifecycle integrity rules.
        """
        triggered = []
        accumulated_score = 0.0
        
        status = str(project.get("status") or "").strip()
        is_completed = status in ("Work Completed", "Completed")
        
        sanctioned = float(project.get("sanctioned_amount") or 0.0)
        disbursed = float(project.get("disbursed_amount") or 0.0)
        expenditure = float(project.get("expenditure_amount") or 0.0)
        util_pct = features.get("utilization_pct", 0.0)
        age_months = features.get("age_months", 0.0)
        
        s_date_str = features.get("sanction_date")
        c_date_str = features.get("completion_date")
        
        # Rule R1: High utilization (>90%) but incomplete status
        if util_pct >= 90.0 and not is_completed and sanctioned > 0:
            accumulated_score += 40.0
            triggered.append({
                "rule_id": "R1",
                "rule_name": self.rules_definitions["R1"]["name"],
                "severity": "HIGH",
                "actual_value": f"Utilization: {util_pct:.1f}%, Status: '{status}'",
                "threshold": "Utilization >= 90.0% with non-completed status",
                "explanation": f"Substantial fund utilization ({util_pct:.1f}%) reported, but operational status remains '{status}'."
            })
            
        # Rule R2: Aging work (>24 months) with active funds but incomplete status
        if age_months >= 24.0 and not is_completed and (disbursed > 0 or expenditure > 0):
            accumulated_score += 25.0
            triggered.append({
                "rule_id": "R2",
                "rule_name": self.rules_definitions["R2"]["name"],
                "severity": "MEDIUM",
                "actual_value": f"Project Age: {age_months:.0f} months, Status: '{status}'",
                "threshold": "Age >= 24 months with active disbursements",
                "explanation": f"Project has been active for {age_months:.0f} months with recorded funds, but work is still '{status}'."
            })
            
        # Rule R3: Disbursed > Sanctioned
        if sanctioned > 0 and disbursed > sanctioned * 1.02:
            over = disbursed - sanctioned
            accumulated_score += 35.0
            triggered.append({
                "rule_id": "R3",
                "rule_name": self.rules_definitions["R3"]["name"],
                "severity": "HIGH",
                "actual_value": f"Disbursed: ₹{disbursed:,.0f} vs Sanctioned: ₹{sanctioned:,.0f}",
                "threshold": "Disbursed > Sanctioned (+2% tolerance)",
                "explanation": f"Disbursed funds exceed administrative sanction by ₹{over:,.0f}."
            })
            
        # Rule R4: Expenditure > Sanctioned * 1.05
        if sanctioned > 0 and expenditure > sanctioned * 1.05:
            over = expenditure - sanctioned
            accumulated_score += 35.0
            triggered.append({
                "rule_id": "R4",
                "rule_name": self.rules_definitions["R4"]["name"],
                "severity": "HIGH",
                "actual_value": f"Expenditure: ₹{expenditure:,.0f} vs Sanctioned: ₹{sanctioned:,.0f}",
                "threshold": "Voucher Expenditure > 1.05 * Sanctioned Amount",
                "explanation": f"Voucher payment lineage exceeds administrative sanction limit by ₹{over:,.0f}."
            })
            
        # Rule R5: Completed status with negligible funds (<10% util) on non-zero project
        if is_completed and sanctioned >= 100000.0 and max(disbursed, expenditure) < (sanctioned * 0.10):
            accumulated_score += 20.0
            triggered.append({
                "rule_id": "R5",
                "rule_name": self.rules_definitions["R5"]["name"],
                "severity": "MEDIUM",
                "actual_value": f"Status: '{status}', Spent: ₹{max(disbursed, expenditure):,.0f} of ₹{sanctioned:,.0f}",
                "threshold": "Completed status with <10% recorded financial utilization",
                "explanation": "Project marked physically completed without corresponding financial voucher reconciliation."
            })
            
        # Rule R6: Completion date before sanction date
        if s_date_str and c_date_str:
            try:
                s_d = datetime.datetime.strptime(s_date_str[:10], "%Y-%m-%d").date()
                c_d = datetime.datetime.strptime(c_date_str[:10], "%Y-%m-%d").date()
                if c_d < s_d:
                    accumulated_score += 50.0
                    triggered.append({
                        "rule_id": "R6",
                        "rule_name": self.rules_definitions["R6"]["name"],
                        "severity": "CRITICAL",
                        "actual_value": f"Sanction: {s_date_str}, Completion: {c_date_str}",
                        "threshold": "Completion Date >= Sanction Date",
                        "explanation": f"Temporal contradiction: Completion date ({c_date_str}) precedes official sanction date ({s_date_str})."
                    })
            except Exception:
                pass
                
        # Rule R7: Anomalous future completion date (>2030)
        if c_date_str:
            try:
                c_d = datetime.datetime.strptime(c_date_str[:10], "%Y-%m-%d").date()
                if c_d.year > 2030:
                    accumulated_score += 25.0
                    triggered.append({
                        "rule_id": "R7",
                        "rule_name": self.rules_definitions["R7"]["name"],
                        "severity": "MEDIUM",
                        "actual_value": f"Completion Date: {c_date_str}",
                        "threshold": "Completion Year <= 2030",
                        "explanation": f"Anomalous distant future completion year ({c_d.year}) recorded in source metadata."
                    })
            except Exception:
                pass
                
        # Rule R8: Negative financial values
        if sanctioned < 0 or disbursed < 0 or expenditure < 0:
            accumulated_score += 50.0
            triggered.append({
                "rule_id": "R8",
                "rule_name": self.rules_definitions["R8"]["name"],
                "severity": "CRITICAL",
                "actual_value": f"Sanction: ₹{sanctioned}, Disbursed: ₹{disbursed}, Exp: ₹{expenditure}",
                "threshold": "Financial values >= 0",
                "explanation": "Negative monetary figure recorded in accounting ledger."
            })
            
        final_score = round(min(100.0, accumulated_score), 1)
        
        if final_score >= 75.0: severity = "CRITICAL"
        elif final_score >= 50.0: severity = "HIGH"
        elif final_score >= 25.0: severity = "MEDIUM"
        else: severity = "LOW"
        
        reasons_summary = [r["explanation"] for r in triggered]
        if not reasons_summary:
            reasons_summary = ["Operational milestones and financial voucher velocity align with standard scheme parameters."]
            
        return {
            "score": final_score,
            "severity": severity,
            "rules_triggered_count": len(triggered),
            "triggered_rules": triggered,
            "reasons": reasons_summary,
            "explanation": reasons_summary[0]
        }
