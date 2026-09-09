# 📑 DATA RECONCILIATION REPORT — MPLAD GUARDIAN

**Project Problem Statement:** SIH 2026 | SIH26102  
**Verification Date:** 2026-08-28  
**System Version:** 2.0.0-sih2026  
**Schema Version:** 2.1.0  
**Database File:** `mplad.db` (SQLite 3 WAL Mode)  
**Verification Standard:** Strict Zero-Estimation Policy (All values verified from active SQLite database and raw MoSPI CSV datasets)

---

## 1. Executive Reconciliation Summary

| Metric | Verified Value | Verification Source / Notes |
| :--- | :--- | :--- |
| **Total Raw CSV Rows** | **374,141** | Direct line count across all 12 MoSPI source CSV files (excluding headers) |
| **Total Accepted Rows** | **96,654** | Unified canonical project records created in `projects` table |
| **Total Rejected Rows** | **0** | No unparseable rows were permanently discarded; unlinked/anomalous rows were mapped to canonical lifecycle models |
| **Total Source Duplicates** | **18,366** | Redundant multi-stage and cross-file duplicate submissions detected and deduplicated during ingestion |
| **Total Canonical Projects** | **96,654** | Primary entity records in `projects` table (77,573 Lok Sabha + 19,081 Rajya Sabha) |
| **Total Expenditure Vouchers** | **106,442** | Financial transaction records in `expenditure_vouchers` table |
| **Total MP Profiles** | **764** | Canonical MP records in `mps` table (542 Lok Sabha + 222 Rajya Sabha) |
| **Total Risk Scores Evaluated** | **96,654** | Risk assessment profiles in `risk_scores` table (100% project coverage) |
| **Total Comparable Project Pairs** | **36,732** | Algorithmic similarity links in `comparable_projects` table |
| **Total Generated Alerts** | **270** | High/Critical priority analytical signals in `alerts` table |
| **Total Unmapped State/UT Locations**| **0** | 100% of project records mapped to 36 valid Indian States & Union Territories |
| **Total Unmapped District Locations**| **0** | 100% of project records mapped to valid administrative districts |
| **Total Unmapped Constituencies** | **19,081** | Exclusively Rajya Sabha projects (RS MPs represent States/UTs at large without Lok Sabha constituencies) |

---

## 2. Ingestion Run & File Hash Manifest

### Ingestion Run Details
- **Run ID:** `RUN-20260824003442` / `RUN-20260824003604`
- **Source Identifier:** `ALL_12_MOSPI_DATASETS`
- **Source Hash:** `COMPOUND_DATASET_HASH`
- **Ingestion Status:** `SUCCESS`
- **Application Version:** `2.0.0-sih2026`
- **Schema Version:** `2.1.0`
- **Total Rows Read:** `374,141`
- **Rows Inserted (Projects):** `96,654`
- **Duplicates Detected:** `18,366`
- **Validation Errors:** `0`
- **Warnings Flagged:** `270`

### Source Datasets Inventory (12 CSV Files)

