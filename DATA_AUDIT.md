# 📊 DATA AUDIT REPORT — MPLAD GUARDIAN
**Smart India Hackathon 2026 — Problem Statement SIH26102**  
**Audit Generated:** August 2026  
**Audited Datasets:** Lok Sabha and Rajya Sabha MPLADS Historical & Operational Records

---

## 1. Executive Summary

| Metric | Value | Notes |
| :--- | :--- | :--- |
| **Total Discovered Files** | 12 CSV files | 6 Lok Sabha + 6 Rajya Sabha |
| **Total Raw Records** | 374,141 rows | Across all 12 operational files |
| **Total Disk Size** | 112.61 MB | Pure CSV data |
| **Unique Project Lifecycles** | 96,547 works | 77,469 Lok Sabha + 19,078 Rajya Sabha |
| **All-India Coverage** | 36 States & UTs | 100% national coverage |
| **Financial Years** | FY 2023-24 to 2026-27 | 4 active fiscal cycles |
| **Total Funds Recommended** | ₹77,709.55 Cr | MP-level recommendations |
| **Total Funds Sanctioned** | ₹57,511.24 Cr | District Authority (IDA) approved |
| **Total Funds Disbursed (Completed)** | ₹47,351.68 Cr | For 43,493 completed works |
| **Total Expenditure Transactions** | ₹78,481.40 Cr | 106,444 payment disbursements to vendors |
| **MP Coverage** | 544 LS MPs + 222 RS MPs | Full parliamentary representation |

---

## 2. File Inventory & Granularity Analysis

### A. Lok Sabha Datasets (`DATA/lok sabha/`)
1. **`Works Recommended-Loksabha.csv`** (32.88 MB | 102,327 rows | 11 columns)
   - *Granularity:* Project Recommendation Level
   - *Columns:* `Sr. No.`, `Work category`, `WORK`, `State`, `IDA`, `Hon'ble Members of Parliament`, `Constituency`, `Work description`, `Recommended date`, `RECOMMENDED AMOUNT ( ₹ )`, `Sanction Date`
   - *Purpose:* Initial project proposals by Lok Sabha MPs.

2. **`Works Sanctioned-Loksabha.csv`** (27.02 MB | 77,470 rows | 12 columns)
   - *Granularity:* Project Administrative Sanction Level
   - *Columns:* `Sr. No.`, `Work category`, `Work`, `State`, `IDA`, `Hon'ble Members of Parliament`, `Constituency`, `Work description`, `Recommended date`, `Sanction Date`, `Sanction Amount ( ₹ )`, `Work Status`
   - *Purpose:* Officially approved works by Implementing District Authorities (IDA).

3. **`Works Completed-Loksabha.csv`** (10.77 MB | 33,664 rows | 11 columns)
   - *Granularity:* Project Completion Level
   - *Columns:* `Sr. No.`, `Work Category`, `Work`, `State`, `IDA`, `Work Description`, `Hon'ble Members of Parliament`, `Constituency`, `Image`, `Completion Date`, `Amount Disbursed ( ₹ )`
   - *Purpose:* Physically finished projects with completion dates and final amounts.

4. **`Expenditure on Completed and On-going Works as on Date-Loksabha.csv`** (20.59 MB | 81,695 rows | 11 columns)
   - *Granularity:* Financial Transaction / Disbursement Level
   - *Columns:* `Sr. No.`, `State`, `Work`, `Work ID`, `IDA`, `Hon'ble Members of Parliament`, `Constituency`, `Expenditure Date`, `Vendor Name`, `Payment Status`, `Fund Disbursed Amount ( ₹ )`
   - *Purpose:* Vendor-level payment vouchers and ongoing disbursements.

5. **`Allocated Limit for Honble MPs -Loksabha.csv`** (36 KB | 544 rows | 5 columns)
   - *Granularity:* MP Allocation Summary
   - *Columns:* `Sr. No.`, `State`, `Hon'ble Members of Parliaments`, `Constituency`, `Allocated AMOUNT ( ₹ )`
   - *Purpose:* MP entitlement ceiling limits (Total: ₹16,612.42 Cr).

6. **`Amount consented for Calamity-Loksabha.csv`** (1.3 KB | 13 rows | 6 columns)
   - *Granularity:* Calamity Consent Event
   - *Columns:* `Sr. No.`, `Calamity Type`, `Calamity Name`, `Hon'ble Members of Parliament`, `Date of Consent`, `Consent Amount ( ₹ )`
   - *Purpose:* Disaster relief contributions by MPs (Total: ₹8.11 Cr).

