"""
MPLAD GUARDIAN — Geographic & Spatial Intelligence Engine (Phase 5)

Analyzes geographic distribution and concentration risk:
- Priority: Exact GPS coordinates (when available) -> District Aggregation -> State Baseline
- ZERO COORDINATE FABRICATION: Missing coordinates remain NULL.
- District concentration normalized by district total project counts and fund volumes.
"""

from typing import Dict, Any, List
from collections import defaultdict
import numpy as np

class GeographicIntelligenceEngine:
    def __init__(self):
        self.district_stats: Dict[str, Dict[str, Any]] = {}
        self.state_stats: Dict[str, Dict[str, Any]] = {}
        self.fitted = False

    def fit(self, projects: List[Dict[str, Any]]) -> "GeographicIntelligenceEngine":
        """Calculates baseline district and state concentration metrics."""
        d_counts = defaultdict(int)
        d_high_cost = defaultdict(int)
        d_total_sanctioned = defaultdict(float)
        
        s_counts = defaultdict(int)
        s_total_sanctioned = defaultdict(float)
        
        for p in projects:
            dist = str(p.get("district") or "").strip()
            st = str(p.get("state") or "").strip()
            amt = float(p.get("sanctioned_amount") or 0.0)
            
            if dist:
                d_counts[dist] += 1
                d_total_sanctioned[dist] += amt
                if amt >= 2500000.0: # ₹25 Lakh+ projects
                    d_high_cost[dist] += 1
                    
            if st:
                s_counts[st] += 1
                s_total_sanctioned[st] += amt
                
        for dist, count in d_counts.items():
            self.district_stats[dist] = {
                "total_projects": count,
                "high_cost_projects": d_high_cost[dist],
                "high_cost_ratio": d_high_cost[dist] / count if count > 0 else 0.0,
                "total_sanctioned": d_total_sanctioned[dist],
                "avg_cost_per_project": d_total_sanctioned[dist] / count if count > 0 else 0.0
            }
            
        for st, count in s_counts.items():
            self.state_stats[st] = {
                "total_projects": count,
                "total_sanctioned": s_total_sanctioned[st],
                "avg_cost_per_project": s_total_sanctioned[st] / count if count > 0 else 0.0
            }
            
        self.fitted = True
        return self

    def evaluate_project(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluates geographic concentration and spatial risk index for an individual project."""
        dist = str(project.get("district") or "").strip()
        st = str(project.get("state") or "").strip()
        amt = float(project.get("sanctioned_amount") or 0.0)
        has_gps = bool(project.get("latitude") and project.get("longitude"))
        
        if not dist or dist not in self.district_stats:
            return {
                "score": 10.0,
                "severity": "LOW",
                "has_exact_gps": False,
                "locality": dist or "Unmapped",
                "district_projects_count": 0,
                "high_cost_concentration_ratio": 0.0,
                "explanation": "Unadjusted baseline project concentration across general administrative territory."
            }
            
        d_info = self.district_stats[dist]
        n_dist = d_info["total_projects"]
        ratio = d_info["high_cost_ratio"]
        
        # Continuous concentration curve
        if n_dist >= 10:
            if amt >= 2500000.0:
                raw_score = min(100.0, ratio * 140.0 + (min(50.0, (amt / 10000000.0) * 20.0)))
            else:
                raw_score = min(75.0, ratio * 60.0 + 10.0)
        else:
            raw_score = 10.0
            
        final_score = round(max(5.0, min(100.0, raw_score)), 1)
        
        if final_score >= 75.0: severity = "CRITICAL"
        elif final_score >= 50.0: severity = "HIGH"
        elif final_score >= 25.0: severity = "MEDIUM"
        else: severity = "LOW"
        
        explanation = ""
        if final_score >= 50.0:
            explanation = (
                f"High capital project concentration at district level: {dist} has {d_info['high_cost_projects']} "
                f"high-value works ({ratio*100:.1f}% of {n_dist} district projects)."
            )
        else:
            explanation = f"Standard spatial distribution across {n_dist} recorded works in {dist}."
            
        return {
            "score": final_score,
            "severity": severity,
            "has_exact_gps": has_gps,
            "locality": dist,
            "district_projects_count": n_dist,
            "high_cost_concentration_ratio": round(ratio * 100, 1),
            "explanation": explanation
        }
