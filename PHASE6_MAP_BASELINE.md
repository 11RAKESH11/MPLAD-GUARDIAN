# PHASE 6.0 — MAP BASELINE & GIS AUDIT REPORT

**Project:** MPLAD GUARDIAN — India Intelligence GIS Experience  
**Audit Timestamp:** 2026-08-28T22:15:00+05:30  
**Cartographic Engine:** Leaflet 1.9 + GeoJSON Administrative Boundaries  
**Auditor:** Principal GIS Architect & Geospatial Data Engineer  

---

## 1. Executive Summary

A comprehensive forensic audit of the existing geospatial stack was conducted across the database schema, backend API routes, frontend React components, and GeoJSON boundary files. The system contains **verified administrative boundaries for all 36 States/UTs and 750+ districts**, with full state/district name normalization. 

**Critical Geographic Finding:** The source MoSPI dataset contains zero raw project-level GPS coordinates. Project `latitude` and `longitude` fields remain strictly `NULL` in the database. The previous frontend map correctly refrained from fabricating coordinates but required enhancement to provide a unified National Intelligence experience with dynamic multi-metric choropleths, district-level aggregation layers, deep drilldowns, synchronized URL filters, and an explainable District Intelligence Drawer.

---

## 2. Inventory of Current Geospatial Assets

| Asset | Path | File Size | Description & Status |
| :--- | :--- | :--- | :--- |
| **State GeoJSON** | `frontend/src/data/india_states_geo.json` | 477 KB | Optimized, topology-preserved polygons for all 36 States/UTs. |
| **District GeoJSON** | `frontend/src/data/india_districts_geo.json` | 31.6 MB | High-resolution district boundary GeoJSON for district drilldowns. |
| **State Boundary Source**| `frontend/src/data/india_states.geojson` | 13.6 MB | Authoritative administrative boundaries source. |
| **Map Component** | `frontend/src/components/map/IndiaRiskMap.tsx` | 42.6 KB | Main interactive Leaflet map component with state/district hover/click handlers. |
| **Map Page** | `frontend/src/pages/RiskMapPage.tsx` | 1.3 KB | Router container page for the National Risk Command Center. |
| **Backend State API** | `backend/app/routers/states_router.py` | 4.4 KB | State-level aggregations and district breakdowns. |
| **Backend Map API** | `backend/app/routers/analytics_router.py` | 14.3 KB | Filtered map queries for states and district drilldowns. |

---

## 3. Current Limitations & Upgrade Objectives

1. **Dedicated Map Router:** Map queries were coupled within generic analytics routes. A dedicated `/api/v1/map` router with specialized PostGIS and SQL aggregation endpoints (`/summary`, `/states`, `/districts`, `/state/{name}`, `/district/{name}`) will provide clean separation and sub-50ms cached responses.
2. **Multi-Metric Layer Modes:** Add smooth switching between 6 distinct intelligence views:
   - **Risk Concentration** (`average_risk` / `risk_signals`)
   - **Project Density** (`project_count` with non-population-adjusted disclaimer)
   - **Sanctioned Funds** (`total_sanctioned` with Indian Crores/Lakhs formatting)
   - **Fund Utilization** (`expenditure / sanctioned` percentage)
   - **Completion Indicator** (`completed_works / total_projects`)
   - **Anomalies / Concentration** (Combined high-risk signals, duplicate signals, progress gaps)
3. **Deep District Intelligence Drawer:** Expand state and district inspection into a sliding intelligence panel displaying comprehensive operational metrics, breakdown of analytical signals, evidence coverage percentages, and direct navigation links to `[VIEW PROJECTS]` and `[VIEW SIGNALS]`.
4. **URL State Synchronization:** Enable deep linking via query params (e.g., `/map?state=Karnataka&fy=2024-2025&metric=risk`) to allow instant sharing and bookmarked investigative views.
5. **Strict Data Quality Disclaimers:** Explicitly display "Exact GPS coverage: 0% — District aggregation only — Zero coordinates fabricated" across legends, tooltips, and info badges.
6. **Dark & Light Mode Refinement:** Ensure high-contrast boundary rendering, legible typography, and accessible indicators across both dark and light government dashboard palettes.
