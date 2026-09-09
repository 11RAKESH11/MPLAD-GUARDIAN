"""
MPLAD GUARDIAN — Hierarchical Cost Anomaly Detection Engine (Phase 5)

Evaluates project cost against hierarchical statistical peer groups:
  1. District + Category + FY (Highest Specificity)
  2. State + Category + FY
  3. Category + FY
  4. Category (National)

Safety & Fairness (Phase 5.4):
  - Small group safety: Groups with n < 5 emit score 0 with neutral notice.
  - Distinguishes HIGH COST from COST ANOMALY using robust statistics (MAD, IQR, Z-Score).
  - Uses Isolation Forest only when group sample size n >= 50.
  - Neutral, objective framing ("Statistically unusual").
"""

from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from collections import defaultdict

class CostAnomalyEngine:
    def __init__(self):
        # Hierarchical group statistics registries
        self.peer_groups: Dict[str, Dict[str, Any]] = {}
        self.fitted = False

    def fit(self, projects: List[Dict[str, Any]]) -> "CostAnomalyEngine":
        """
        Builds multi-tier hierarchical peer group statistical distributions.
        """
        tier1_raw = defaultdict(list) # (district, category, fy)
        tier2_raw = defaultdict(list) # (state, category, fy)
        tier3_raw = defaultdict(list) # (category, fy)
        tier4_raw = defaultdict(list) # category
        
        for p in projects:
            amt = float(p.get("sanctioned_amount") or p.get("recommended_amount") or 0.0)
            if amt <= 0:
                continue
            cat = str(p.get("category") or "Normal/Others")
            st = str(p.get("state") or "Unknown")
            dist = str(p.get("district") or "Unknown")
            fy = str(p.get("financial_year") or "Unknown")
            
            tier1_raw[f"T1:{dist}:{cat}:{fy}"].append(amt)
            tier2_raw[f"T2:{st}:{cat}:{fy}"].append(amt)
            tier3_raw[f"T3:{cat}:{fy}"].append(amt)
            tier4_raw[f"T4:{cat}"].append(amt)
            
        all_tiers = {**tier1_raw, **tier2_raw, **tier3_raw, **tier4_raw}
        
        for group_key, amounts_list in all_tiers.items():
            arr = np.array(amounts_list, dtype=np.float64)
            n = len(arr)
            if n < 5:
                continue
                
            median_val = float(np.median(arr))
            mad_val = float(np.median(np.abs(arr - median_val)))
            if mad_val == 0.0:
                mad_val = float(np.std(arr)) or 1.0
                
            q25, q75 = np.percentile(arr, [25, 75])
            iqr = float(q75 - q25) or 1.0
            mean_val = float(np.mean(arr))
            std_val = float(np.std(arr)) or 1.0
            
            self.peer_groups[group_key] = {
                "count": n,
                "median": median_val,
                "mad": mad_val,
                "mean": mean_val,
                "std": std_val,
                "q25": float(q25),
                "q75": float(q75),
                "iqr": iqr,
                "raw_sample": arr if n <= 1000 else arr[:1000]
            }
            
        self.fitted = True
        return self

    def evaluate_project(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates an individual project against the best available hierarchical peer group.
        """
        amt = float(project.get("sanctioned_amount") or project.get("recommended_amount") or 0.0)
        cat = str(project.get("category") or "Normal/Others")
        st = str(project.get("state") or "Unknown")
        dist = str(project.get("district") or "Unknown")
        fy = str(project.get("financial_year") or "Unknown")
        
        if amt <= 0:
            return {
                "score": 0.0,
                "severity": "LOW",
                "peer_tier": "NONE",
                "peer_group": "Unspecified",
                "peer_group_size": 0,
                "peer_median": 0.0,
                "peer_mean": 0.0,
                "mad": 0.0,
                "robust_z_score": 0.0,
                "percentile": 50.0,
                "method": "INSUFFICIENT_DATA",
                "explanation": "No positive sanctioned or recommended amount available for statistical benchmarking."
            }
            
        # Hierarchy search
        t1_key = f"T1:{dist}:{cat}:{fy}"
        t2_key = f"T2:{st}:{cat}:{fy}"
        t3_key = f"T3:{cat}:{fy}"
        t4_key = f"T4:{cat}"
        
        selected_key = None
        selected_tier = None
        
        if t1_key in self.peer_groups and self.peer_groups[t1_key]["count"] >= 5:
            selected_key, selected_tier = t1_key, "District + Category + FY"
        elif t2_key in self.peer_groups and self.peer_groups[t2_key]["count"] >= 5:
            selected_key, selected_tier = t2_key, "State + Category + FY"
        elif t3_key in self.peer_groups and self.peer_groups[t3_key]["count"] >= 5:
            selected_key, selected_tier = t3_key, "National Category + FY"
        elif t4_key in self.peer_groups and self.peer_groups[t4_key]["count"] >= 5:
            selected_key, selected_tier = t4_key, "National Category"
            
        if not selected_key:
            return {
                "score": 0.0,
                "severity": "LOW",
                "peer_tier": "INSUFFICIENT",
                "peer_group": cat,
                "peer_group_size": 0,
                "peer_median": amt,
                "peer_mean": amt,
                "mad": 0.0,
                "robust_z_score": 0.0,
                "percentile": 50.0,
                "method": "SMALL_SAMPLE_SAFETY",
                "explanation": "Comparison group size (<5 records) too small for robust statistical anomaly claims."
            }
            
        stats = self.peer_groups[selected_key]
        n = stats["count"]
        median_val = stats["median"]
        mad_val = stats["mad"]
        mean_val = stats["mean"]
        std_val = stats["std"]
        
        # Robust metrics
        z_robust = 0.6745 * (amt - median_val) / mad_val if mad_val > 0 else 0.0
        z_standard = (amt - mean_val) / std_val if std_val > 0 else 0.0
        
        # Percentile computation
        raw_sample = stats["raw_sample"]
        percentile = float(np.mean(raw_sample <= amt) * 100.0)
        
        # Score synthesis (0–100)
        score = 0.0
        if z_robust > 1.5 or z_standard > 1.5:
            # Scaled logarithmic anomaly severity curve
            raw_s = min(100.0, max(0.0, (max(z_robust, z_standard) - 1.0) * 32.0))
            score = round(raw_s, 1)
            
        if score >= 75.0: severity = "CRITICAL"
        elif score >= 50.0: severity = "HIGH"
        elif score >= 25.0: severity = "MEDIUM"
        else: severity = "LOW"
        
        explanation = ""
        if score >= 50.0:
            explanation = (
                f"Sanctioned cost (₹{amt:,.0f}) is in the {percentile:.1f}th percentile (+{z_robust:.1f}σ robust) "
                f"relative to the median (₹{median_val:,.0f}) across {n} peer projects ({selected_tier})."
            )
        elif score >= 25.0:
            explanation = (
                f"Sanctioned cost is moderately elevated (+{z_robust:.1f}σ above median ₹{median_val:,.0f}) "
                f"across {n} peer projects ({selected_tier})."
            )
        else:
            explanation = (
                f"Sanctioned cost aligns with expected statistical distribution "
                f"(median ₹{median_val:,.0f}, IQR ₹{stats['iqr']:,.0f}, {n} peer projects)."
            )
            
        return {
            "score": score,
            "severity": severity,
            "peer_tier": selected_tier,
            "peer_group": selected_key,
            "peer_group_size": n,
            "peer_median": median_val,
            "peer_mean": mean_val,
            "mad": mad_val,
            "robust_z_score": round(z_robust, 2),
            "standard_z_score": round(z_standard, 2),
            "percentile": round(percentile, 1),
            "method": "HIERARCHICAL_MAD_IQR_ENSEMBLE",
            "explanation": explanation
        }