| House | Dataset / File Name | Raw Rows | Columns | File Size (Bytes) | SHA-256 Checksum |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Lok Sabha** | `Allocated Limit for Honble MPs -Loksabha.csv` | 544 | 5 | 36,133 | `c4888689983af565a24fc619d852f850576e0f8061a8c45ec0cf3d31ad7e48aa` |
| **Lok Sabha** | `Amount consented for Calamity-Loksabha.csv` | 13 | 6 | 1,336 | `7f75cf2105b1084ac47ba5e4c6a794a3c878edea5d66bf47fdf6c9c26762e4d6` |
| **Lok Sabha** | `Expenditure on Completed and On-going Works as on Date-Loksabha.csv` | 81,695 | 11 | 20,593,085 | `b6def5862d530b1c3009de43283b7d2ef1f78f60bd158163cb968b4a68a1d57f` |
| **Lok Sabha** | `Works Completed-Loksabha.csv` | 33,664 | 11 | 10,765,976 | `d9d70320f87c5cc1cd17699ca187933c6bf016f77f8166118edbd052f85b1ff1` |
| **Lok Sabha** | `Works Recommended-Loksabha.csv` | 102,327 | 11 | 32,879,480 | `9fb927d6d1c483430bdbad3e4305dba08aecdd71d1b7507033e6c10a55f8ec74` |
| **Lok Sabha** | `Works Sanctioned-Loksabha.csv` | 77,470 | 12 | 27,015,540 | `5e09e7a3fcc79fe4297d2c8406f991bb97548e35650e17f7b76b8eee4e864ea2` |
| **Rajya Sabha** | `Allocated Limit for Honble MPs-Rajyasabha.csv` | 222 | 5 | 20,403 | `25486cd0a3d02bba05ab04753b40c786abf5f23bd90c30f1c3420956cbf471da` |
| **Rajya Sabha** | `Amount consented for Calamity-Rajyasabha.csv` | 21 | 6 | 2,525 | `e942f2aaf7480b95d2e4c14e4d9f440a814379cba4d0260d1e76099696c7c76c` |
| **Rajya Sabha** | `Expenditure on Completed and On-going Works as on Date-Rajyasabha.csv` | 24,749 | 11 | 6,947,686 | `cad5530b7d08602460d1e6c1eecc41eb8c21be799077b5053d15b3cfa52b8c87` |
| **Rajya Sabha** | `Works Completed-Rajyasabha.csv` | 9,831 | 11 | 3,517,749 | `5b4874ca2da94a7249f2ca3801688e0c4030a7304d280d4aa721d845c76e4cff` |
| **Rajya Sabha** | `Works Recommended-Rajyasabha.csv` | 24,526 | 11 | 8,858,631 | `cb29c2e23a3d066b2ad09ef68f71e4ff26b6f247cb519252a06faddf1c68f660` |
| **Rajya Sabha** | `Works Sanctioned-Rajyasabha.csv` | 19,079 | 12 | 7,437,116 | `4cd61841d61340dd7e1fa1f959bf6551523ad217dee2ac59ce51e9018302d3c2` |
| **TOTAL** | **12 Files** | **374,141** | — | **118,075,660 Bytes** | — |

---

## 3. Financial Totals & Aggregations

All monetary figures are verified directly against SQL aggregations on `mplad.db`.

| Financial Field | Record Count | Total Value (₹) | Total Value (Crores) | Average Per Record (₹) |
| :--- | :--- | :--- | :--- | :--- |
| **Projects: Recommended Amount** | 96,654 | ₹57,237,690,425.95 | ₹5,723.77 Cr | ₹592,191.64 |
| **Projects: Sanctioned Amount** | 96,654 | ₹57,511,237,457.95 | ₹5,751.12 Cr | ₹595,021.80 |
| **Projects: Disbursed Amount** | 96,654 | ₹23,675,840,886.61 | ₹2,367.58 Cr | ₹244,954.69 |
| **Projects: Cumulative Expenditure** | 96,654 | ₹39,240,698,923.14 | ₹3,924.07 Cr | ₹405,991.46 |
| **Vouchers: Disbursed Amount** | 106,442 | ₹39,240,698,923.14 | ₹3,924.07 Cr | ₹368,658.04 |
| **MPs: Total Allocated Limit** | 764 | ₹116,210,588,210.35 | ₹11,621.06 Cr | ₹152,108,100.01 |
| **MPs: Calamity Consent Amount** | 764 | ₹145,067,400.00 | ₹14.51 Cr | ₹189,878.80 |
| **MPs: Aggregated Sanctioned Amount** | 764 | ₹57,511,237,457.95 | ₹5,751.12 Cr | ₹75,276,488.82 |
| **MPs: Aggregated Expenditure Amount** | 764 | ₹39,240,698,923.14 | ₹3,924.07 Cr | ₹51,362,171.37 |

---

## 4. Financial Year Coverage & Reconciliation

