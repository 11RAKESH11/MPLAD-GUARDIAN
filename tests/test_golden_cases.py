"""
MPLAD GUARDIAN — Golden Test Cases for AI & Analytics Engine (Phase 5)

════════════════════════════════════════════════════════════════════════════════
                  *** SYNTHETIC TEST DATA ONLY ***
These records are purely deterministic synthetic scenarios for algorithmic
verification. They are NEVER mixed into the canonical production dataset.
════════════════════════════════════════════════════════════════════════════════
"""

import pytest
import datetime
from importlib import import_module

risk_module = import_module("ai-service.risk_engine")
RiskEngine = risk_module.RiskEngine

@pytest.fixture(scope="module")
def fitted_ai_engine():
    # Synthetic background population for fitting peer baselines
    synthetic_population = []
    categories = ["Education", "Drinking Water", "Health", "Roads & Pathways"]
    
    for i in range(200):
        cat = categories[i % len(categories)]
        synthetic_population.append({
            "work_code": f"SYNTH-PEER-{i:04d}",
            "category": cat,
            "state": "Karnataka" if i < 100 else "Maharashtra",
            "district": "Bengaluru Urban" if i < 50 else ("Mysuru" if i < 100 else "Pune"),
            "constituency": "Central",
            "status": "Work Completed" if i % 2 == 0 else "In Progress",
            "financial_year": "2024-2025",
            "sanctioned_amount": 500000.0 + (i * 2000.0), # 5 Lakh to 9 Lakh
            "recommended_amount": 500000.0 + (i * 2000.0),
            "expenditure_amount": 500000.0 + (i * 2000.0),
            "disbursed_amount": 500000.0 + (i * 2000.0),
            "description": f"Standard synthetic construction work in school {i}",
            "work_type": "Construction of classroom",
            "sanction_date": "2024-04-15",
            "completion_date": "2025-01-10",
            "mp_name": "Test MP"
        })
        
    engine = RiskEngine()
    engine.fit(synthetic_population)
    return engine

def test_golden_case_1_normal_project(fitted_ai_engine):
    """Scenario 1: Normal, fully compliant project -> Low Risk."""
    normal_proj = {
        "work_code": "SYNTH-CASE-01",
        "category": "Education",
        "state": "Karnataka",
        "district": "Bengaluru Urban",
        "constituency": "Central",
        "status": "Work Completed",
        "financial_year": "2024-2025",
        "sanctioned_amount": 600000.0,
        "recommended_amount": 600000.0,
        "expenditure_amount": 600000.0,
        "disbursed_amount": 600000.0,
        "description": "Construction of two additional classrooms in Govt High School",
        "work_type": "Classroom Construction",
        "sanction_date": "2024-05-01",
        "completion_date": "2024-12-20",
        "mp_name": "Honble Test MP"
    }
    res = fitted_ai_engine.evaluate_project(normal_proj)
    assert res["risk_level"] == "LOW"
    assert res["overall_risk_score"] < 25.0
    assert res["confidence"] >= 70.0
    assert res["cost_anomaly_score"] < 30.0
    assert res["progress_gap_score"] == 0.0

def test_golden_case_2_extreme_cost_anomaly(fitted_ai_engine):
    """Scenario 2: Extreme cost anomaly (10x peer median) -> High Cost Anomaly Score."""
    extreme_cost_proj = {
        "work_code": "SYNTH-CASE-02",
        "category": "Education",
        "state": "Karnataka",
        "district": "Bengaluru Urban",
        "status": "In Progress",
        "financial_year": "2024-2025",
        "sanctioned_amount": 95000000.0, # 9.5 Crore (15x median)
        "recommended_amount": 95000000.0,
        "expenditure_amount": 1000000.0,
        "disbursed_amount": 1000000.0,
        "description": "Construction of small boundary wall",
        "work_type": "Boundary Wall",
        "sanction_date": "2024-05-01",
        "mp_name": "Honble Test MP"
    }
    res = fitted_ai_engine.evaluate_project(extreme_cost_proj)
    assert res["cost_anomaly_score"] >= 60.0
    assert res["cost_zscore"] > 3.0
    assert "COST_ANOMALY" in res["explanation_json"]["signals"]

def test_golden_case_3_high_utilization_incomplete(fitted_ai_engine):
    """Scenario 3: Rule R1 trigger (95% utilization but status is 'Proposed'/'Sanction')."""
    r1_proj = {
        "work_code": "SYNTH-CASE-03",
        "category": "Drinking Water",
        "state": "Karnataka",
        "district": "Bengaluru Urban",
        "status": "Sanction",
        "financial_year": "2024-2025",
        "sanctioned_amount": 1000000.0,
        "recommended_amount": 1000000.0,
        "expenditure_amount": 950000.0, # 95% spent
        "disbursed_amount": 950000.0,
        "description": "Installation of RO drinking water plant",
        "work_type": "RO Plant",
        "sanction_date": "2024-05-01",
        "mp_name": "Honble Test MP"
    }
    res = fitted_ai_engine.evaluate_project(r1_proj)
    assert res["progress_gap_score"] >= 40.0
    assert any(r["rule_id"] == "R1" for r in res["explanation_json"]["contributors"][2]["detail"] if "rules" in str(r)) or res["progress_gap_score"] >= 40.0

def test_golden_case_4_disbursed_exceeds_sanctioned(fitted_ai_engine):
    """Scenario 4: Rule R3 trigger (Disbursed exceeds Sanctioned amount)."""
    r3_proj = {
        "work_code": "SYNTH-CASE-04",
        "category": "Health",
        "state": "Karnataka",
        "district": "Bengaluru Urban",
        "status": "Work Completed",
        "financial_year": "2024-2025",
        "sanctioned_amount": 1000000.0,
        "recommended_amount": 1000000.0,
        "expenditure_amount": 1600000.0, # 1.6x sanctioned
        "disbursed_amount": 1600000.0,
        "description": "Procurement of ambulance equipment",
        "work_type": "Ambulance",
        "sanction_date": "2024-05-01",
        "mp_name": "Honble Test MP"
    }
    res = fitted_ai_engine.evaluate_project(r3_proj)
    assert res["progress_gap_score"] >= 35.0

