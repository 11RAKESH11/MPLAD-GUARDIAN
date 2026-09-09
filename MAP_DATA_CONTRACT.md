# MAP DATA CONTRACT — INDIA DEVELOPMENT INTELLIGENCE GIS

**Document Version:** `2.0.0`  
**Effective Date:** 2026-08-28  
**Scope:** Geospatial boundaries, backend aggregation queries, spatial coordinate policy, and API payloads for MPLAD GUARDIAN.

---

## 1. Authoritative Geographic Geometry

### 1.1 Administrative Boundaries & Coverage
- **National State/UT Boundaries:** 36 States & Union Territories mapped via optimized GeoJSON (`frontend/src/data/india_states_geo.json`).
- **District Boundaries:** 750+ Districts mapped via individual state GeoJSON partitions (`frontend/public/data/districts/{code}.json`).
- **Spatial Reference System:** WGS 84 (`EPSG:4326`).

### 1.2 Coordinate Fabrication Policy
> **STRICT COMPLIANCE MANDATE:** Project-level GPS coordinates are **NOT** present in official MoSPI raw CSV source files.
- **Zero Coordinate Fabrication:** Exact project coordinates are never synthesized, geocoded to fake pins, or assigned to random points inside district centroids.
- **Visual Representation:** Spatial visualization operates exclusively at the **State and District polygon aggregation** level.
- **Explicit Metric Reporting:** `gpsCoveragePct: 0.0%`, `geographicCoveragePct: 100.0%`, `districtMappingPct: 100.0%`.

---

## 2. Supported Layer Metric Modes

| Layer Identifier | Metric Evaluated | Calculation Formula | Color Scale / Tiers |
| :--- | :--- | :--- | :--- |
| `risk_concentration` | Analytical Risk | `AVG(r.overall_risk_score)` | Low (0–10), Med (10–25), High (25–50), Critical (&gt;50) |
| `project_count` | Work Density | `COUNT(p.work_code)` | &lt;50, 50–500, 500–1.5k, 1.5k–4k, 4k–8k, &gt;8k |
| `sanctioned_funds` | Fund Allocation | `SUM(p.sanctioned_amount)` | &lt;₹100 Cr, ₹100–500 Cr, ₹500–1500 Cr, &gt;₹3000 Cr |
| `utilization` | Expenditure % | `(SUM(exp) / SUM(sanc)) * 100` | &lt;45% (Red), 45–60% (Amber), 60–75% (Green), &gt;75% (Dark Green) |
| `completion_rate` | Physical Progress | `(Completed / Total) * 100` | &lt;20% (Red), 20–35% (Amber), 35–50% (Green), &gt;50% (Dark Green) |
| `anomalies` | Signals Density | `SUM(Critical + High Signals)` | &lt;4 (Emerald), 4–12 (Amber), 12–30 (Red), &gt;30 (Burgundy) |

---

## 3. Dedicated Geospatial API Contract (`/api/v1/map`)

### 3.1 `GET /api/v1/map/summary`
```json
{
  "totalProjects": 96654,
  "totalStates": 36,
  "totalDistricts": 767,
  "totalSanctioned": 57511237457.95,
  "totalExpenditure": 39240698923.14,
  "utilizationPct": 68.23,
  "completionPct": 45.0,
  "criticalSignals": 10,
  "highSignals": 260,
  "dataQuality": {
    "geographicCoveragePct": 100.0,
    "districtMappingPct": 100.0,
    "gpsCoveragePct": 0.0,
    "policy": "District and State polygon aggregation only. Zero project coordinates fabricated."
  },
  "source": "Official MoSPI MPLAD dataset"
}
```

### 3.2 `GET /api/v1/map/states`
Accepts query params: `year`, `category`, `status`, `riskLevel`.
Returns array of 36 State records with complete project counts, financial sums, completion %, utilization %, and signal breakdowns.

### 3.3 `GET /api/v1/map/state/{state_name}`
Returns state overview KPIs, all constituent districts breakdown, and sector category distributions.

### 3.4 `GET /api/v1/map/district/{state_name}/{district_name}`
Returns deep district intelligence for the right sliding panel, including:
- `overview`: `totalProjects`, `totalSanctioned`, `utilizationPct`, `completionPct`.
- `signalsBreakdown`: `costAnomalies`, `progressGaps`, `potentialDuplicates`.
- `signalsOverlapNote`: *"Analytical signals may overlap across multiple dimensions on the same project."*
- `topProjects`: High-risk works list with work code, sanctioned funds, and status for direct investigation.
