# 🛡️ MPLAD GUARDIAN — Parliamentary Development Intelligence Platform

> **Smart India Hackathon 2026 — Problem Statement SIH26102**  
> **AI-Powered Parliamentary Development Intelligence, Anomaly Detection & Risk Monitoring System**

---

## 📌 Executive Summary

**MPLAD GUARDIAN** is an enterprise-grade parliamentary oversight intelligence platform designed to transform raw Member of Parliament Local Area Development Scheme (MPLADS) operational data into explainable, accountable, and actionable governance intelligence.

Built on **374,141 verified primary records** across **12 official CSV datasets** spanning both **Lok Sabha and Rajya Sabha** (totaling **₹57,511+ Crore** sanctioned funds and **96,654 unique project lifecycles**), the platform operationalizes the pipeline:

$$\text{RAW DATA} \longrightarrow \text{INTELLIGENCE} \longrightarrow \text{RISK DETECTION} \longrightarrow \text{EXPLAINABILITY} \longrightarrow \text{ACTION}$$

```
+----------------------------------------------------------------------------------------------------+
|                                      MPLAD GUARDIAN ARCHITECTURE                                   |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  [ 12 Official CSV Datasets - 112 MB ]                                                             |
|   - Works Recommended (126,853 rows)                                                               |
|   - Works Sanctioned  (96,549 rows)                                                                |
|   - Works Completed   (43,495 rows)                                                                |
|   - Expenditure Vouchers (106,444 rows)                                                            |
|   - MP Limits & Calamities (800 rows)                                                              |
|                         │                                                                          |
|                         ▼                                                                          |
|  [ Ingestion & Normalization Layer ]                                                               |
|   - Canonical Column Normalizer (Handles UTF-8 BOM, Rupee currency formatting, multi-format dates)  |
|   - Cross-Lifecycle Relational Linker (WS/{MP_CODE}/{FY}/{SEQ} code mapping)                       |
|   - Ingestion Error & Data Quality Registry                                                         |
|                         │                                                                          |
|                         ▼                                                                          |
|  [ Relational Storage Engine (mplad.db) ]                                                          |
|   - projects | mps | expenditure_vouchers | risk_scores | comparable_projects | alerts | audit_logs  |
|                         │                                                                          |
|                         ▼                                                                          |
|  [ AI Risk & Anomaly Detection Service ]                                                           |
|   ┌─────────────────────────────────┬──────────────────────────────────┐                           |
|   │ 1. Cost Anomaly Engine          │ 2. Duplicate Detection Engine    │                           |
|   │    • MAD (Median Absolute Dev)  │    • TF-IDF Vectorization        │                           |
|   │    • Grouped Z-Score (Category) │    • Cosine Similarity (>=70%)   │                           |
|   │    • Statistical Outlier Scores │    • Geographic/Cost Match       │                           |
|   ├─────────────────────────────────┼──────────────────────────────────┤                           |
|   │ 3. Progress Gap Engine          │ 4. Explainability & Confidence   │                           |
|   │    • Rule 1: High util (>90%)   │    • Multi-factor Weighted Model │                           |
|   │    • Rule 2: Aging without prog │    • Natural Language Evidence   │                           |
|   │    • Rule 3/4: Over-expenditure │    • Actionable Recommendation   │                           |
|   └─────────────────────────────────┴──────────────────────────────────┘                           |
|                         │                                                                          |
|                         ▼                                                                          |
|  [ FastAPI Core REST Services ] (Swagger: http://localhost:8000/docs)                              |
|   - /api/dashboard/overview • /api/dashboard/insights • /api/projects • /api/risks/map             |
|   - /api/alerts • /api/states • /api/mps • /api/data-quality • /api/auth • /api/audit-logs          |
|                         │                                                                          |
|                         ▼                                                                          |
|  [ Premium Frontend Experience (React + TypeScript + Vite + Tailwind CSS) ]                       |
|   - Executive Hero Overview & Dynamic AI Narrative Insight Cards                                   |
|   - National Risk Command Center with Interactive State/District Drill-down                        |
|   - AI Risk Explainer ("Why was this project flagged?") with Contributor Bars                      |
|   - Project Intelligence Explorer (Fuzzy Search, Multi-Filter, CSV Export)                         |
|   - Detailed Investigation Dossier with Payment Vouchers & Raw CSV JSON Traceability               |
|   - Alert Management Center (Open → Acknowledged → Resolved Review Workflow)                       |
|   - Data Quality & Integrity Center (98.4% Health Score & Monitored Issue Registry)                |
|   - Guided 3-Minute Evaluator Investigation Tour & Ctrl+K Command Palette                          |
+----------------------------------------------------------------------------------------------------+
```

---

## 🌟 Key Differentiators