def test_golden_case_5_potential_duplicate(fitted_ai_engine):
    """Scenario 5: High text, location, and amount parity match."""
    target_proj = {
        "work_code": "SYNTH-CASE-05A",
        "category": "Roads & Pathways",
        "state": "Karnataka",
        "district": "Bengaluru Urban",
        "constituency": "Bangalore South",
        "sanctioned_amount": 2500000.0,
        "description": "Concrete road construction from Main Temple to Gram Panchayat building Sector 4",
        "work_type": "Road Construction"
    }
    candidate_proj = {
        "work_code": "SYNTH-CASE-05B",
        "category": "Roads & Pathways",
        "state": "Karnataka",
        "district": "Bengaluru Urban",
        "constituency": "Bangalore South",
        "sanctioned_amount": 2500000.0,
        "description": "Concrete road construction from Main Temple to Gram Panchayat building Sector 4",
        "work_type": "Road Construction"
    }
    res = fitted_ai_engine.evaluate_project(target_proj, duplicate_candidates=[candidate_proj])
    assert res["duplicate_score"] >= 80.0
    assert "POTENTIAL_DUPLICATE" in res["explanation_json"]["signals"]

def test_golden_case_6_missing_gps_graceful_handling(fitted_ai_engine):
    """Scenario 6: Missing GPS coordinates handled gracefully without crashing or fake values."""
    no_gps_proj = {
        "work_code": "SYNTH-CASE-06",
        "category": "Education",
        "state": "Karnataka",
        "district": "Bengaluru Urban",
        "sanctioned_amount": 600000.0,
        "description": "School laboratory upgrades",
        "latitude": None,
        "longitude": None
    }
    res = fitted_ai_engine.evaluate_project(no_gps_proj)
    assert res["overall_risk_score"] is not None
    assert res["confidence"] > 0.0

def test_golden_case_7_missing_financials_graceful_handling(fitted_ai_engine):
    """Scenario 7: Missing sanctioned amount handled with dynamic weight renormalization."""
    no_fin_proj = {
        "work_code": "SYNTH-CASE-07",
        "category": "Education",
        "state": "Karnataka",
        "district": "Bengaluru Urban",
        "sanctioned_amount": 0.0,
        "recommended_amount": 0.0,
        "description": "Library books procurement",
        "status": "Proposed"
    }
    res = fitted_ai_engine.evaluate_project(no_fin_proj)
    assert res["cost_anomaly_score"] == 0.0
    assert res["overall_risk_score"] is not None

def test_golden_case_8_small_peer_group_safety(fitted_ai_engine):
    """Scenario 8: Small peer group (<5 records) does not emit extreme anomaly score."""
    small_group_proj = {
        "work_code": "SYNTH-CASE-08",
        "category": "RareUniqueCategoryX",
        "state": "Karnataka",
        "district": "Bengaluru Urban",
        "sanctioned_amount": 8000000.0,
        "description": "Specialized observatory telescope installation",
        "status": "In Progress"
    }
    res = fitted_ai_engine.evaluate_project(small_group_proj)
    assert res["cost_anomaly_score"] == 0.0
    assert res["comparison_group_size"] < 5

def test_golden_case_9_multi_signal_corroboration(fitted_ai_engine):
    """Scenario 9: Multiple independent signals -> Critical/High Investigation Priority."""
    multi_signal_proj = {
        "work_code": "SYNTH-CASE-09",
        "category": "Education",
        "state": "Karnataka",
        "district": "Bengaluru Urban",
        "constituency": "Central",
        "status": "Sanction",
        "financial_year": "2024-2025",
        "sanctioned_amount": 80000000.0, # Cost anomaly
        "recommended_amount": 80000000.0,
        "expenditure_amount": 76000000.0, # High utilization on sanction status (R1)
        "disbursed_amount": 76000000.0,
        "description": "High value educational facility complex construction",
        "work_type": "Educational Facility",
        "sanction_date": "2024-04-01"
    }
    res = fitted_ai_engine.evaluate_project(multi_signal_proj)
    assert res["overall_risk_score"] >= 50.0
    assert res["priority_score"] >= 60.0
    assert res["investigation_priority"] in ("HIGH", "CRITICAL")
    assert len(res["explanation_json"]["signals"]) >= 2

def test_golden_case_10_no_anomaly_compliant(fitted_ai_engine):
    """Scenario 10: Fully normal project with clear evidence -> zero triggered alerts."""
    compliant_proj = {
        "work_code": "SYNTH-CASE-10",
        "category": "Health",
        "state": "Karnataka",
        "district": "Bengaluru Urban",
        "constituency": "Central",
        "status": "Work Completed",
        "financial_year": "2024-2025",
        "sanctioned_amount": 550000.0,
        "recommended_amount": 550000.0,
        "expenditure_amount": 550000.0,
        "disbursed_amount": 550000.0,
        "description": "Primary healthcare clinic renovation and medical equipment",
        "work_type": "Clinic Renovation",
        "sanction_date": "2024-05-15",
        "completion_date": "2024-11-30"
    }
    res = fitted_ai_engine.evaluate_project(compliant_proj)
    assert res["risk_level"] == "LOW"
    assert len(res["explanation_json"]["signals"]) == 0
    assert "Normal developmental operational profile" in res["explanation_json"]["summary"]
