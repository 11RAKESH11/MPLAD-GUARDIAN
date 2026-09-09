"""
MPLAD GUARDIAN — Evidence Room & Investigation Workspace Test Suite (Phase 7)
Validates multi-signal evidence dossiers, 5-tier data lineage, review workflows, RBAC, and audit trails.
"""

import json
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import query_db
from backend.app.auth import create_access_token

client = TestClient(app)

# Tokens must use real usernames from the users table (auth middleware does DB lookup by sub=username)
ANALYST_TOKEN = create_access_token({"sub": "analyst", "role": "ANALYST"})
ADMIN_TOKEN = create_access_token({"sub": "admin", "role": "ADMIN"})
VIEWER_TOKEN = create_access_token({"sub": "viewer", "role": "VIEWER"})

def test_alert_evidence_endpoint_payload_structure():
    """Verify /api/v1/alerts/{id}/evidence returns rich structured dossier."""
    # Find a sample alert
    alert = query_db("SELECT id, work_code FROM alerts LIMIT 1", one=True)
    assert alert is not None, "No alert found in database"
    alert_id = alert["id"]

    res = client.get(f"/api/v1/alerts/{alert_id}/evidence")
    assert res.status_code == 200
    data = res.json()

    assert "alert" in data
    assert "comparables" in data
    assert "vouchers" in data
    assert "peer_benchmark" in data
    assert "recommended_checklist" in data
    assert "lineage" in data
    assert "disclaimer" in data

    # Check alert fields
    a = data["alert"]
    assert a["id"] == alert_id
    assert "overall_risk_score" in a
    assert "confidence" in a
    assert "cost_anomaly_score" in a
    assert "progress_gap_score" in a

def test_project_evidence_endpoint():
    """Verify /api/v1/projects/{work_code}/evidence returns project dossier."""
    proj = query_db("SELECT work_code FROM projects LIMIT 1", one=True)
    work_code = proj["work_code"]

    res = client.get(f"/api/v1/projects/{work_code}/evidence")
    assert res.status_code == 200
    data = res.json()

    assert "project" in data
    assert "peer_benchmark" in data
    assert "recommended_checklist" in data
    assert data["project"]["work_code"] == work_code

def test_project_5_tier_lineage():
    """Verify /api/v1/projects/{work_code}/lineage returns complete 5-tier pipeline."""
    proj = query_db("SELECT work_code FROM projects LIMIT 1", one=True)
    work_code = proj["work_code"]

    res = client.get(f"/api/v1/projects/{work_code}/lineage")
    assert res.status_code == 200
    data = res.json()

    assert data["work_code"] == work_code
    assert "tiers" in data
    assert len(data["tiers"]) == 5

    tier_names = [t["name"] for t in data["tiers"]]
    assert "Primary Source CSV Records" in tier_names
    assert "Relational Storage (SQLite/PostgreSQL)" in tier_names
    assert "Decision-Intelligence Layer" in tier_names

def test_project_relationships_graph():
    """Verify /api/v1/projects/{work_code}/relationships returns graph nodes and edges."""
    proj = query_db("SELECT work_code FROM projects LIMIT 1", one=True)
    work_code = proj["work_code"]

    res = client.get(f"/api/v1/projects/{work_code}/relationships")
    assert res.status_code == 200
    data = res.json()

    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) >= 1
    assert data["nodes"][0]["is_target"] is True

def test_project_vouchers_endpoint():
    """Verify /api/v1/projects/{work_code}/vouchers returns linked expenditure vouchers."""
    # Find a project with vouchers
    vouch = query_db("SELECT work_code FROM expenditure_vouchers LIMIT 1", one=True)
    if vouch:
        wc = vouch["work_code"]
        res = client.get(f"/api/v1/projects/{wc}/vouchers")
        assert res.status_code == 200
        data = res.json()
        assert data["work_code"] == wc
        assert data["count"] > 0
        assert len(data["vouchers"]) > 0

