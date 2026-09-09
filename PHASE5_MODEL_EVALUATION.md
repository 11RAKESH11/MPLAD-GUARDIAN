# PHASE 5.0 MODEL EVALUATION & SHADOW COMPARISON REPORT

**Evaluation Timestamp:** 2026-08-28T16:13:36Z  
**Execution Mode:** SHADOW MODE (Zero Production Overwrites)  
**Dataset Scale:** 96,654 Canonical Projects  
**Baseline Model:** `risk-engine-v1.0` / `risk-engine-v2.0`  
**Candidate Model:** `guardian-risk-2.0.0-shadow`  

---

## 1. Risk Tier Distribution Comparison

| Risk Tier | Baseline Engine v1 | Candidate Shadow Engine v2 | Shift / Delta | Interpretation |
| :--- | :--- | :--- | :--- | :--- |
| **CRITICAL (75–100)** | **10** | **3** | -7 | Highly specific multi-signal corroboration |
| **HIGH (50–74)** | **260** | **408** | +148 | Filtered via hierarchical peer MAD baselines |
| **MEDIUM (25–49)** | **6,025** | **13,025** | +7000 | Moderate statistical deviations |
| **LOW (0–24)** | **90,359** | **83,218** | -7141 | Standard compliant operational works |
| **Total Evaluated** | **96,654** | **96,654** | **0** | **100% Coverage Verified** |

---

## 2. Statistical Score Shift Analysis

- **Mean Difference (v2 - v1):** +3.60 points
- **Median Difference:** +1.50 points
- **Standard Deviation of Difference:** 9.45 points
- **Extreme Range:** [-47.1, +59.6]
- **Determinism:** **100% VERIFIED DETERMINISTIC** (Identical input yields identical floating-point scores).

---

## 3. Candidate Model Improvements & Explainability Innovations

1. **Hierarchical Statistical Peer Groups:** Replaced brittle single-level grouping with 4-tier fallback hierarchy (District $	o$ State $	o$ Category $	o$ National), eliminating small-sample distortions ($n < 5$).
2. **Disentangled Confidence & Evidence Coverage:** Confidence ($0-100\%$) and Evidence Coverage ($0-100\%$) are now reported as distinct orthogonal metrics alongside Risk Severity.
3. **Dynamic Weight Renormalization:** Missing fields (e.g., absent rich text or GPS) dynamically reallocate weights across available dimensions without artificially dampening scores.
4. **Candidate Blocking Duplicate Detection:** Reduces comparison complexity from $O(N^2)$ to partitioned blocks, completing full candidate analysis in seconds.
5. **Neutral Decision-Support Lexicon:** 100% compliance with ethical governance terminology ("Requires review", "Statistically unusual", "High-risk signal").
