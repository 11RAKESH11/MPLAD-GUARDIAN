# EVIDENCE DATA CONTRACT

**Project:** MPLAD GUARDIAN — Evidence Room & Investigation Workspace  
**Version:** 1.0  
**Updated:** 2026-08-28  

---

## 1. Overview

This document specifies the typed API contract for all Evidence Room endpoints. Frontend components must source all displayed evidence exclusively from these API payloads — no evidence fabrication is permitted.

---

## 2. Alert Evidence Endpoint

### `GET /api/v1/alerts/{alert_id}/evidence`

Returns the full multi-signal evidence dossier for an alert.

#### Response Schema

```json
{
  "alert": {
    "id": "string",
    "work_code": "string",
    "alert_type": "COST_ANOMALY | POTENTIAL_DUPLICATE | PROGRESS_GAP | GEOGRAPHIC_CLUSTER",
    "severity": "CRITICAL | HIGH | MEDIUM | LOW",
    "title": "string",
    "trigger_description": "string",
    "evidence": "string",
    "status": "OPEN | UNDER_REVIEW | EVIDENCE_REQUESTED | VALIDATED | NOT_SUBSTANTIATED | RESOLVED | CLOSED",
    "priority_score": "number (0-100)",
    "created_at": "ISO datetime",
    "updated_at": "ISO datetime",
    "overall_risk_score": "number (0-100)",
    "risk_level": "CRITICAL | HIGH | MEDIUM | LOW",
    "confidence": "number (0-100)",
    "cost_anomaly_score": "number (0-100)",
    "duplicate_score": "number (0-100)",
    "progress_gap_score": "number (0-100)",
    "geographic_score": "number (0-100)",
    "cost_zscore": "number",
    "cost_mad_score": "number",
    "comparison_group_size": "integer",
    "explanation_json": {
      "summary": "string",
      "triggered_rules": ["R1", "R2"],
      "features": {}
    },
    "recommendation": "string",
    "model_version": "guardian-risk-2.0.0",
    "calculated_at": "ISO datetime",
    "sanctioned_amount": "number",
    "disbursed_amount": "number",
    "expenditure_amount": "number",
    "mp_name": "string",
    "category": "string",
    "state": "string",
    "district": "string",
    "constituency": "string",
    "project_status": "string",
    "raw_data": "object (original CSV fields)"
  },
  "comparables": [
    {
      "comparable_work_code": "string",
      "similarity_score": "number (0-1)",
      "similarity_type": "string",
      "reason": "string",
      "work_type": "string",
      "state": "string",
      "district": "string",
      "sanctioned_amount": "number",
      "status": "string",
      "overall_risk_score": "number",
      "risk_level": "string"
    }
  ],
  "vouchers": [
    {
      "id": "string",
      "work_code": "string",
      "voucher_number": "string",
      "expenditure_amount": "number",
      "expenditure_date": "date string",
      "vendor_name": "string",
      "description": "string"
    }
  ],
  "audit_history": [
    {
      "id": "string",
      "user_id": "string",
      "username": "string",
      "user_role": "ADMIN | ANALYST | VIEWER",
      "action": "ALERT_STATUS_UPDATE | ANALYST_NOTE_ADDED",
      "target_type": "ALERT | PROJECT",
      "target_id": "string",
      "previous_state": "string",
      "new_state": "string",
      "notes": "string",
      "created_at": "ISO datetime"
    }
  ],
  "peer_benchmark": {
    "peer_count": "integer",
    "peer_avg_cost": "number",
    "peer_min_cost": "number",
    "peer_max_cost": "number",
    "current_cost": "number",
    "z_score": "number",
    "mad_score": "number"
  },
  "recommended_checklist": [
    {
      "id": "c1 | c2 | c3 | c4",
      "step": "string",
      "done": false
    }
  ],
  "lineage": {
    "tier_1_dashboard": "string",
    "tier_2_api": "string",
    "tier_3_db_table": "string",
    "tier_4_normalized_id": "string",
    "tier_5_source_file": "string"
  },
  "disclaimer": "string"
}
```

---

## 3. Project Evidence Endpoint

### `GET /api/v1/projects/{work_code}/evidence`

Returns the same rich dossier structure but anchored to the canonical project.

#### Additional fields over alert evidence:
- `project` (instead of `alert`) — full project record including all raw and computed fields
- `alerts` — array of all alerts linked to this work_code

---

## 4. Project Lineage Endpoint

### `GET /api/v1/projects/{work_code}/lineage`

```json
{
  "work_code": "string",
  "tiers": [
    {
      "tier": 1,
      "name": "Decision-Intelligence Layer",
      "source": "MPLAD GUARDIAN National Pulse",
      "verified": true
    },
    {
      "tier": 2,
      "name": "API Service Layer",
      "source": "/api/projects/{work_code}",
      "verified": true
    },
    {
      "tier": 3,
      "name": "Relational Storage (SQLite/PostgreSQL)",
      "source": "Table: projects + risk_scores",
      "verified": true
    },
    {
      "tier": 4,
      "name": "Data Integration & Cross-Linkage",
      "source": "Canonical Work ID + N linked payment vouchers",
      "verified": true
    },
    {
      "tier": 5,
      "name": "Primary Source CSV Records",
      "source": "MoSPI Official CSVs: Works Sanctioned",
      "verified": true
    }
  ]
}
```

---

## 5. Investigation Status Update

### `POST /api/v1/alerts/{alert_id}/status`

**Authorization:** ANALYST or ADMIN only

**Request:**
```json
{
  "status": "UNDER_REVIEW | EVIDENCE_REQUESTED | VALIDATED | NOT_SUBSTANTIATED | RESOLVED | CLOSED | OPEN",
  "resolution_notes": "string (optional)",
  "assigned_to": "string (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "alert_id": "string",
  "previous_status": "string",
  "new_status": "string",
  "updated_by": "string",
  "updated_at": "ISO datetime"
}
```

---

## 6. Analyst Note

### `POST /api/v1/alerts/{alert_id}/notes`

**Authorization:** ANALYST or ADMIN only

**Request:**
```json
{ "notes": "string (min 1 character)" }
```

**Response:**
```json
{
  "success": true,
  "alert_id": "string",
  "added_by": "string",
  "created_at": "ISO datetime",
  "note": "string"
}
```

---

## 7. Investigation History

### `GET /api/v1/alerts/{alert_id}/history`

Returns chronological audit trail.

```json
{
  "target_id": "string",
  "count": "integer",
  "history": [ "...audit_log entries..." ]
}
```

---

## 8. RBAC Matrix

| Endpoint                          | VIEWER | ANALYST | ADMIN |
|-----------------------------------|--------|---------|-------|
| GET /evidence                     | ✅     | ✅      | ✅    |
| GET /lineage                      | ✅     | ✅      | ✅    |
| GET /relationships                | ✅     | ✅      | ✅    |
| GET /vouchers                     | ✅     | ✅      | ✅    |
| GET /history                      | ✅     | ✅      | ✅    |
| POST /status                      | ❌     | ✅      | ✅    |
| POST /notes                       | ❌     | ✅      | ✅    |

---

## 9. Critical Guardrails

> [!IMPORTANT]
> No frontend component may construct or fabricate evidence strings. All evidence content must come directly from the API response.

> [!WARNING]
> The disclaimer field must always be rendered. It reminds the analyst that analytical signals require human oversight and do not constitute legal determinations.

> [!NOTE]
> GPS coordinates: `evidence_coverage.geographic_pct = 0` is expected. Source data does not contain exact project GPS.
