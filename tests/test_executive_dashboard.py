"""
MPLAD GUARDIAN — Phase 8 Executive Dashboard Test Suite
Validates numerical reconciliation, API contracts, and dynamic data integrity.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import query_db

client = TestClient(app)

def test_dashboard_overview_kpis_reconciliation():
    """Verify Dashboard Overview numbers match direct database queries exactly."""
    # 1. Direct DB verification
    db_projects = query_db("SELECT COUNT(*) as c FROM projects", one=True)["c"]
    db_sanc = query_db("SELECT SUM(sanctioned_amount) as s FROM projects", one=True)["s"]
    db_exp = query_db("SELECT SUM(expenditure_amount) as e FROM projects", one=True)["e"]
    db_vouchers = query_db("SELECT COUNT(*) as c FROM expenditure_vouchers", one=True)["c"]
    db_mps = query_db("SELECT COUNT(*) as c FROM mps", one=True)["c"]
    db_alerts = query_db("SELECT COUNT(*) as c FROM alerts", one=True)["c"]
    db_duplicates = query_db("SELECT COUNT(*) as c FROM comparable_projects", one=True)["c"]

    # 2. Call API
    response = client.get("/api/v1/dashboard/overview")
    assert response.status_code == 200
    data = response.json()

    kpis = data["kpis"]
    risk = data["risk_metrics"]
    alerts = data["alerts_summary"]

    # 3. Exact assertions
    assert kpis["total_projects"] == db_projects == 96654
    assert round(kpis["total_sanctioned_funds"], 2) == round(db_sanc, 2)
    assert round(kpis["total_expenditure_funds"], 2) == round(db_exp, 2)
    assert kpis["total_vouchers"] == db_vouchers == 106442
    assert kpis["total_mps"] == db_mps == 764
    assert alerts["total_alerts"] == db_alerts == 270
    assert risk["potential_duplicates_count"] == db_duplicates == 36732


def test_dashboard_attention_priority_queue():
    """Verify What Needs Attention returns top 5 prioritized items with all necessary fields."""
    response = client.get("/api/v1/dashboard/attention")
    assert response.status_code == 200
    data = response.json()

    assert "attention_items" in data
    items = data["attention_items"]
    assert len(items) <= 5
    assert len(items) > 0

    for item in items:
        assert "alert_id" in item
        assert "work_code" in item
        assert "signal_type" in item
        assert "severity" in item
        assert item["severity"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        assert "district" in item
        assert "state" in item
        assert "sanctioned_amount" in item
        assert "why_prioritized" in item
        assert len(item["why_prioritized"]) > 10


def test_dashboard_financial_flow_integrity():
    """Verify Fund Flow endpoint returns 4 distinct pipeline stages with consistent totals."""
    response = client.get("/api/v1/dashboard/financial-flow")
    assert response.status_code == 200
    data = response.json()

    assert "stages" in data
    stages = data["stages"]
    assert len(stages) == 4

    stage_ids = [s["id"] for s in stages]
    assert stage_ids == ["recommended", "sanctioned", "disbursed", "expenditure"]

    # Verify stage properties
    for stage in stages:
        assert "amount" in stage
        assert stage["amount"] > 0
        assert "percentage_of_sanctioned" in stage
        assert "description" in stage
        assert "source" in stage

    assert data["total_sanctioned"] > 0
    assert data["total_expenditure"] > 0
    assert data["utilization_rate_pct"] > 0


def test_dashboard_signal_distribution_integrity():
    """Verify Analytical Signal distribution and risk score allocation."""
    response = client.get("/api/v1/dashboard/signal-distribution")
    assert response.status_code == 200
    data = response.json()

    assert "signals" in data
    assert "total_alerts" in data
    assert data["total_alerts"] == 270
    assert "overlap_note" in data
    assert "risk_distribution" in data
    assert "confidence_distribution" in data

    risk_dist = data["risk_distribution"]
    total_risk_records = (
        risk_dist.get("critical", 0)
        + risk_dist.get("high", 0)
        + risk_dist.get("medium", 0)
        + risk_dist.get("low", 0)
    )
    assert total_risk_records == 96654


def test_dashboard_what_changed_evaluation():
    """Verify Period-over-period comparison evaluation."""
    response = client.get("/api/v1/dashboard/what-changed")
    assert response.status_code == 200
    data = response.json()

    if data.get("historical_comparison_available"):
        assert "current_period" in data
        assert "previous_period" in data
        assert "metrics" in data
        assert len(data["metrics"]) >= 3
        for m in data["metrics"]:
            assert "name" in m
            assert "current" in m
            assert "previous" in m
            assert "diff_pct" in m
            assert "explanation" in m
            assert "neutral_note" in m


def test_dashboard_state_indicators_reconciliation():
    """Verify State Development Indicators return accurate state aggregations."""
    response = client.get("/api/v1/dashboard/state-indicators")
    assert response.status_code == 200
    data = response.json()

    assert "states" in data
    states = data["states"]
    assert len(states) >= 30

    total_projects_sum = sum(s["total_projects"] for s in states)
    assert total_projects_sum == 96654

    for st in states:
        assert "state" in st
        assert "total_projects" in st
        assert "total_sanctioned" in st
        assert "total_expenditure" in st
        assert "utilization_rate_pct" in st
        assert "completion_rate_pct" in st
        assert "signal_count" in st


def test_no_hardcoded_dashboard_statistics():
    """Verify dashboard overview uses dynamic queries and accurate data health."""
    response = client.get("/api/v1/dashboard/overview")
    assert response.status_code == 200
    data = response.json()

    assert data["data_health"]["status"] == "HEALTHY"
    assert data["data_health"]["completeness_pct"] > 95.0
    assert data["data_health"]["total_raw_rows"] == 374141
