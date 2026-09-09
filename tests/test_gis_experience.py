"""
MPLAD GUARDIAN — GIS & India Geospatial Intelligence Test Suite (Phase 6)
Validates boundary integrity, API aggregation, zero GPS fabrication, and SQL reconciliation.
"""

import json
import os
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import query_db

client = TestClient(app)

def test_india_state_boundary_geojson_integrity():
    """Verify authoritative India State GeoJSON file has all 36 States/UTs."""
    path = os.path.join(r"c:\SIH_PROJECT", "frontend", "src", "data", "india_states_geo.json")
    assert os.path.exists(path), f"State GeoJSON file not found at {path}"
    with open(path, "r", encoding="utf-8") as f:
        geo = json.load(f)
    assert geo["type"] == "FeatureCollection"
    features = geo["features"]
    assert len(features) >= 36, f"Expected at least 36 state features, found {len(features)}"

def test_district_geojson_files_exist_for_states():
    """Verify district boundary files exist in public data directory."""
    dist_dir = os.path.join(r"c:\SIH_PROJECT", "frontend", "public", "data", "districts")
    assert os.path.exists(dist_dir), f"District GeoJSON dir not found at {dist_dir}"
    files = [f for f in os.listdir(dist_dir) if f.endswith(".json")]
    assert len(files) >= 30, f"Expected at least 30 state district files, found {len(files)}"
    
    # Check KA district json
    ka_path = os.path.join(dist_dir, "KA.json")
    with open(ka_path, "r", encoding="utf-8") as f:
        ka_geo = json.load(f)
    assert ka_geo["type"] == "FeatureCollection"
    assert len(ka_geo["features"]) > 0

def test_map_summary_endpoint():
    """Verify /api/v1/map/summary returns accurate national KPIs."""
    res = client.get("/api/v1/map/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["totalProjects"] == 96654
    assert data["totalStates"] == 36
    assert data["dataQuality"]["gpsCoveragePct"] == 0.0
    assert data["dataQuality"]["geographicCoveragePct"] == 100.0

def test_map_states_endpoint_and_filters():
    """Verify /api/v1/map/states returns all states and supports filtering."""
    res = client.get("/api/v1/map/states")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 36
    assert len(data["states"]) == 36
    
    # Filter test: filter by status
    res_filt = client.get("/api/v1/map/states?status=Work%20Completed")
    assert res_filt.status_code == 200
    data_filt = res_filt.json()
    assert data_filt["count"] > 0
    # Every state's completedWorks should equal its projectCount when filtered by Work Completed
    for st in data_filt["states"]:
        assert st["completedWorks"] == st["projectCount"]

def test_state_intelligence_endpoint():
    """Verify /api/v1/map/state/{state_name} returns deep state breakdown."""
    res = client.get("/api/v1/map/state/Karnataka")
    assert res.status_code == 200
    data = res.json()
    assert data["state"] == "Karnataka"
    assert data["code"] == "KA"
    assert len(data["districts"]) > 0
    assert len(data["categories"]) > 0
    assert data["overview"]["totalProjects"] > 0

def test_district_intelligence_endpoint():
    """Verify /api/v1/map/district/{state}/{district} returns district intelligence drawer data."""
    res = client.get("/api/v1/map/district/Karnataka/BENGALURU%20URBAN")
    assert res.status_code == 200
    data = res.json()
    assert data["state"] == "Karnataka"
    assert data["district"] == "BENGALURU URBAN"
    assert data["totalProjects"] > 0
    assert "signalsBreakdown" in data
    assert "topProjects" in data

def test_sql_reconciliation_total_projects():
    """Verify sum of state projects matches database total canonical count."""
    res = client.get("/api/v1/map/states")
    states = res.json()["states"]
    sum_projects = sum(s["projectCount"] for s in states)
    
    db_count = query_db("SELECT COUNT(*) as cnt FROM projects WHERE state != ''", one=True)["cnt"]
    assert sum_projects == db_count, f"Map state sum ({sum_projects}) != DB count ({db_count})"
    assert sum_projects == 96654

def test_zero_project_coordinate_fabrication_policy():
    """Verify database project coordinates are not fabricated and map policy is explicitly documented."""
    # Direct DB verification: verify projects table does not have fake GPS columns
    cols = query_db("PRAGMA table_info(projects)")
    col_names = [c["name"].lower() for c in cols]
    assert "latitude" not in col_names or query_db("SELECT COUNT(*) as cnt FROM projects WHERE latitude IS NOT NULL", one=True)["cnt"] == 0
    
    # API disclaimer verification
    res = client.get("/api/v1/map/summary")
    assert res.json()["dataQuality"]["gpsCoveragePct"] == 0.0
    assert "Zero project coordinates fabricated" in res.json()["dataQuality"]["policy"]

def test_empty_state_graceful_handling():
    """Verify filters yielding 0 projects return valid empty lists with 200 OK."""
    res = client.get("/api/v1/map/states?category=NON_EXISTENT_CATEGORY_XYZ")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 0
    assert data["states"] == []

def test_non_existent_state_and_district_404():
    """Verify non-existent state or district returns clean 404."""
    res_st = client.get("/api/v1/map/state/Atlantis")
    assert res_st.status_code == 404
    
    res_dist = client.get("/api/v1/map/district/Karnataka/Narnia")
    assert res_dist.status_code == 404
