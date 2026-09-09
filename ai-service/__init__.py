"""
MPLAD GUARDIAN — AI & Analytics Intelligence Engine Package (Phase 5)
"""
from .features import extract_project_features
from .cost_anomaly import CostAnomalyEngine
from .duplicate_engine import DuplicateEngine
from .progress_rules import ProgressRuleEngine
from .geo_intelligence import GeographicIntelligenceEngine
from .risk_engine import RiskEngine, MODEL_VERSION, ALGORITHM_VERSION, FEATURE_VERSION
from .alerts import generate_alerts_for_evaluation