### 1. Explainable Risk Intelligence ("Why Flagged?")
Unlike black-box dashboards that output arbitrary risk scores, MPLAD GUARDIAN provides transparent, statistically grounded evidence for every analytical flag:
- **Exact Contributor Weightage:** Cost Anomaly (30%), Duplicate Similarity (30%), Progress Gap (25%), Geographic Concentration (15%).
- **Comparable Group Context:** Compares sanctioned costs against median baselines within the same category and state.
- **Natural Language Findings:** Clear bullets such as *"Sanctioned cost (₹1,50,000) is 2.8σ above the category median across 134 comparable works"*.
- **Confidence Metric:** Independent confidence score computed from sample size, data completeness, and voucher lineage.

### 2. Strict Data Integrity — Zero Fabrication
- In compliance with official hackathon principles, **coordinates, MP details, and financial figures are never synthesized**.
- Because raw GPS coordinates do not exist in the official MPLADS CSVs, the platform maps projects to canonical District & State representations with transparent source badges: *"District-level representation — not exact project GPS location"*.
- Every UI metric displays its data origin: `REAL CSV DATA`, `DERIVED ANALYTICS`, or `AI ANALYSIS`.

### 3. Complete Source Traceability
Every project record retains raw JSON snapshots of its initial recommendation, administrative sanction, completion certificate, and individual contractor payment vouchers.

### 4. Ethical AI & Decision-Support Framing
The system is strictly designed as an **objective decision-support and anomaly-detection tool**. It avoids accusatory language, framing signals as *"High-Risk Anomaly"*, *"Potential Duplicate"*, or *"Requires Review"*, reinforced with the disclaimer:
> *"This is an analytical signal and does not establish wrongdoing."*

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React 18, TypeScript, Vite | Ultra-fast, type-safe reactive user interface |
| **Styling** | Tailwind CSS, Lucide Icons, Glassmorphism | Dark theme design system (`#070B14`, `#0B1120`, `#111827`) |
| **Data Viz** | Recharts, SVG Gauge, Leaflet | Financial trajectory charts, status rings, interactive maps |
| **Backend API** | Python, FastAPI, Uvicorn | High-performance asynchronous REST API with Swagger docs |
| **AI / ML Engine** | Scikit-Learn, NumPy, SciPy, TF-IDF | MAD, Z-score cost anomaly, TF-IDF cosine duplicate detection |
| **Database** | SQLite + PostgreSQL-compatible schema | Fully indexed relational storage (`mplad.db`) |
| **Containerization** | Docker, Docker Compose, Nginx | Multi-container reproducible production deployment |

---

## 🚀 Quick Start Guide

### Option A: Running via Docker Compose (Recommended)

```bash
# 1. Clone the repository and navigate to root
cd SIH_PROJECT

# 2. Build and launch all containerized services
docker compose up --build
```
- Frontend UI: `http://localhost:5173`
- Backend API & Interactive Swagger Docs: `http://localhost:8000/docs`

---

### Option B: Running Locally

#### 1. Ingest Data & Execute AI Engine
```bash
# Execute ingestion across all 12 CSV files (generates mplad.db in ~30 seconds)
python ai-service/ingest_and_analyze.py
```

#### 2. Start Backend API
```bash
# Launch FastAPI server on port 8000
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 3. Start Frontend UI
```bash
# In a new terminal window
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 👥 Demo Evaluation Accounts (1-Click Switcher)

The login screen features instant 1-click evaluation roles:

| Role | Username | Password | Access Scope |
| :--- | :--- | :--- | :--- |
| **Executive Administrator** | `admin` | `admin123` | Full access, alert resolution, audit logs, system configuration |
| **Oversight Analyst** | `analyst` | `analyst123` | Risk investigation, alert acknowledgment, project deep-dive |
| **Public Viewer** | `viewer` | `viewer123` | Public intelligence dashboards, state analytics, MP portfolios |

---

## 🎯 3-Minute Live Evaluator Walkthrough

1. **Executive Hero Dashboard (`/dashboard`):**
   - Click **"Start Live Investigation"** in the sidebar to launch the 4-step guided evaluator tour.
   - Review live KPIs: **₹57,511 Cr Sanctioned**, **96,654 Projects**, **10 Critical Risk Signals**, **3,558 Potential Duplicates**.
   - Read dynamically generated AI Narrative Insight cards.
2. **National Risk Command Center (`/risk-map`):**
   - Explore state-level risk densities across 36 States & UTs.
   - Click a state (e.g. *Uttar Pradesh* or *Maharashtra*) to inspect regional district intelligence.
3. **Alert Management Center (`/alerts`):**
   - Triage 270 prioritized alerts categorized by severity (`CRITICAL`, `HIGH`, `MEDIUM`).
   - Click **"Triage"** on an alert to enter remarks and update status (`Open` → `Acknowledged` → `Resolved`).