---

### B. Rajya Sabha Datasets (`DATA/rajya sabha/`)
1. **`Works Recommended-Rajyasabha.csv`** (8.86 MB | 24,526 rows | 11 columns)
   - *Columns:* `Sr. No.`, `Work category`, `WORK`, `State`, `IDA`, `Hon'ble Members of Parliament`, `Elected/Nominated`, `Work description`, `Recommended date`, `RECOMMENDED AMOUNT ( ₹ )`, `Sanction Date`
2. **`Works Sanctioned-Rajyasabha.csv`** (7.44 MB | 19,079 rows | 12 columns)
   - *Columns:* `Sr. No.`, `Work category`, `Work`, `State`, `IDA`, `Hon'ble Members of Parliament`, `Elected/Nominated`, `Work description`, `Recommended date`, `Sanction Date`, `Sanction Amount ( ₹ )`, `Work Status`
3. **`Works Completed-Rajyasabha.csv`** (3.52 MB | 9,831 rows | 11 columns)
   - *Columns:* `Sr. No.`, `Work Category`, `Work`, `State`, `IDA`, `Work Description`, `Hon'ble Members of Parliament`, `Elected/Nominated`, `Image`, `Completion Date`, `Amount Disbursed ( ₹ )`
4. **`Expenditure on Completed and On-going Works as on Date-Rajyasabha.csv`** (6.95 MB | 24,749 rows | 11 columns)
   - *Columns:* `Sr. No.`, `State`, `Work`, `Work ID`, `IDA`, `Hon'ble Members of Parliament`, `Elected/Nominated`, `Expenditure Date`, `Vendor Name`, `Payment Status`, `Fund Disbursed Amount ( ₹ )`
5. **`Allocated Limit for Honble MPs-Rajyasabha.csv`** (20 KB | 222 rows | 5 columns)
   - *Columns:* `Sr. No.`, `State`, `Hon'ble Members of Parliament`, `Elected/Nominated`, `Allocated AMOUNT ( ₹ )` (Total: ₹6,629.70 Cr)
6. **`Amount consented for Calamity-Rajyasabha.csv`** (2.5 KB | 21 rows | 6 columns)
   - *Columns:* `Sr. No.`, `Calamity Type`, `Calamity Name`, `Hon'ble Members of Parliament`, `Date of Consent`, `Consent Amount ( ₹ )` (Total: ₹20.90 Cr)

---

## 3. Relational Schema & Linkage Integrity

The dataset forms an end-to-end relational lifecycle using the canonical **Work Code / Work ID**:
- **Format:** `WS/{MP_CODE}/{FINANCIAL_YEAR}/{WORK_SEQUENCE}` (e.g. `WS/MP620/2024-2025/133166`)
- In `Works Recommended`, `Works Sanctioned`, and `Works Completed`, the work string is structured as: `[Work ID]-[Work Standard Category]` (e.g., `WS/MP620/2024-2025/133166-Construction of buildings for community cultural activities`).
- In `Expenditure`, the `Work ID` is explicitly given in its own column.

### Cross-File Linkage Verification Rates:
- **Sanctioned to Recommended Match:** **99.5% (LS)** and **98.8% (RS)**
- **Completed to Sanctioned Match:** **100.0% (LS)** and **100.0% (RS)**
- **Expenditure to Sanctioned Match:** **100.0% (LS)** and **100.0% (RS)**

This confirms that project records link cleanly across the entire execution lifecycle.

---

## 4. Geographic & Spatial Coverage

- **Geographic Granularity:**
  - `State`: Normalized across 36 States & Union Territories.
  - `District` & `IDA`: Extracted from the `IDA` column format `DISTRICT_NAME(IDA_AGENCY_NAME)` (e.g., `DHARWAD(DEPUTY COMMISSIONER DHARWAR_IDA)` -> District: `Dharwad`, Authority: `Deputy Commissioner Dharwar`).
  - `Constituency`: Lok Sabha Constituency names (e.g., `DHARWAD`, `ARARIA`, `GHAZIABAD`, `CHAMARAJANAGAR(SC)`).
  - For Rajya Sabha: MP Nodal District / State representation with `Elected MP` vs `Nominated MP` designation.