| Financial Year | Project Count | Sanctioned Amount (₹) | Expenditure Amount (₹) | Status / Notes |
| :--- | :--- | :--- | :--- | :--- |
| **2023-2024** | 2,953 | ₹1,926,508,154.79 | ₹1,828,654,549.51 | Complete fiscal cycle |
| **2024-2025** | 17,927 | ₹10,941,244,259.65 | ₹10,016,757,196.63 | Complete fiscal cycle |
| **2025-2026** | 57,884 | ₹33,890,913,556.14 | ₹23,785,432,552.00 | Peak operational fiscal cycle |
| **2026-2027** | 17,783 | ₹10,752,571,487.37 | ₹3,609,854,625.00 | Current / ongoing fiscal cycle |
| *[Empty String]* | 104 | ₹0.00 | ₹0.00 | Unsanctioned / proposed works |
| *`'M'`* | 1 | ₹0.00 | ₹0.00 | Shifted token in raw CSV |
| *`'correctionalhomes'`* | 1 | ₹0.00 | ₹0.00 | Shifted category token in raw CSV |
| *`'cremationground'`* | 1 | ₹0.00 | ₹0.00 | Shifted category token in raw CSV |
| **TOTAL** | **96,654** | **₹57,511,237,457.95** | **₹39,240,698,923.14** | **100% Reconciled** |

---

## 5. State & Union Territory Coverage (36 States/UTs)

All 36 Indian States and Union Territories are represented. Location normalization resolved historical variants via the `location_mappings` alias table.

| # | State / Union Territory | Project Count | Sanctioned Amount (₹) | Expenditure Amount (₹) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Andaman And Nicobar Islands | 13 | ₹36,232,528.00 | ₹15,498,347.00 |
| 2 | Andhra Pradesh | 3,618 | ₹2,571,377,428.00 | ₹1,263,063,991.00 |
| 3 | Arunachal Pradesh | 244 | ₹192,473,640.00 | ₹185,067,486.00 |
| 4 | Assam | 1,842 | ₹1,311,637,221.54 | ₹878,753,323.44 |
| 5 | Bihar | 5,989 | ₹4,711,481,111.00 | ₹3,797,243,174.00 |
| 6 | Chandigarh | 103 | ₹76,579,010.00 | ₹40,213,579.00 |
| 7 | Chhattisgarh | 2,456 | ₹1,341,032,127.00 | ₹974,001,906.50 |
| 8 | Dadra And Nagar Haveli And Daman And Diu | 2 | ₹1,000,000.00 | ₹0.00 |
| 9 | Delhi | 577 | ₹533,443,033.00 | ₹190,897,652.00 |
| 10 | Goa | 98 | ₹114,076,728.29 | ₹101,670,731.99 |
| 11 | Gujarat | 7,313 | ₹2,756,946,515.00 | ₹1,344,573,165.00 |
| 12 | Haryana | 1,644 | ₹883,927,298.00 | ₹439,258,753.00 |
| 13 | Himachal Pradesh | 2,293 | ₹614,591,498.04 | ₹433,403,635.04 |
| 14 | Jammu And Kashmir | 1,025 | ₹558,346,452.56 | ₹285,172,112.00 |
| 15 | Jharkhand | 4,501 | ₹1,784,941,282.00 | ₹1,341,210,623.00 |
| 16 | Karnataka | 3,654 | ₹2,505,818,756.00 | ₹1,769,653,417.00 |
| 17 | Kerala | 3,703 | ₹2,389,294,526.34 | ₹1,106,649,717.00 |
| 18 | Ladakh | 19 | ₹16,128,000.00 | ₹6,009,392.00 |
| 19 | Lakshadweep | 26 | ₹59,447,173.00 | ₹39,337,535.00 |
| 20 | Madhya Pradesh | 6,624 | ₹3,046,878,495.00 | ₹2,350,738,203.12 |
| 21 | Maharashtra | 2,912 | ₹2,992,976,765.87 | ₹1,902,451,821.00 |
| 22 | Manipur | 77 | ₹204,700,909.00 | ₹178,812,355.00 |
| 23 | Meghalaya | 464 | ₹197,620,000.00 | ₹166,890,000.00 |
| 24 | Mizoram | 171 | ₹98,944,229.00 | ₹94,866,729.00 |
| 25 | Nagaland | 128 | ₹343,589,000.00 | ₹334,256,200.00 |
| 26 | Odisha | 4,725 | ₹1,854,511,449.00 | ₹693,122,788.00 |
| 27 | Puducherry | 83 | ₹219,756,213.00 | ₹132,090,184.00 |
| 28 | Punjab | 4,389 | ₹1,886,997,981.26 | ₹1,328,602,279.67 |
| 29 | Rajasthan | 3,041 | ₹2,165,342,377.10 | ₹1,383,597,802.11 |
| 30 | Sikkim | 156 | ₹199,176,521.00 | ₹189,944,460.00 |
| 31 | Tamil Nadu | 4,940 | ₹4,315,698,696.00 | ₹3,597,552,810.00 |
| 32 | Telangana | 4,283 | ₹1,625,270,457.00 | ₹935,799,912.00 |
| 33 | Tripura | 92 | ₹190,304,100.00 | ₹119,108,040.00 |
| 34 | Uttar Pradesh | 19,489 | ₹11,371,778,799.89 | ₹8,999,404,309.89 |
| 35 | Uttarakhand | 1,106 | ₹593,939,747.00 | ₹333,838,434.00 |
| 36 | West Bengal | 4,854 | ₹3,744,977,390.06 | ₹2,287,944,055.38 |
| **TOTAL** | **36 States / UTs** | **96,654** | **₹57,511,237,457.95** | **₹39,240,698,923.14** |

