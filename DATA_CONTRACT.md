# 📜 MPLADS Official Source Data Contract (MoSPI Specification)

**Specification Version:** 2.0 (Production / SIH 2026)  
**Authority:** Ministry of Statistics and Programme Implementation (MoSPI)  
**Dataset Coverage:** 12 Official Operational Datasets (Lok Sabha + Rajya Sabha)  
**Total Monitored Raw Records:** 374,141  
**Last Audited:** 24 August 2026

---

## 1. Executive Data Architecture Overview

```
                      ┌───────────────────────────────────────────────┐
                      │    12 MoSPI Operational Datasets (CSV)        │
                      │               (374,141 Rows)                  │
                      └──────────────────────┬────────────────────────┘
                                             │
                                   ┌─────────▼─────────┐
                                   │  SHA-256 Ingestion│
                                   │   & Verification  │
                                   └─────────┬─────────┘
                                             │
                                   ┌─────────▼─────────┐
                                   │  Data Cleaning &  │
                                   │   Normalization   │
                                   └─────────┬─────────┘
                                             │
                     ┌───────────────────────┼───────────────────────┐
                     │                       │                       │
             ┌───────▼───────┐       ┌───────▼───────┐       ┌───────▼───────┐
             │ Canonical     │       │  Expenditure  │       │  Parliament-  │
             │ Projects      │       │   Vouchers    │       │     arians    │
             │ (96,654 Works)│       │ (106,442 Rows)│       │  (764 MPs)    │
             └───────────────┘       └───────────────┘       └───────────────┘
```

---

## 2. Dataset Specific Data Contracts (12 Datasets)

### 2.1. Lok Sabha: Allocated Limit for Hon'ble MPs
- **File Name:** `lok sabha/Allocated Limit for Honble MPs -Loksabha.csv`
- **Primary Key:** `Constituency` + `Hon'ble Members of Parliaments`
- **Total Records:** 544 rows
- **Schema Specification:**
  | Column Name | Data Type | Required | Nullable | Field Category | Description |
  | :--- | :--- | :---: | :---: | :--- | :--- |
  | `Sr. No.` | INTEGER | Yes | No | Identifier | Sequential source counter |
  | `State` | TEXT | Yes | No | Geographic | State / UT jurisdiction |
  | `Hon'ble Members of Parliaments` | TEXT | Yes | No | Entity | Full official name of Parliamentarian |
  | `Constituency` | TEXT | Yes | No | Geographic | Lok Sabha parliamentary constituency |
  | `Allocated AMOUNT ( ₹ )` | NUMERIC | Yes | No | Financial | Total MPLADS entitlement limit (INR) |

---

### 2.2. Lok Sabha: Amount Consented for Calamity
- **File Name:** `lok sabha/Amount consented for Calamity-Loksabha.csv`
- **Primary Key:** `Sr. No.` + `Hon'ble Members of Parliament` + `Date of Consent`
- **Total Records:** 13 rows
- **Schema Specification:**
  | Column Name | Data Type | Required | Nullable | Field Category | Description |
  | :--- | :--- | :---: | :---: | :--- | :--- |
  | `Sr. No.` | INTEGER | Yes | No | Identifier | Sequential counter |
  | `Calamity Type` | TEXT | Yes | No | Categorical | Calamity tier (e.g., National Calamity) |
  | `Calamity Name` | TEXT | Yes | No | Descriptive | Disaster title (e.g., Flood 2025 in Punjab) |
  | `Hon'ble Members of Parliament` | TEXT | Yes | No | Entity | Parliamentarian consenting fund transfer |
  | `Date of Consent` | DATE (ISO) | Yes | No | Temporal | Date consent form registered |
  | `Consent Amount ( ₹ )` | NUMERIC | Yes | No | Financial | Fund amount contributed from entitlement (INR) |

---

