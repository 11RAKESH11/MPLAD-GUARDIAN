"""
MPLAD GUARDIAN — AI & Analytics Intelligence Microservice (Phase 5)

FastAPI service exposing explainable AI anomaly detection and risk scoring endpoints.

Import compatibility:
  - When running as a package (uvicorn ai_service.main:app): uses relative imports
  - When running standalone (uvicorn main:app): uses absolute imports
"""

import sys
import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import datetime

# Add the directory containing this file to sys.path to support both
# standalone and package-based execution
_this_dir = os.path.dirname(os.path.abspath(__file__))
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)

# Import engines using absolute imports (works whether run as package or standalone)
from risk_engine import RiskEngine, MODEL_VERSION, ALGORITHM_VERSION, FEATURE_VERSION
from cost_anomaly import CostAnomalyEngine
from duplicate_engine import DuplicateEngine
from progress_rules import ProgressRuleEngine
from geo_intelligence import GeographicIntelligenceEngine
from features import extract_project_features

app = FastAPI(
    title="MPLAD GUARDIAN AI & Risk Intelligence Engine",
    version="2.0.0",
    description="Explainable Anomaly Detection, Statistical Peer Benchmarking, and Risk Prioritization Service"
)

# Global engine instances (initialized and cached in memory)
_engine = RiskEngine()

class ProjectPayload(BaseModel):
    work_code: str
    category: Optional[str] = "Normal/Others"
    state: Optional[str] = ""
    district: Optional[str] = ""
    constituency: Optional[str] = ""
    status: Optional[str] = "Proposed"
    financial_year: Optional[str] = "2024-2025"
    sanctioned_amount: Optional[float] = 0.0
    recommended_amount: Optional[float] = 0.0
    expenditure_amount: Optional[float] = 0.0
    disbursed_amount: Optional[float] = 0.0
    description: Optional[str] = ""
    work_type: Optional[str] = ""
    sanction_date: Optional[str] = None
    completion_date: Optional[str] = None
    mp_name: Optional[str] = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class BatchAnalysisPayload(BaseModel):
    projects: List[ProjectPayload]

@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": "MPLAD GUARDIAN AI Microservice",
        "model_version": MODEL_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/models", tags=["Model Registry"])
def get_model_registry():
    return {
        "active_models": [
            {
                "model_name": "guardian-risk-engine",
                "version": MODEL_VERSION,
                "type": "ENSEMBLE_DECISION_SUPPORT",
                "components": [
                    {"name": "Hierarchical Cost Anomaly", "type": "MAD / Robust Z-Score", "weight": 30},
                    {"name": "Multi-Signal Duplicate Detection", "type": "TF-IDF / N-Gram Cosine", "weight": 30},
                    {"name": "Progress Gap Rule Engine", "type": "Deterministic Rules R1-R8", "weight": 25},
                    {"name": "Geographic Concentration", "type": "Spatial Density Index", "weight": 15}
                ],
                "status": "SHADOW_MODE",
                "disclaimer": "All outputs are decision-support signals only. Human review is required before any administrative action."
            }
        ]
    }

@app.post("/analyze/project", tags=["Analysis"])
def analyze_single_project(project: ProjectPayload):
    """Full explainable multi-signal risk and anomaly analysis for an individual project."""
    try:
        p_dict = project.model_dump()
        res = _engine.evaluate_project(p_dict)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

@app.post("/detect/cost-anomalies", tags=["Anomaly Detection"])
def detect_cost_anomaly(project: ProjectPayload):
    """Evaluates project cost against hierarchical statistical peer groups."""
    try:
        p_dict = project.model_dump()
        return _engine.cost_engine.evaluate_project(p_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cost anomaly detection error: {str(e)}")

@app.post("/detect/progress-gaps", tags=["Anomaly Detection"])
def detect_progress_gaps(project: ProjectPayload):
    """Evaluates project against deterministic operational progress rules."""
    try:
        p_dict = project.model_dump()
        features = extract_project_features(p_dict)
        return _engine.prog_engine.evaluate(p_dict, features)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Progress gap detection error: {str(e)}")

@app.post("/detect/geographic-anomalies", tags=["Anomaly Detection"])
def detect_geo_anomalies(project: ProjectPayload):
    """Evaluates district and locality project concentration indices."""
    try:
        p_dict = project.model_dump()
        return _engine.geo_engine.evaluate_project(p_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Geographic anomaly detection error: {str(e)}")

@app.post("/detect/duplicates", tags=["Anomaly Detection"])
def detect_duplicates(target_project: ProjectPayload, candidate_pool: List[ProjectPayload]):
    """Evaluates multi-signal duplicate likelihood against a candidate pool."""
    try:
        target = target_project.model_dump()
        candidates = [c.model_dump() for c in candidate_pool]
        return _engine.dup_engine.evaluate_single_project(target, candidates)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Duplicate detection error: {str(e)}")

@app.post("/evaluate/shadow", tags=["Shadow Evaluation"])
def trigger_shadow_evaluation(background_tasks: BackgroundTasks):
    """Triggers background shadow evaluation run."""
    from shadow_evaluator import run_shadow_evaluation
    background_tasks.add_task(run_shadow_evaluation)
    return {
        "status": "QUEUED",
        "message": "Shadow evaluation run queued in background.",
        "model_version": MODEL_VERSION
    }