---

## 6. Location Aliases Mapped

The following 9 historical raw names from source datasets were successfully standardized in `location_mappings`:

| Raw Source Name | Canonical Name | Target State | Mapping Type | Method | Confidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `orissa` | Odisha | Odisha | STATE | ALIAS_TABLE | 1.0 (100%) |
| `pondicherry` | Puducherry | Puducherry | STATE | ALIAS_TABLE | 1.0 (100%) |
| `the dadra and nagar haveli and daman and diu` | Dadra And Nagar Haveli And Daman And Diu | Dadra And Nagar Haveli And Daman And Diu | STATE | ALIAS_TABLE | 1.0 (100%) |
| `dadra and nagar haveli` | Dadra And Nagar Haveli And Daman And Diu | Dadra And Nagar Haveli And Daman And Diu | STATE | ALIAS_TABLE | 1.0 (100%) |
| `daman and diu` | Dadra And Nagar Haveli And Daman And Diu | Dadra And Nagar Haveli And Daman And Diu | STATE | ALIAS_TABLE | 1.0 (100%) |
| `andaman & nicobar islands` | Andaman And Nicobar Islands | Andaman And Nicobar Islands | STATE | ALIAS_TABLE | 1.0 (100%) |
| `jammu & kashmir` | Jammu And Kashmir | Jammu And Kashmir | STATE | ALIAS_TABLE | 1.0 (100%) |
| `delhi` | Delhi | Delhi | STATE | ALIAS_TABLE | 1.0 (100%) |
| `nct of delhi` | Delhi | Delhi | STATE | ALIAS_TABLE | 1.0 (100%) |

---

## 7. Canonical Records Breakdown by Project Lifecycle Status

| Project Status | Lok Sabha Projects | Rajya Sabha Projects | Total Projects |
| :--- | :--- | :--- | :--- |
| **Work Completed** | 33,663 | 9,830 | 43,493 |
| **Sanction** | 19,058 | 4,627 | 23,685 |
| **Vendor Identification** | 11,544 | 2,626 | 14,170 |
| **Work partially Completed** | 8,367 | 1,203 | 9,570 |
| **Physical Inspection** | 4,008 | 726 | 4,734 |
| **Time Estimation** | 826 | 69 | 895 |
| **Proposed** | 107 | 0 | 107 |
| **TOTAL** | **77,573** | **19,081** | **96,654** |