### 2.3. Lok Sabha: Expenditure on Completed and On-going Works
- **File Name:** `lok sabha/Expenditure on Completed and On-going Works as on Date-Loksabha.csv`
- **Primary Key:** Composite (`Work ID`, `Expenditure Date`, `Vendor Name`, `Fund Disbursed Amount ( ₹ )`)
- **Total Records:** 81,695 rows
- **Schema Specification:**
  | Column Name | Data Type | Required | Nullable | Field Category | Description |
  | :--- | :--- | :---: | :---: | :--- | :--- |
  | `Sr. No.` | INTEGER | Yes | No | Identifier | Sequential counter |
  | `State` | TEXT | Yes | No | Geographic | State / UT jurisdiction |
  | `Work` | TEXT | Yes | No | Descriptive | Categorical description of work activity |
  | `Work ID` | TEXT | Yes | No | Identifier | Canonical Work Code (`WS/<MP>/<FY>/<SEQ>`) |
  | `IDA` | TEXT | Yes | No | Administrative | Implementing District Authority + Agency |
  | `Hon'ble Members of Parliament` | TEXT | Yes | No | Entity | Recommending Parliamentarian |
  | `Constituency` | TEXT | Yes | No | Geographic | Parliamentary Constituency |
  | `Expenditure Date` | DATE (ISO) | Yes | Yes | Temporal | Date of voucher payment settlement |
  | `Vendor Name` | TEXT | Yes | Yes | Entity | Payee / Contractor entity |
  | `Payment Status` | TEXT | Yes | No | Status | Payment state (`Payment Done`, `In-Progress`) |
  | `Fund Disbursed Amount ( ₹ )` | NUMERIC | Yes | No | Financial | Actual amount disbursed to contractor (INR) |

---

### 2.4. Lok Sabha: Works Completed
- **File Name:** `lok sabha/Works Completed-Loksabha.csv`
- **Primary Key:** Extracted Canonical `Work ID`
- **Total Records:** 33,664 rows
- **Schema Specification:**
  | Column Name | Data Type | Required | Nullable | Field Category | Description |
  | :--- | :--- | :---: | :---: | :--- | :--- |
  | `Sr. No.` | INTEGER | Yes | No | Identifier | Sequential counter |
  | `Work Category` | TEXT | Yes | No | Categorical | Sector category (`Normal/Others`, `Trust`) |
  | `Work` | TEXT | Yes | No | Composite | Work Code prefixed to Work Title |
  | `State` | TEXT | Yes | No | Geographic | State / UT |
  | `IDA` | TEXT | Yes | No | Administrative | District Authority |
  | `Work Description` | TEXT | Yes | Yes | Descriptive | Detailed civil works project description |
  | `Hon'ble Members of Parliament` | TEXT | Yes | No | Entity | Parliamentarian |
  | `Constituency` | TEXT | Yes | No | Geographic | Constituency |
  | `Image` | TEXT | No | Yes | Media | Photographic evidence indicator (`Images`, `N/A`) |
  | `Completion Date` | DATE (ISO) | Yes | Yes | Temporal | Formal date of physical milestone completion |
  | `Amount Disbursed ( ₹ )` | NUMERIC | Yes | No | Financial | Final liquidated expenditure (INR) |

---

### 2.5. Lok Sabha: Works Recommended
- **File Name:** `lok sabha/Works Recommended-Loksabha.csv`
- **Primary Key:** Extracted Canonical `Work ID`
- **Total Records:** 102,327 rows
- **Schema Specification:**
  | Column Name | Data Type | Required | Nullable | Field Category | Description |
  | :--- | :--- | :---: | :---: | :--- | :--- |
  | `Sr. No.` | INTEGER | Yes | No | Identifier | Sequential counter |
  | `Work category` | TEXT | Yes | No | Categorical | Sector allocation category |
  | `WORK` | TEXT | Yes | No | Composite | Work Code prefixed to Work Title |
  | `State` | TEXT | Yes | No | Geographic | State / UT |
  | `IDA` | TEXT | Yes | No | Administrative | District Authority |
  | `Hon'ble Members of Parliament` | TEXT | Yes | No | Entity | Recommending MP |
  | `Constituency` | TEXT | Yes | No | Geographic | Constituency |
  | `Work description` | TEXT | Yes | Yes | Descriptive | Proposal specification |
  | `Recommended date` | DATE (ISO) | Yes | Yes | Temporal | Date of MP formal letter of recommendation |
  | `RECOMMENDED AMOUNT   ( ₹ )` | NUMERIC | Yes | No | Financial | Proposed budgetary outlay (INR) |
  | `Sanction Date` | DATE (ISO) | No | Yes | Temporal | District Collector sanction date |

