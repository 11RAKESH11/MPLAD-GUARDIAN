"""
MPLAD GUARDIAN — Composite Risk Intelligence & Explainability Engine (Phase 5)

Synthesizes multi-dimensional signals into explainable, deterministic risk scores:
- Dynamic Weight Renormalization when dimensions are missing in source data
- Deterministic 0–100 Overall Risk Score (Low, Medium, High, Critical)
- Independent Confidence Score (0–100%) and Evidence Coverage Score (0–100%)
- Structured Explainable JSON with actionable recommendations and evidence decomposition
- Model Version: 'guardian-risk-2.0.0-shadow'
"""

from typing import Dict, Any, List, Optional
import json
import datetime
try:
    from .features import extract_project_features
    from .cost_anomaly import CostAnomalyEngine
    from .duplicate_engine import DuplicateEngine
    from .progress_rules import ProgressRuleEngine
    from .geo_intelligence import GeographicIntelligenceEngine
except (ImportError, ValueError):
    from features import extract_project_features
    from cost_anomaly import CostAnomalyEngine
    from duplicate_engine import DuplicateEngine
    from progress_rules import ProgressRuleEngine
    from geo_intelligence import GeographicIntelligenceEngine

MODEL_VERSION = "guardian-risk-2.0.0-shadow"
ALGORITHM_VERSION = "2.1.0"
FEATURE_VERSION = "2.0.0"