4. **Project Intelligence Explorer (`/projects`):**
   - Use the fuzzy search to find specific works (e.g. `WS/MP792/2025-2026/225865`).
   - Click any project row to open the detailed dossier.
5. **Detailed Investigation Dossier (`/projects/:id`):**
   - Review the financial progress bar, **"Why Flagged?" AI explainer**, comparable projects matrix, contractor payment vouchers table, and raw CSV JSON records.
6. **Command Palette:**
   - Press **`Ctrl+K`** anywhere to search projects, jump between states, or switch views instantly.

---

## 📊 Dataset Audit Summary

| Dataset File | House | Rows | Key Role |
| :--- | :--- | :--- | :--- |
| `Works Recommended-Loksabha.csv` | Lok Sabha | 102,327 | Initial MP project recommendations & estimated budgets |
| `Works Sanctioned-Loksabha.csv` | Lok Sabha | 77,470 | District Authority approvals, status, and sanction amounts |
| `Works Completed-Loksabha.csv` | Lok Sabha | 33,664 | Physically finished works with completion disbursements |
| `Expenditure on Completed and On-going Works-Loksabha.csv` | Lok Sabha | 81,695 | Contractor/vendor payment vouchers & voucher dates |
| `Allocated Limit for Honble MPs-Loksabha.csv` | Lok Sabha | 544 | Parliamentary financial allocation ceilings |
| `Amount consented for Calamity-Loksabha.csv` | Lok Sabha | 13 | Disaster & calamity relief contributions |
| `Works Recommended-Rajyasabha.csv` | Rajya Sabha | 24,526 | Rajya Sabha MP project proposals |
| `Works Sanctioned-Rajyasabha.csv` | Rajya Sabha | 19,079 | Rajya Sabha district sanctioned works |
| `Works Completed-Rajyasabha.csv` | Rajya Sabha | 9,831 | Completed Rajya Sabha projects |
| `Expenditure on Completed and On-going Works-Rajyasabha.csv` | Rajya Sabha | 24,749 | Payment vouchers for Rajya Sabha works |
| `Allocated Limit for Honble MPs-Rajyasabha.csv` | Rajya Sabha | 222 | Rajya Sabha MP allocation limits |
| `Amount consented for Calamity-Rajyasabha.csv` | Rajya Sabha | 21 | Calamity relief consents |

**Total Ingested Scope:** 374,141 rows | 112.61 MB | 96,654 Unified Projects | 106,442 Vouchers | 764 MPs.

---

## 🗺️ Authoritative Geographic GIS Architecture & Attribution

MPLAD GUARDIAN uses an authoritative, high-fidelity GIS boundary pipeline to render geographically accurate national and district administrative boundaries:

- **State & Union Territory Boundaries:** Survey of India compliant boundary dataset covering all 36 States & Union Territories (including Ladakh, Jammu & Kashmir, Telangana, Dadra & Nagar Haveli and Daman & Diu, Andaman & Nicobar Islands, Lakshadweep, Sikkim, and the 8 Northeastern states).
- **District Boundaries:** Comprehensive 820+ district boundary polygons derived from authoritative administrative datasets (DataMeet / Survey of India Open Data).
- **Data Linkage:** Geometry is decoupled from analytics. Boundary features link dynamically to live SQLite database records via canonical `stateCode` and normalized state/district keys.
- **Cartographic Standards:** 1.2px neutral state borders, 2.5px selection outlines, dynamic data-driven choropleths, normalized signal density (preventing large state count skew), and zero artificial distortion.
- **Licensing & Attribution:**
  - Administrative boundary geometry: **DataMeet Community Maps / Survey of India Open Data Project** (Open Database License - ODbL / CC BY 4.0).
  - MPLADS operational metrics: **Official Ministry of Statistics and Programme Implementation (MoSPI) Source Records**.

---

## 🔒 Security & Observability

- **Zero-Dependency JWT Authentication:** Cryptographically verified HMAC-SHA256 tokens with role-based access control.
- **SQL Injection Immunity:** Fully parameterized SQLite/PostgreSQL queries with strict Zod/Pydantic typing.
- **Immutable Audit Logging:** Every administrative action, alert resolution, and ingestion run is permanently logged in `audit_logs`.
- **Offline Resilience:** The platform operates with 100% functionality in offline environments with local SQLite database caching.

---

## ⚖️ Responsible AI & Ethical Governance Statement

MPLAD GUARDIAN is engineered as an **explainable decision-support and anomaly-detection platform**. Its algorithms highlight statistical outliers, documentation gaps, and descriptive similarities to aid authorized government auditors and human evaluators. The system does not assert fraud or declare legal culpability. Every insight is traceable to official primary records.
