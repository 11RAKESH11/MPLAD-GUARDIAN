# PHASE 4.5 FORENSIC BASELINE

**Audit Timestamp:** 2026-08-28T21:03:00+05:30  
**Project:** MPLAD GUARDIAN — Parliamentary Development Intelligence  
**System Profile:** Production Infrastructure Upgrade (Phase 4.5)  

---

## 1. Executive Summary & Forensic Snapshot

Prior to performing any PostgreSQL + PostGIS schema migrations or Redis cache integrations, a forensic read-only baseline of the active SQLite production database (`mplad.db`) was captured.

| Property | Value |
| :--- | :--- |
| **Database Engine** | SQLite 3.38.4 |
| **Journal Mode** | WAL (Write-Ahead Logging) |
| **Database File** | `mplad.db` |
| **Database File Size** | 473,538,560 bytes (451.60 MB) |
| **Total Verified Tables** | 13 |
| **Total Verified Indexes** | 44 |
| **Raw Ingested Records (Verified Phase 2)** | 374,141 |
| **Canonical Projects (Verified Phase 2.5)** | 96,654 |
| **Total Financial Expenditure Tracked** | ₹39,240,698,923.14 (₹39,240.70 Cr) |

---

## 2. Table-by-Table Forensic Row Counts

The exact verified counts below serve as the authoritative baseline for all data migration reconciliation tests.

| Table Name | Verified Row Count | Column Count | Primary Role |
| :--- | :--- | :--- | :--- |
| `projects` | **96,654** | 28 | Canonical deduplicated project records |
| `risk_scores` | **96,654** | 20 | Deterministic multi-dimensional risk scores |
| `expenditure_vouchers` | **106,442** | 11 | Transactional payment vouchers |
| `mps` | **764** | 14 | Parliamentarian intelligence dossiers |
| `comparable_projects` | **36,732** | 7 | Deterministic peer similarity relationships |
| `alerts` | **270** | 18 | Rule-generated anomaly signals & triage states |
| `data_sources` | **12** | 8 | Official raw CSV file source registry |
| `ingestion_runs` | **2** | 8 | Complete ETL execution run logs |
| `location_mappings` | **9** | 5 | State & District boundary crosswalk mappings |
| `users` | **3** | 8 | Hardened Argon2id RBAC accounts (Admin, Analyst, Viewer) |
| `audit_logs` | **94** | 10 | Immutable system audit log records |
| `data_quality_issues` | **0** | 8 | Data quality exception registry |
| `background_jobs` | **0** | 7 | Asynchronous job state tracker (Phase 4 baseline) |

---

## 3. Financial Aggregate Baseline

Exact mathematical aggregates across all records:

- **Total Sanctioned Amount (`projects.sanctioned_amount`):** ₹57,511,237,457.95
- **Total Recommended Amount (`projects.recommended_amount`):** ₹57,237,690,425.95
- **Total Project Expenditure (`projects.expenditure_amount`):** ₹39,240,698,923.14
- **Total Disbursed Amount (`projects.disbursed_amount`):** ₹23,675,840,886.61
- **Total Voucher Disbursed Amount (`expenditure_vouchers.disbursed_amount`):** ₹39,240,698,923.14

*Note: Project Expenditure and Voucher Disbursed totals match to exact 2 decimal places.*

---

## 4. Current API Route Inventory (`/api/v1`)

The FastAPI backend currently exposes the following standardized endpoints:

1. **Authentication & Access Control (`/api/v1/auth`)**:
   - `POST /api/v1/auth/login` (Argon2id + JWT + Rate Limiting)
   - `POST /api/v1/auth/change-password`
   - `GET /api/v1/auth/me`
   - `GET /api/v1/auth/demo-accounts`
2. **Dashboard Overview & Insights (`/api/v1/dashboard`)**:
   - `GET /api/v1/dashboard/overview` (Cached)
   - `GET /api/v1/dashboard/insights`
   - `GET /api/v1/dashboard/trends`
3. **Projects Intelligence (`/api/v1/projects`)**:
   - `GET /api/v1/projects` (Paginated `{ data, meta }`, Filtered)
   - `GET /api/v1/projects/{work_code}`
   - `GET /api/v1/projects/{work_code}/relationships`
   - `GET /api/v1/projects/{work_code}/lineage`
4. **Parliamentarian Intelligence Dossiers (`/api/v1/mps`)**:
   - `GET /api/v1/mps` (Paginated `{ data, meta }`)
   - `GET /api/v1/mps/{mp_id}`
5. **Alert Management Center (`/api/v1/alerts`)**:
   - `GET /api/v1/alerts` (Paginated `{ data, meta }`)
   - `GET /api/v1/alerts/{alert_id}`
   - `GET /api/v1/alerts/{alert_id}/evidence`
   - `POST /api/v1/alerts/{alert_id}/status` (RBAC Protected: ADMIN, ANALYST)
6. **AI Risk & Anomaly Intelligence (`/api/v1/risks`)**:
   - `GET /api/v1/risks/summary`
   - `GET /api/v1/risks/map`
   - `GET /api/v1/risks/map/districts`
   - `POST /api/v1/risks/analyze`
7. **Analytics & Map (`/api/v1/analytics`)**:
   - `GET /api/v1/analytics/map`
   - `GET /api/v1/analytics/map/state/{state}`
8. **State Governance (`/api/v1/states`)**:
   - `GET /api/v1/states`
   - `GET /api/v1/states/{state_name}`
9. **Data Quality Registry (`/api/v1/data-quality`)**:
   - `GET /api/v1/data-quality/summary`
10. **Audit Logs (`/api/v1/audit-logs`)**:
    - `GET /api/v1/audit-logs` (RBAC Protected: ADMIN)
11. **Background Jobs (`/api/v1/jobs`)**:
    - `POST /api/v1/jobs/analyze/batch`
    - `GET /api/v1/jobs/{job_id}`
12. **Health & Readiness (`/api/v1/health`, `/api/v1/ready`)**:
    - `GET /api/v1/health` (Liveness)
    - `GET /api/v1/ready` (Readiness / DB Probe)

---

## 5. Current Infrastructure State

- **Database:** SQLite embedded file with WAL mode.
- **Cache:** In-process Python TTL dictionary (`backend/app/cache.py`).
- **Job Execution:** FastAPI `BackgroundTasks` writing to SQLite `background_jobs`.
- **Target Upgrade:** PostgreSQL 15+ (PostGIS enabled), Redis 7 (TTL caching + graceful fallback), Redis Queue (RQ) durable worker, multi-container Docker Compose with isolated internal networking.

This baseline is verified and locked for Phase 4.5.