---

## 8. Data-Quality Issues Flagged & Reconciled

1. **Header Byte Order Mark (BOM):**
   - Source CSV files contain `\ufeff` UTF-8 BOM characters in initial column headers (e.g. `\ufeff"Sr. No."`). Handled cleanly via UTF-8-sig encoding parsing.
2. **Column Shifting in Source Text:**
   - 3 records in source datasets suffered delimiter unescaped comma shifts, resulting in text category fragments (`'M'`, `'correctionalhomes'`, `'cremationground'`) populating the financial year column. These records were preserved with 0 amounts rather than discarded.
3. **Empty Financial Year on Proposed Works:**
   - 104 project recommendations in Lok Sabha datasets have no assigned financial year because administrative sanction had not yet been granted.
4. **Asymmetric Lifecycle Presence:**
   - **585 projects** appeared in Sanctioned datasets without a corresponding initial entry in Recommended datasets (direct sanction uploads).
   - **107 projects** appeared in Recommended datasets without an administrative sanction (status remains `Proposed`).
5. **Over-Expenditure Outlier:**
   - Exactly **1 project** exhibits cumulative expenditure exceeding the sanctioned cap (`expenditure_amount > sanctioned_amount`). Flagged as an analytical alert in the system.
6. **Disbursement vs Cumulative Voucher Expenditure Difference:**
   - Project-level `disbursed_amount` represents milestone release tranches (₹2,367.58 Cr), whereas `expenditure_amount` and the `expenditure_vouchers` table represent cumulative vendor invoices paid (₹3,924.07 Cr across 106,442 vouchers). All 106,442 vouchers map 100% to valid canonical project work codes.

---

## 9. Records That Could Not Be Reconciled

1. **107 Unsanctioned Proposed Works:**
   - Works recommended by Lok Sabha MPs that have no matching records in `Works Sanctioned`, `Works Completed`, or `Expenditure` CSVs. Retained in canonical projects with status `Proposed` and sanctioned amount `₹0.00`.
2. **3 Delimiter-Shifted Fiscal Year Records:**
   - The 3 records with corrupted FY fields (`'M'`, `'correctionalhomes'`, `'cremationground'`) cannot be mapped to an exact fiscal year without external MoSPI metadata correction.
3. **Individual Voucher Primary Key Identifiers:**
   - NOT AVAILABLE FROM CURRENT IMPLEMENTATION (The upstream MoSPI expenditure CSV files provide `Work ID` and `Vendor Name` but do not assign unique alphanumeric voucher transaction sequence IDs; unique synthetic integer IDs `1..106442` are assigned by the database).

---

## 10. Known System Limitations

1. **Constitutional Absence of Rajya Sabha Constituencies:**
   - Rajya Sabha MPs represent entire States or Union Territories. The `constituency` column is empty/NULL for all 19,081 Rajya Sabha projects. This is constitutional domain design, not a data loss error.
2. **Absence of Point GPS Coordinates in Raw Data:**
   - NOT AVAILABLE FROM CURRENT IMPLEMENTATION (MoSPI source CSV datasets do not publish point latitude/longitude coordinates; geographic visualization is rendered using district and state polygon administrative boundaries).
3. **External Contractor Registration Data:**
   - NOT AVAILABLE FROM CURRENT IMPLEMENTATION (Vendor details in source datasets are limited to the payee string `Vendor Name` on expenditure vouchers; contractor corporate registry / CIN is not in raw MoSPI data).
4. **Historical Fiscal Coverage:**
   - Datasets cover active fiscal cycles from **FY 2023-24 through FY 2026-27**. Pre-2023 historical records are not present in the supplied source directory.

---

**Report Status:** Fully Reconciled & Formally Verified  
**All 14 Parameters:** Verified Against Active Database and Data Inventory  
**Auditor Signature:** Antigravity System Ingestion & Reconciliation Engine
