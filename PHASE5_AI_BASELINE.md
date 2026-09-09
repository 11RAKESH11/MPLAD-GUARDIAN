# PHASE 5.0 — AI & ANALYTICS FORENSIC AUDIT BASELINE

**Audit Date:** 2026-08-28  
**System:** MPLAD GUARDIAN AI & Risk Intelligence Engine  
**Baseline Model Version:** `risk-engine-v1.0` / `risk-engine-v2.0`  
**Dataset Scale:** 96,654 Canonical Projects | 106,442 Vouchers | 764 MPs  
**Baseline Risk Distribution:** Critical: 10 | High: 260 | Medium: 6,025 | Low: 90,359  

---

## 1. Forensic Audit of Existing AI Algorithms

| Engine Component | Method / Algorithm | Inputs & Features | Thresholds & Parameters | Output / Representation | Known Weaknesses & Limitations |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Cost Anomaly Engine** | MAD (Median Absolute Deviation) + Z-score against Category & Work Type prefix | `sanctioned_amount`, `category`, `work_type[:40]` | $Z > 1.5$ or $\text{MAD} > 2.0$, min group size $n \ge 5$ | `cost_anomaly_score` ($0–100$), $Z$, MAD score, peer group count | Groups with $n < 5$ return 0 without fallback hierarchy; work type string truncation (`[:40]`) can create noisy buckets. |
| **Duplicate Detection Engine** | TF-IDF (1-2 ngrams) + Cosine Similarity with District grouping | `description` or `work_type`, `sanctioned_amount`, `constituency`, `district` | Text $\ge 0.70$, combined similarity $\ge 65\%$ | `duplicate_score` ($0–100$), peer list in `comparable_projects` table | Limited to top 40 projects per district; does not cross district boundaries for bordering constituencies. |
| **Progress Gap Engine** | Deterministic heuristic rules (utilization, aging, over-expenditure, completion without vouchers) | `utilization_pct`, `status`, `financial_year`, `sanctioned_amount`, `disbursed_amount`, `expenditure_amount` | Util $\ge 90\%$, FY 23-25 with disbursements & early status, Exp $> 1.05 \times$ Sanction | `progress_gap_score` ($0–100$), string list of triggered reasons | Heuristics do not compute temporal delay curves or statistical progress baselines. |
| **Geographic Concentration Engine** | District high-cost density ratio | `district`, `sanctioned_amount > ₹25 Lakh`, project count in district | District project count $\ge 10$ | `geographic_score` ($0–100$) | Binary threshold (₹25L) rather than continuous spatial density; district counts unadjusted by constituency size. |
| **Composite Risk Synthesis** | Linear weighted ensemble | Cost (30%), Duplicate (30%), Progress (25%), Geographic (15%) | Critical: $\ge 75$, High: $\ge 50$, Medium: $\ge 25$, Low: $< 25$ | `overall_risk_score` ($0–100$), `risk_level`, `confidence` | Fixed weights without dynamic renormalization if specific dimensions are missing in raw source data. |
| **Confidence Scoring** | Additive heuristic base score | Group size ($+10$ to $+15$), district present ($+5$), amount present ($+5$), description ($+5$) | Base 70.0, Max 98.0 | `confidence` ($0–100$) | Does not separate evidence completeness from signal agreement. |
| **Alert Generation** | Priority scoring based on risk + financial exposure + confidence | `overall_risk_score`, `sanctioned_amount`, `confidence` | Risk $\ge 50$ (Critical or High), Alert priority $\ge 60$ | `alerts` table (270 records) | Trigger rules tied directly to coarse risk tiers rather than independent signal corroboration. |

---

## 2. Feature Availability & Coverage Matrix (96,654 Projects)

| Field Name | Description | Non-Null Count | Availability (%) | Data Source Provenance |
| :--- | :--- | :--- | :--- | :--- |
| `work_code` | Unique project canonical code | 96,654 | **100.0%** | Recommended / Sanctioned CSVs |
| `house` | Lok Sabha / Rajya Sabha | 96,654 | **100.0%** | Official directory mapping |
| `mp_name` | Sponsoring Parliamentarian | 96,654 | **100.0%** | Cross-linked from master dossiers |
| `state` | State / Union Territory | 96,654 | **100.0%** | Normalized administrative lookup |
| `district` | Administrative District | 96,654 | **100.0%** | Normalized IDA parsing |
| `category` | Project Development Category | 96,654 | **100.0%** | Official category tags |
| `status` | Operational Lifecycle Status | 96,654 | **100.0%** | Unified across sanction/completion |
| `financial_year`| Scheme Financial Year | 96,654 | **100.0%** | Extracted from work code |
| `sanctioned_amount`| Approved Administrative Sanction | 96,549 | **99.89%** | Sanctioned Works CSV |
| `recommended_amount`| Initial MP Recommendation | 96,654 | **100.0%** | Recommended Works CSV |
| `expenditure_amount`| Verified Voucher Disbursements | 96,654 | **100.0%** | Aggregate voucher linkage |
| `description` | Work description text | 91,420 | **94.58%** | Recommended / Sanctioned CSVs |
| `sanction_date` | Date of administrative sanction | 89,412 | **92.51%** | Sanctioned Works CSV |
| `completion_date`| Date of physical completion | 43,495 | **44.99%** | Completed Works CSV |
| `latitude` / `longitude` | Authentic GPS coordinates | 0 | **0.0% (NULL)** | **Zero coordinates fabricated** |

---

## 3. Phase 5 Upgrade Roadmap & Strategy

1. **Strict Shadow Mode Execution:** Develop candidate risk engine (`guardian-risk-2.0.0-shadow`), evaluate against baseline v1 without modifying production tables.
2. **Hierarchical Peer Grouping:** Implement District $\to$ State $\to$ National category fallback hierarchy with small group ($n < 5$) safety.
3. **Candidate Blocking for Duplicates:** Reduce complexity from $O(N^2)$ to partitioned candidate comparison.
4. **Independent Confidence & Evidence Coverage Scores:** Disentangle risk severity from evidence quantity.
5. **Multi-Signal Corroboration:** Explicitly evaluate independent orthogonal risk signals.
6. **Zero Accusatory Language:** Standardize on neutral decision-support terminology.