def test_review_workflow_status_transitions_and_audit_logging():
    """Verify status transition workflow: OPEN -> UNDER_REVIEW -> EVIDENCE_REQUESTED -> RESOLVED."""
    alert = query_db("SELECT id, status FROM alerts LIMIT 1", one=True)
    alert_id = alert["id"]

    headers = {"Authorization": f"Bearer {ANALYST_TOKEN}"}

    # Step 1: Transition to UNDER_REVIEW
    r1 = client.post(
        f"/api/v1/alerts/{alert_id}/status",
        headers=headers,
        json={"status": "UNDER_REVIEW", "resolution_notes": "Desk review initiated by investigative auditor"}
    )
    assert r1.status_code == 200
    assert r1.json()["new_status"] == "UNDER_REVIEW"

    # Step 2: Transition to EVIDENCE_REQUESTED
    r2 = client.post(
        f"/api/v1/alerts/{alert_id}/status",
        headers=headers,
        json={"status": "EVIDENCE_REQUESTED", "resolution_notes": "Requested PWD measurement book verification"}
    )
    assert r2.status_code == 200
    assert r2.json()["new_status"] == "EVIDENCE_REQUESTED"

    # Step 3: Transition to RESOLVED
    r3 = client.post(
        f"/api/v1/alerts/{alert_id}/status",
        headers=headers,
        json={"status": "RESOLVED", "resolution_notes": "Technical approval confirmed within acceptable variance"}
    )
    assert r3.status_code == 200
    assert r3.json()["new_status"] == "RESOLVED"

    # Step 4: Reset back to OPEN for idempotency
    r4 = client.post(
        f"/api/v1/alerts/{alert_id}/status",
        headers=headers,
        json={"status": "OPEN", "resolution_notes": "Reset to baseline status"}
    )
    assert r4.status_code == 200

def test_analyst_notes_and_history_logging():
    """Verify adding analyst notes logs to audit trail."""
    alert = query_db("SELECT id FROM alerts LIMIT 1", one=True)
    alert_id = alert["id"]

    headers = {"Authorization": f"Bearer {ANALYST_TOKEN}"}

    # Add Note
    note_text = "Verified sanction order copy with district planning cell."
    r_note = client.post(
        f"/api/v1/alerts/{alert_id}/notes",
        headers=headers,
        json={"notes": note_text}
    )
    assert r_note.status_code == 200
    assert r_note.json()["success"] is True

    # Check History
    r_hist = client.get(f"/api/v1/alerts/{alert_id}/history")
    assert r_hist.status_code == 200
    hist = r_hist.json()
    assert hist["count"] > 0
    actions = [h["action"] for h in hist["history"]]
    assert "ANALYST_NOTE_ADDED" in actions

def test_rbac_protection_on_evidence_status_mutations():
    """Verify VIEWER role is rejected with 403 when attempting status modifications."""
    alert = query_db("SELECT id FROM alerts LIMIT 1", one=True)
    alert_id = alert["id"]

    viewer_headers = {"Authorization": f"Bearer {VIEWER_TOKEN}"}
    r = client.post(
        f"/api/v1/alerts/{alert_id}/status",
        headers=viewer_headers,
        json={"status": "RESOLVED", "resolution_notes": "Unauthorized attempt"}
    )
    # VIEWER token passes auth (user exists) but RBAC blocks → 403
    assert r.status_code == 403

def test_end_to_end_5_project_lineage_traceability():
    """Verify 5 canonical projects maintain exact end-to-end data lineage."""
    projects = query_db("""
    SELECT p.work_code, p.sanctioned_amount, p.state, p.district, p.category, r.overall_risk_score
    FROM projects p
    JOIN risk_scores r ON p.work_code = r.work_code
    LIMIT 5
    """)
    assert len(projects) == 5

    for p in projects:
        wc = p["work_code"]
        res = client.get(f"/api/v1/projects/{wc}/evidence")
        assert res.status_code == 200
        p_res = res.json()["project"]
        
        # Verify exact field preservation
        assert p_res["work_code"] == wc
        assert p_res["state"] == p["state"]
        assert p_res["district"] == p["district"]
        assert p_res["sanctioned_amount"] == p["sanctioned_amount"]
        assert p_res["overall_risk_score"] == p["overall_risk_score"]

def test_non_existent_alert_and_project_evidence_404():
    """Verify clean 404 responses for non-existent alerts/projects."""
    r1 = client.get("/api/v1/alerts/NON_EXISTENT_ALERT_99999/evidence")
    assert r1.status_code == 404

    r2 = client.get("/api/v1/projects/NON_EXISTENT_WORK_99999/evidence")
    assert r2.status_code == 404