class RiskEngine:
    def __init__(
        self,
        base_weight_cost: float = 0.30,
        base_weight_dup: float = 0.30,
        base_weight_prog: float = 0.25,
        base_weight_geo: float = 0.15
    ):
        self.w_cost = base_weight_cost
        self.w_dup = base_weight_dup
        self.w_prog = base_weight_prog
        self.w_geo = base_weight_geo
        
        self.cost_engine = CostAnomalyEngine()
        self.dup_engine = DuplicateEngine()
        self.prog_engine = ProgressRuleEngine()
        self.geo_engine = GeographicIntelligenceEngine()
        self.is_fitted = False

    def fit(self, projects: List[Dict[str, Any]]) -> "RiskEngine":
        """Fits statistical baselines across all engines."""
        self.cost_engine.fit(projects)
        self.geo_engine.fit(projects)
        self.is_fitted = True
        return self

    def evaluate_project(
        self,
        project: Dict[str, Any],
        duplicate_candidates: Optional[List[Dict[str, Any]]] = None,
        precomputed_dup_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes full multi-dimensional evaluation for a project.
        """
        features = extract_project_features(project)
        code = project.get("work_code", "UNKNOWN")
        
        # 1. Cost Anomaly Evaluation
        cost_eval = self.cost_engine.evaluate_project(project)
        c_score = cost_eval["score"]
        
        # 2. Duplicate Evaluation
        if precomputed_dup_info:
            dup_eval = precomputed_dup_info
        elif duplicate_candidates:
            dup_eval = self.dup_engine.evaluate_single_project(project, duplicate_candidates)
        else:
            dup_eval = {"score": 0.0, "severity": "LOW", "matched_count": 0, "top_matches": [], "explanation": "No duplicate comparison executed."}
        d_score = dup_eval["score"]
        
        # 3. Progress Gap Evaluation
        prog_eval = self.prog_engine.evaluate(project, features)
        p_score = prog_eval["score"]
        
        # 4. Geographic Concentration Evaluation
        geo_eval = self.geo_engine.evaluate_project(project)
        g_score = geo_eval["score"]
        
        # 5. Dynamic Weight Renormalization (Phase 5.12)
        active_weights = {}
        if features["evidence_available_dimensions"]["financial"]:
            active_weights["cost"] = self.w_cost
        if features["evidence_available_dimensions"]["text"]:
            active_weights["dup"] = self.w_dup
        if features["evidence_available_dimensions"]["lifecycle"]:
            active_weights["prog"] = self.w_prog
        if features["evidence_available_dimensions"]["geographic"]:
            active_weights["geo"] = self.w_geo
            
        total_active_weight = sum(active_weights.values()) or 1.0
        norm_w_cost = (active_weights.get("cost", 0.0) / total_active_weight)
        norm_w_dup = (active_weights.get("dup", 0.0) / total_active_weight)
        norm_w_prog = (active_weights.get("prog", 0.0) / total_active_weight)
        norm_w_geo = (active_weights.get("geo", 0.0) / total_active_weight)
        
        # 6. Composite Score Synthesis (0–100)
        raw_composite = (
            (norm_w_cost * c_score) +
            (norm_w_dup * d_score) +
            (norm_w_prog * p_score) +
            (norm_w_geo * g_score)
        )
        overall_risk = round(min(100.0, max(0.0, raw_composite)), 1)
        
        if overall_risk >= 75.0: risk_level = "CRITICAL"
        elif overall_risk >= 50.0: risk_level = "HIGH"
        elif overall_risk >= 25.0: risk_level = "MEDIUM"
        else: risk_level = "LOW"
        
        # 7. Independent Confidence Score (Phase 5.14)
        base_confidence = 65.0
        if cost_eval["peer_group_size"] >= 20: base_confidence += 15.0
        elif cost_eval["peer_group_size"] >= 5: base_confidence += 10.0
        if features["has_sanctioned"]: base_confidence += 5.0
        if features["has_district"]: base_confidence += 5.0
        if features["has_rich_text"]: base_confidence += 5.0
        if features["has_sanction_date"]: base_confidence += 5.0
        confidence_score = round(min(98.0, base_confidence), 1)
        
        evidence_coverage_score = features["evidence_coverage_pct"]
        
        # 8. Multi-Signal Corroboration & Investigation Priority (Phase 5.30 & 5.32)
        signals_triggered = []
        if c_score >= 50.0: signals_triggered.append("COST_ANOMALY")
        if d_score >= 60.0: signals_triggered.append("POTENTIAL_DUPLICATE")
        if p_score >= 50.0: signals_triggered.append("PROGRESS_GAP")
        if g_score >= 50.0: signals_triggered.append("GEOGRAPHIC_CONCENTRATION")
        
        fin_exposure_weight = min(100.0, (features["sanctioned_amount"] / 5000000.0) * 100.0)
        priority_score = round(
            (0.45 * overall_risk) +
            (0.25 * fin_exposure_weight) +
            (0.15 * confidence_score) +
            (0.15 * (min(3, len(signals_triggered)) / 3.0 * 100.0)),
            1
        )
        
        if priority_score >= 75.0: investigation_priority = "CRITICAL"
        elif priority_score >= 50.0: investigation_priority = "HIGH"
        elif priority_score >= 25.0: investigation_priority = "MEDIUM"
        else: investigation_priority = "LOW"
        
        # 9. Bullet Point Explanations & Structured Recommendations
        why_flagged = []
        if c_score >= 40.0 and cost_eval.get("explanation"):
            why_flagged.append(cost_eval["explanation"])
            
        dup_exp = dup_eval.get("explanation")
        if not dup_exp and dup_eval.get("matched_pairs"):
            dup_exp = dup_eval["matched_pairs"][0].get("reason")
        if d_score >= 50.0 and dup_exp:
            why_flagged.append(dup_exp)
            
        if p_score >= 30.0:
            for r in prog_eval.get("reasons", []):
                why_flagged.append(r)
                
        if g_score >= 50.0 and geo_eval.get("explanation"):
            why_flagged.append(geo_eval["explanation"])
        
        if not why_flagged:
            why_flagged.append("Developmental metrics and operational disbursements align with standard scheme distributions.")
            
        recommendation = "Standard periodic administrative monitoring."
        if risk_level == "CRITICAL" or len(signals_triggered) >= 2:
            recommendation = (
                "Priority desk & physical inspection recommended. Verify contractor milestone certification, "
                "reconcile expenditure vouchers against administrative sanction, and verify site GPS coordinates."
            )
        elif risk_level == "HIGH":
            recommendation = (
                "Desk review recommended. Verify execution timeline and voucher lineage with Implementing District Authority (IDA)."
            )
        elif risk_level == "MEDIUM":
            recommendation = "Routine verification recommended during quarterly administrative review cycle."
            
        explanation_json = {
            "summary": f"{risk_level} analytical risk signal ({overall_risk}/100) identified." if risk_level in ("CRITICAL", "HIGH") else "Normal developmental operational profile.",
            "why_flagged": why_flagged,
            "contributors": [
                {"name": "Cost Anomaly", "score": c_score, "weight": round(norm_w_cost * 100), "detail": f"Peer size: {cost_eval['peer_group_size']}, Robust Z: {cost_eval.get('robust_z_score', 0)}"},
                {"name": "Duplicate Similarity", "score": d_score, "weight": round(norm_w_dup * 100), "detail": f"Matches: {dup_eval.get('matched_count', 0)}"},
                {"name": "Progress Gap", "score": p_score, "weight": round(norm_w_prog * 100), "detail": f"Rules triggered: {prog_eval['rules_triggered_count']}"},
                {"name": "Geographic Concentration", "score": g_score, "weight": round(norm_w_geo * 100), "detail": f"Locality: {geo_eval['locality']}"}
            ],
            "signals": signals_triggered,
            "investigation_priority": investigation_priority,
            "priority_score": priority_score,
            "recommendation": recommendation,
            "confidence": confidence_score,
            "evidence_coverage": evidence_coverage_score,
            "model_version": MODEL_VERSION,
            "disclaimer": "This is an objective analytical decision-support metric; it does not establish administrative or legal wrongdoing."
        }
        
        return {
            "work_code": code,
            "overall_risk_score": overall_risk,
            "risk_level": risk_level,
            "confidence": confidence_score,
            "evidence_coverage": evidence_coverage_score,
            "cost_anomaly_score": c_score,
            "duplicate_score": d_score,
            "progress_gap_score": p_score,
            "geographic_score": g_score,
            "investigation_priority": investigation_priority,
            "priority_score": priority_score,
            "cost_zscore": cost_eval.get("robust_z_score", 0.0),
            "cost_mad_score": cost_eval.get("mad", 0.0),
            "comparison_group_size": cost_eval.get("peer_group_size", 0),
            "explanation_json": explanation_json,
            "recommendation": recommendation,
            "model_version": MODEL_VERSION,
            "calculated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
