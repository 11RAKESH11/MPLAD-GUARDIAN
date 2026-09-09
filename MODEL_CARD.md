# MODEL CARD — MPLAD GUARDIAN AI & RISK INTELLIGENCE ENGINE

**Model Identifier:** `guardian-risk-2.0.0-shadow`  
**Algorithm Version:** `2.1.0`  
**Feature Version:** `2.0.0`  
**Release Date:** 2026-08-28  
**Model Type:** Multi-Signal Decision-Support Anomaly Ensemble  
**Status:** Shadow Mode Verified (Zero Production Overwrites)  

---

## 1. Model Overview & Purpose

### 1.1 Intended Use
The **MPLAD GUARDIAN AI & Risk Intelligence Engine** is an explainable decision-support and anomaly-detection system engineered specifically for parliamentary oversight analysts, audit officers, and development authorities. Its objective is to prioritize complex public works portfolios for human desk review and on-site physical inspection.

### 1.2 Core Principle & Out-of-Scope Use
> **CRITICAL:** MPLAD GUARDIAN is **NOT** an automated fraud detector or judicial determination tool.
- It identifies statistically unusual expenditure velocity, potential description redundancies, and administrative milestone contradictions.
- It **never** asserts criminal wrongdoing or intentional misconduct.
- It **never** uses political party, personal MP attributes, or religious/demographic variables as risk features.

---

## 2. Model Architecture & Signal Ensemble

$$\text{Overall Risk} = \sum_{i \in \text{Active}} w_i \cdot S_i \quad \text{where} \quad \sum w_i = 1.0$$

```
+-----------------------------------------------------------------------------------------------+
|                                COMPOSITE RISK SYNTHESIS ENGINE                                |
+-----------------------------------------------------------------------------------------------+
|                                                                                               |
|  1. Hierarchical Cost Anomaly Engine (Weight: 30%)                                            |
|     • 4-Tier Hierarchy: District+Cat+FY → State+Cat+FY → National Cat+FY → National Cat       |
|     • Statistical Metrics: Median, MAD (Median Absolute Deviation), IQR, Robust Z-Score       |
|     • Small Sample Protection: n < 5 yields score 0 with neutral explanation                  |
|                                                                                               |
|  2. Candidate-Blocked Duplicate Detection Engine (Weight: 30%)                                |
|     • Multi-Signal Scoring: Word TF-IDF (35%) + Char N-Gram (25%) + Locality (25%) + Cost (15%)|
|     • Candidate Blocking: District + Category partitions (O(N) vs O(N²) scalability)          |
|                                                                                               |
|  3. Deterministic Progress Gap Rule Engine (Weight: 25%)                                      |
|     • Rules R1–R8: Utilization (>90%), Delayed Aging (>24mo), Over-Expenditure, Temporal Order|
|     • Evidence-Based Triggering: Only activates when verified source dates & amounts exist    |
|                                                                                               |
|  4. Geographic & Locality Concentration Engine (Weight: 15%)                                  |
|     • Spatial density index normalized by district project counts and high-cost ratios        |
|     • Zero Coordinate Fabrication: Exact GPS coordinates are NULL when unverified             |
|                                                                                               |
+-----------------------------------------------------------------------------------------------+
```

---

## 3. Inputs & Outputs

### 3.1 Input Feature Space
- **Financial:** `sanctioned_amount`, `recommended_amount`, `expenditure_amount`, `disbursed_amount`, `utilization_ratio`.
- **Temporal:** `sanction_date`, `completion_date`, `financial_year`, `age_months`.
- **Categorical:** `category`, `status`, `house`, `state`, `district`, `constituency`.
- **Textual:** `work_type`, `description` (Word & Character N-Gram tokens).

### 3.2 Standard Output Contract
- `overall_risk_score` ($0–100$, Deterministic Float)
- `risk_level` (`LOW` [0–24], `MEDIUM` [25–49], `HIGH` [50–74], `CRITICAL` [75–100])
- `confidence_score` ($0–100\%$, Independent measurement of evidence completeness)
- `evidence_coverage_score` ($0–100\%$, Completeness of raw data dimensions)
- `investigation_priority` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
- `explanation_json` (Structured contributors, why flagged bullet points, actionable recommendation)

---

## 4. Ethical Safeguards & Bias Mitigations

1. **Neutral Lexicon:** Prohibits accusatory terminology ("fraud", "corrupt", "illegal"). Employs objective framing ("Statistically unusual", "High-risk signal", "Requires review").
2. **Missing Dimension Renormalization:** If specific fields (e.g. text or GPS) are absent in source CSVs, active weights dynamically renormalize across available dimensions without penalty.
3. **Audit Trail & Human-in-the-Loop:** All analytical flags serve as inputs to human triage workflows with permanent audit logging.
4. **Reproducibility:** 100% deterministic (zero stochastic hallucination).
