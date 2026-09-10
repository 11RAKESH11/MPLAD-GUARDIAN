# MPLAD GUARDIAN — System Architecture & Design Specification

**SIH 2026 | Problem Statement SIH26102**  
**Autonomous Public Expenditure Integrity & AI-Powered Anomaly Monitoring**

---

## 1. Executive Summary

MPLAD GUARDIAN is an autonomous, scalable public expenditure integrity and risk analysis platform engineered for the Member of Parliament Local Area Development Scheme (MPLADS). The platform reconciles and analyzes ~96,654 real public infrastructure projects, 106,442 expenditure vouchers, and 764 MP allocations across India's states and Union Territories.

The system provides:
- **Decision-Support Anomaly Detection**: Unbiased, multi-dimensional risk scores (0–100) with explainable evidence decompositions.
- **Durable Geospatial Intelligence**: National, state, and district-level aggregations and GIS polygon boundaries without coordinate fabrication.
- **Evidence Workspace**: Complete 5-tier audit trails from MP recommendations through administrative sanctions, voucher disbursements, and spatial verification.
- **Enterprise Security**: Argon2id password hashing, stateless HMAC-SHA256 JWT authentication, strict role-based access control (RBAC), and SQL injection parameterized query defense.

---

## 2. High-Level Architecture Topology

```
                         REAL MPLADS DATA
                                |
                                v
                      SQLite Source Database
                            (mplad.db)
                                |
                                v
               Robust Migration Engine (ETL)
             scripts/migrate_sqlite_to_postgres.py
                                |
                                v
                 PostgreSQL 15+ with PostGIS
                      (Target Database)
                                |
             +------------------+------------------+
             |                                     |
             v                                     v
       FastAPI Backend                        AI Service
         (Port 8000)                         (Port 8001)
             |                                     |
             +------------------+------------------+
                                |
                           Redis 7 Queue
                            (Port 6379)
                                |
                            RQ Worker
                      (Background Job Daemon)
                                |
                                v
                          RESTful APIs
                                |
                                v
                         React 18 Frontend
                       (Vite + TailwindCSS)
                                |
                                v
                          Nginx Gateway
                           (Port 80/443)
```

---

## 3. Core Subsystems

### 3.1 Data Ingestion & Storage Layer
- **Source Database**: `mplad.db` (~473 MB SQLite database containing 13 canonical tables).
- **Production Database**: PostgreSQL 15 with the PostGIS 3.4 extension.
- **Abstraction Layer**: `backend/app/database.py` with `psycopg2.pool.ThreadedConnectionPool` (pool min=2, max=10) and automatic `?` to `%s` query placeholder translation.
- **Dual-Mode Operation**: Enforces PostgreSQL in production mode (`ENVIRONMENT=production` fails clearly if `DATABASE_URL` is missing or invalid) while supporting SQLite fallback in local development.

### 3.2 FastAPI Backend Core (`backend/app/`)
- **FastAPI 0.111+**: High-throughput REST API with automatic OpenAPI specification (`/docs` conditionally enabled via `ENABLE_DOCS=true`).
- **Authentication & Security**: Argon2id password hashing via `argon2-cffi`, automatic legacy SHA-256 hash upgrade upon authentication, JWT tokens with 12-hour expiration, and IP rate limiting on login attempts (max 5 per minute per IP).
- **Role-Based Access Control**:
  - `PUBLIC`: Read-only access to national overview and high-level GIS aggregations.
  - `AUDITOR`: Access to detailed project ledgers, voucher lineages, and risk scoring metrics.
  - `OFFICIAL`: Administrative capabilities including status transitions on flagged alerts and background analysis triggering.
- **Routers**:
  - `/api/v1/auth`: Authentication, token issuance, demo accounts.
  - `/api/v1/dashboard`: Executive KPI totals, financial flow pipeline, attention items.
  - `/api/v1/projects`: Filtered pagination across 96,654 works, full-text search, relational details.
  - `/api/v1/map`: National and state GIS intelligence, district aggregates.
  - `/api/v1/risks`: Multi-signal distribution, methodology metadata.
  - `/api/v1/alerts`: Operational alert inbox, resolution workflow, audit logging.
  - `/api/v1/data-quality`: Data completeness and issue logging.
  - `/api/v1/jobs`: Asynchronous batch analysis job submission and progress tracking.

### 3.3 AI & Analytics Microservice (`ai-service/`)
- **Autonomous Decision Support**: Purely analytical, objective risk prioritization without accusations of legal wrongdoing.
- **Dimension Engines**:
  1. `CostAnomalyEngine`: Robust Z-scores and Median Absolute Deviation (MAD) against hierarchical peer groups (District + Category -> State + Category -> National Category).
  2. `DuplicateEngine`: Rapid n-gram character and token overlap similarity for co-located projects in identical constituencies.
  3. `ProgressRuleEngine`: 10 deterministic lifecycle heuristics (e.g., completion prior to sanction, excessive fund disbursement with zero physical progress).
  4. `GeographicIntelligenceEngine`: Geographic density clustering and outlier detection.
- **Composite Risk Synthesis**: Dynamic weight renormalization when source records lack certain dimensions, producing deterministic 0–100 risk scores with independent confidence ratings.

### 3.4 Queue & Background Worker (`worker/`)
- **Redis Queue (RQ)**: Lightweight, durable background task execution with up to 3 retries and exponential backoff.
- **In-Process Fallback**: Executes jobs asynchronously via thread pools if Redis is unreachable in constrained environments.
- **Progress Tracking**: Real-time progress updates stored in `background_jobs` table.

### 3.5 React 18 Frontend (`frontend/`)
- **Modern Architecture**: Vite 5, React 18, TypeScript, TailwindCSS, Lucide React, and Leaflet.
- **Key Modules**:
  - Interactive Executive Dashboard (KPI metrics, financial flow stages, priority attention queue).
  - Project Intelligence Explorer (search, filter, sort, and pagination across 96,654 works).
  - Geospatial India GIS Map (state-level choropleth, district polygon drill-down).
  - Evidence Room & Lineage Workspace (multi-tier verification, voucher reconciliation).
  - Alert Management Center (triage, status workflow, auditor notes, audit logging).
  - System Health & Background Jobs Monitor.

---

## 4. Production Security Controls

| Security Control | Implementation Details |
|---|---|
| **Password Storage** | Argon2id (`m=65536, t=3, p=4`) via `argon2-cffi`. Legacy SHA-256 automatically upgraded. |
| **Session Integrity** | Stateless HMAC-SHA256 JWT tokens. `JWT_SECRET` must be cryptographically random (min 32 bytes). |
| **Transport Security** | Nginx SSL/TLS termination, HSTS headers, X-Frame-Options: DENY, CSP directives. |
| **SQL Injection** | Parameterized queries (`query_db(sql, params)`) exclusively. No ad-hoc string formatting in SQL. |
| **CORS Restriction** | Explicit origin allowlist loaded from `ALLOWED_ORIGINS` environment variable. |
| **Privilege Separation** | Backend and Worker containers execute under dedicated non-root `appuser:appgroup` (UID 10001). |
