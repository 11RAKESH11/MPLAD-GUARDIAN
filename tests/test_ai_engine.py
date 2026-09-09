"""
MPLAD GUARDIAN — AI Engine Unit & Integration Test Suite (Phase 5)
"""

import pytest
from importlib import import_module
from fastapi.testclient import TestClient

features_mod = import_module("ai-service.features")
cost_mod = import_module("ai-service.cost_anomaly")
dup_mod = import_module("ai-service.duplicate_engine")
prog_mod = import_module("ai-service.progress_rules")
geo_mod = import_module("ai-service.geo_intelligence")
risk_mod = import_module("ai-service.risk_engine")
main_mod = import_module("ai-service.main")

app = main_mod.app
client = TestClient(app)

def test_feature_extraction_completeness():
    proj = {
        "work_code": "KA-BLR-001",
        "category": "Education",
        "state": "Karnataka",
        "district": "Bengaluru Urban",
        "sanctioned_amount": 1000000.0,
        "expenditure_amount": 800000.0,
        "sanction_date": "2024-01-01",
        "status": "In Progress"
    }
    feats = features_mod.extract_project_features(proj)
    assert feats["utilization_pct"] == 80.0
    assert feats["has_sanctioned"] is True
    assert feats["has_district"] is True
    assert feats["evidence_coverage_pct"] >= 50.0

def test_cost_anomaly_hierarchy_fallback():
    engine = cost_mod.CostAnomalyEngine()
    # Fit with national category data only
    sample_data = [
        {"sanctioned_amount": 500000.0 + i*10000, "category": "Sanitation", "state": "Goa", "district": "North Goa", "financial_year": "2023-2024"}
        for i in range(10)
    ]
    engine.fit(sample_data)
    
    # Evaluate project from another district -> falls back to National Category
    p = {"sanctioned_amount": 550000.0, "category": "Sanitation", "state": "Kerala", "district": "Wayanad", "financial_year": "2023-2024"}
    res = engine.evaluate_project(p)
    assert res["peer_tier"] in ("National Category + FY", "National Category")
    assert res["peer_group_size"] >= 5

def test_progress_rules_r6_temporal_anomaly():
    engine = prog_mod.ProgressRuleEngine()
    p = {
        "work_code": "TIME-ERR-01",
        "status": "Work Completed",
        "sanctioned_amount": 500000.0,
        "sanction_date": "2025-06-01",
        "completion_date": "2024-01-01" # Completion BEFORE Sanction!
    }
    feats = features_mod.extract_project_features(p)
    res = engine.evaluate(p, feats)
    assert res["score"] >= 50.0
    assert any(r["rule_id"] == "R6" for r in res["triggered_rules"])

def test_ai_microservice_health_and_models_endpoints():
    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "healthy"
    
    r_models = client.get("/models")
    assert r_models.status_code == 200
    assert "active_models" in r_models.json()

def test_ai_microservice_analyze_project_endpoint():
    payload = {
        "work_code": "API-TEST-001",
        "category": "Education",
        "state": "Karnataka",
        "district": "Bengaluru Urban",
        "sanctioned_amount": 750000.0,
        "expenditure_amount": 750000.0,
        "status": "Work Completed"
    }
    resp = client.post("/analyze/project", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_risk_score" in data
    assert "confidence" in data
    assert "explanation_json" in data
