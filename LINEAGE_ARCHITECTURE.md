# LINEAGE ARCHITECTURE

**Project:** MPLAD GUARDIAN  
**Document:** End-to-End Data Provenance Architecture  
**Phase:** 7 — Evidence Room + Source Traceability  
**Updated:** 2026-08-28  

---

## 1. Overview

MPLAD GUARDIAN implements a **5-Tier Data Traceability Architecture** where every analytical signal and displayed metric is traceable to its authoritative source. This enables human oversight reviewers to follow any value from the Evidence Room screen back to the official MoSPI CSV file.

---

## 2. The 5-Tier Lineage Model

```
TIER 1: PRIMARY SOURCE CSV
  MoSPI official MPLADS datasets:
  - Works Sanctioned-Loksabha.csv
  - Works Sanctioned-Rajyasabha.csv
  - Expenditure Vouchers CSVs
        │
        ▼
TIER 2: INGESTION & NORMALIZATION
  - Batch ingestion engine processes raw CSVs
  - Numeric normalization (₹ symbols, commas)
  - Date parsing (DD/MM/YYYY → ISO)
  - Work code extraction and deduplication
  - IDA name parsing
  - Location normalization (State / District / Constituency)
        │
        ▼
TIER 3: RELATIONAL OPERATIONAL STORAGE
  - SQLite (dev) / PostgreSQL (prod) database
  - Table: projects (96,654 canonical records)
  - Table: expenditure_vouchers (106,442 linked vouchers)
  - Table: risk_scores (96,654 analytical results)
  - Table: comparable_projects (36,732 relationships)
  - Table: alerts (270 active signals)
        │
        ▼
TIER 4: ANALYTICAL INTELLIGENCE ENGINE
  - Model: guardian-risk-2.0.0
  - Hierarchical Cost Anomaly (MAD + IQR + Peer Z-Score)
  - Candidate-Blocked Duplicate Detector (text + locality + amount)
  - Deterministic Progress Rules R1–R8 (utilization + temporal)
  - Spatial Concentration Engine (district-level clustering)
  - Confidence scoring (evidence coverage)
        │
        ▼
TIER 5: DECISION INTELLIGENCE & ANALYST REVIEW
  - FastAPI REST Evidence Room endpoints
  - Investigation Workspace (human-in-the-loop triage)
  - RBAC-protected status transitions
  - Permanent immutable audit log
  - Exported oversight briefs
```

---

## 3. Field-Level Provenance

Every critical field in the Evidence Room can be traced:

| Displayed Value            | Source Table         | Source Column          | Source CSV Field           |
|---------------------------|----------------------|------------------------|---------------------------|
| Sanctioned Amount (₹)      | `projects`           | `sanctioned_amount`    | "Sanctioned Amount"        |
| Expenditure Amount (₹)     | `projects`           | `expenditure_amount`   | "Expenditure Amount"       |
| Disbursed Amount (₹)       | `projects`           | `disbursed_amount`     | "Amount Released"          |
| Risk Score                 | `risk_scores`        | `overall_risk_score`   | Computed (guardian-risk-2.0.0) |
| Cost Z-Score               | `risk_scores`        | `cost_zscore`          | Computed (MAD + IQR)       |
| Voucher Amount             | `expenditure_vouchers`| `expenditure_amount`  | "Expenditure Amount"       |
| MP Name                    | `projects`           | `mp_name`              | "MP Name"                  |
| State / District           | `projects`           | `state`, `district`    | "State", "District"        |
| Comparable Similarity      | `comparable_projects`| `similarity_score`     | Computed (text + locality) |

---

## 4. Lineage API

The lineage API (`GET /api/v1/projects/{work_code}/lineage`) returns the 5-tier chain as a structured response:

```json
{
  "work_code": "WS/MP492/2024-2025/134981",
  "tiers": [
    { "tier": 1, "name": "Decision-Intelligence Layer", "verified": true },
    { "tier": 2, "name": "API Service Layer", "verified": true },
    { "tier": 3, "name": "Relational Storage (SQLite/PostgreSQL)", "verified": true },
    { "tier": 4, "name": "Data Integration & Cross-Linkage", "verified": true },
    { "tier": 5, "name": "Primary Source CSV Records", "verified": true }
  ]
}
```

---

## 5. GPS Coordinate Policy

> [!IMPORTANT]
> **Zero GPS Fabrication Policy:** Source data contains no project-level GPS coordinates. The `geographic_score` component is calculated via district-level administrative clustering, not individual project points. No latitude/longitude values are synthesized. Evidence Room shows "District-level geographic context" with a link to the verified administrative boundary map.

---

## 6. Reproducibility

Each risk analysis output includes:
- `model_version`: `guardian-risk-2.0.0`
- `calculated_at`: ISO datetime of analysis run
- `comparison_group_size`: number of peer projects used
- `confidence`: evidence coverage percentage

These metadata fields allow any analyst to reconstruct the conditions under which the analytical signal was generated.

---

## 7. Audit Log Immutability

Every status transition and analyst note is written to `audit_logs`:
- Written immediately; never deleted
- Each row carries `user_id`, `username`, `user_role`, `action`, `previous_state`, `new_state`, `notes`, `created_at`
- No UPDATE or DELETE is permitted on audit_logs rows
- Serves as the permanent investigation paper trail