---

### 2.6. Lok Sabha: Works Sanctioned
- **File Name:** `lok sabha/Works Sanctioned-Loksabha.csv`
- **Primary Key:** Extracted Canonical `Work ID`
- **Total Records:** 77,470 rows
- **Schema Specification:**
  | Column Name | Data Type | Required | Nullable | Field Category | Description |
  | :--- | :--- | :---: | :---: | :--- | :--- |
  | `Sr. No.` | INTEGER | Yes | No | Identifier | Sequential counter |
  | `Work category` | TEXT | Yes | No | Categorical | Priority / Trust sector category |
  | `Work` | TEXT | Yes | No | Composite | Work Code + Title |
  | `State` | TEXT | Yes | No | Geographic | State / UT |
  | `IDA` | TEXT | Yes | No | Administrative | District Authority |
  | `Hon'ble Members of Parliament` | TEXT | Yes | No | Entity | Parliamentarian |
  | `Constituency` | TEXT | Yes | No | Geographic | Constituency |
  | `Work description` | TEXT | Yes | Yes | Descriptive | Approved technical scope of work |
  | `Recommended date` | DATE (ISO) | Yes | Yes | Temporal | Recommendation timestamp |
  | `Sanction Date` | DATE (ISO) | Yes | Yes | Temporal | Administrative sanction timestamp |
  | `Sanction Amount ( ₹ )` | NUMERIC | Yes | No | Financial | Legally sanctioned budget envelope (INR) |
  | `Work Status` | TEXT | Yes | No | Status | Execution stage (`Sanction`, `Physical Inspection`, `Vendor Identification`) |

---

### 2.7 to 2.12. Rajya Sabha Datasets
The 6 Rajya Sabha datasets mirror the Lok Sabha structure with the following specific variations:
1. `Constituency` is replaced by `Elected/Nominated` designating whether the MP is an Elected State Representative or Nominated Parliamentarian.
2. In Rajya Sabha Works files, `Elected/Nominated` is present as a dedicated column.

---

## 3. Deterministic Canonical Identity Strategy

1. **Primary Canonical Identifier:**  
   Format: `WS/<MP_CODE>/<FINANCIAL_YEAR>/<SEQUENCE_NUMBER>`  
   *Example:* `WS/MP18207/2025-2026/258118`

2. **Parsing & Normalization Rules:**
   - Strip leading/trailing whitespaces, tabs (`\t`), and currency glyphs.
   - Regex: `r"WS/[A-Za-z0-9_-]+/\d{4}-\d{4}/\d+"`
   - If Work Title is appended after a hyphen (e.g. `WS/MP18207/...-Construction of road`), split at boundary to isolate `work_code` and `work_type`.

3. **Fallback Composite Identifier:**  
   If a record lacks a standard `WS/` code, generate a deterministic UUIDv5 using namespace `DNS`:
   $$\text{UUIDv5}(\text{NAMESPACE\_DNS}, \text{House} + \text{MP} + \text{State} + \text{Date} + \text{Amount})$$

---

## 4. Financial & Date Normalization Standards

1. **Financial Precision:**
   - Stripped: `₹`, `,`, spaces.
   - Database Column: `NUMERIC(15, 2)` (represented as `REAL`/`NUMERIC` in SQLite/PostgreSQL).
   - Inconsistencies (`Disbursed > Sanctioned`, `Sanctioned == 0 AND Disbursed > 0`) are flagged in `data_quality_issues` without altering the raw evidence.

2. **Date Standards:**
   - Ingested formats: `%d-%b-%Y`, `%d/%m/%Y`, `%Y-%m-%d`, `%d-%m-%Y`.
   - Canonical output format: ISO `YYYY-MM-DD`.
   - Nullable representations: `"NaN-NaN"`, `"NA"`, `"N/A"`, `"-"`, `""` $\longrightarrow$ `NULL`.