- **GPS Coordinates Audit:**
  - **Raw GPS coordinates (Lat/Long) are NOT present in the source CSVs.**
  - **Handling:** As required by the core prompt principles, **we will NEVER fabricate coordinates**. The platform uses canonical Indian State and District boundary GeoJSON and centroid mappings with clear source badges: *"District-level representation — not exact project location"*.

---

## 5. Temporal & Categorical Coverage

### Financial Years:
- **FY 2023-2024:** 2,953 projects
- **FY 2024-2025:** 17,927 projects
- **FY 2025-2026:** 57,884 projects (Peak active cycle)
- **FY 2026-2027:** 17,783 projects

### Work Categories:
- `Normal/Others` (~88%)
- `Trust and Society` (~11%)
- `Calamity Support` (<1%)

### Work Status Distribution:
- `Physical Inspection`: 42,761 works (44.3%)
- `Sanction`: 23,685 works (24.5%)
- `Vendor Identification`: 14,170 works (14.7%)
- `Work partially Completed`: 9,570 works (9.9%)
- `Work Completed`: 5,466 works (5.7%)
- `Time Estimation`: 895 works (0.9%)

---

## 6. Data Quality Issues Discovered

1. **Footer Summary Rows in Source CSVs:**
   - 1 row in `Works Sanctioned-Loksabha.csv` and 1 row in `Works Sanctioned-Rajyasabha.csv` contains raw column sums (`40,72,44,63,767.08`) shifted into the `Work Status` column.
   - *Action:* Ingestion layer filters footer totals into metadata audit rather than database records.

2. **Column Naming Variations & Formatting:**
   - Rupee symbol `( ₹ )` with non-breaking whitespace and trailing spaces.
   - `WORK` vs `Work` vs `Work ID`.
   - `RECOMMENDED AMOUNT   ( ₹ )` has variable spacing.
   - `﻿"Sr. No."` has UTF-8 BOM (`﻿`).
   - *Action:* Canonical column mapping layer handles UTF-8 BOM, case-insensitivity, and regex-based currency stripping.

3. **Date Formats:**
   - Formatted as `DD-Mon-YYYY` (e.g. `08-Jul-2024`, `05-Sep-2024`) with occasional `NaN-NaN` in MP tenure metadata.
   - *Action:* Strict date normalizer parsing ISO dates and logging unparseable dates to `ingestion_errors`.

4. **Progress & Cost Inconsistencies for AI Anomaly Detection:**
   - Multiple works have significant expenditure disbursed but remain under `Physical Inspection` or `Sanction` status.
   - Distinct cost distributions per work type (e.g., CC Roads vs Solar Street Lights vs School Rooms) providing baseline distributions for Z-score / IQR / MAD cost outlier detection.
   - Substantial text description overlap in proximate districts indicating potential duplicate proposals.

---

## 7. Ingestion & Architecture Recommendations

1. **Database Schema:** Unified `projects` table containing normalized lifecycle fields:
   - Identifiers: `work_code`, `house`, `mp_code`, `financial_year`, `work_sequence`
   - Metadata: `state`, `district`, `constituency`, `ida_name`, `mp_name`, `mp_type`
   - Classification: `category`, `work_type`, `description`
   - Lifecycle: `status`, `recommended_date`, `sanction_date`, `completion_date`
   - Financials: `recommended_amount`, `sanctioned_amount`, `disbursed_amount`, `expenditure_amount`, `utilization_pct`
   - Lineage: `source_file`, `raw_data` JSONB
2. **Normalized Child Tables:**
   - `mps`: 766 parliamentarians with total limits, utilized limits, and party/state allocations.
   - `expenditure_vouchers`: 106,444 payment vouchers with vendor names, payment dates, statuses, and amounts.
   - `risk_scores`: Multi-dimensional AI anomaly scores, contributor breakdown, confidence, and human-readable explanations.
   - `alerts`: Actionable investigative signals with severity and review workflows.
   - `data_quality_issues`: Granular registry of all ingestion notices, discrepancies, and rejected rows.
3. **AI Pipeline:**
   - Vector / TF-IDF text similarity for duplicate detection within same district/constituency.
   - Z-score + MAD robust statistical anomaly engine grouped by `(category, work_type, state)`.
   - Deterministic rule engine for progress gaps and financial flow inconsistencies.
   - Adaptive weighted risk score with analysis coverage metric.
