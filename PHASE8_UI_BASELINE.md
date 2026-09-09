# PHASE 8 UI BASELINE AUDIT

**Project:** MPLAD GUARDIAN  
**Audit Date:** 2026-08-28  
**Auditor:** Principal Product Designer + UX Architect  

---

## 1. Current Layout Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Sidebar (w-64, fixed left)  │  Content (ml-64)          │
│  ─────────────────────────   │  ─────────────────────    │
│  Logo: MPLAD GUARDIAN        │  TopNav (h-16, fixed)     │
│  Brand: National Dev Intel   │  Search + Freshness badge │
│                              │  + Bell + User menu       │
│  OVERVIEW                    │                           │
│    National Pulse            │  Page Content (pt-16)     │
│    National GIS Map          │  mt-8, px-6-8             │
│                              │                           │
│  DEVELOPMENT                 │  DashboardPage content:   │
│    Projects Explorer         │  ─ Hero Banner            │
│    States & Districts        │  ─ 5× KPI MetricCards     │
│    MP Portfolios             │  ─ IndiaRiskMap            │
│    Compare Indicators        │  ─ 3× Narrative Insights  │
│                              │  ─ Area Chart (FY Trends) │
│  MONITORING & DECISION       │  ─ State Rankings table   │
│    Priority Review Queue     │                           │
│    Data Quality & Health     │                           │
│                              │                           │
│  GOVERNANCE & AUDIT          │                           │
│    System Audit Trail        │                           │
│    Reports & Briefs          │                           │
│    Platform Settings         │                           │
│                              │                           │
│  Footer: AI Operational      │                           │
│          374,141 records     │                           │
│          Data updated badge  │                           │
└──────────────────────────────────────────────────────────┘
```

---

## 2. Current Component Inventory

### Layout
| Component | File | Role |
|-----------|------|------|
| `AppLayout` | `components/layout/AppLayout.tsx` | Shell wrapper, sidbar + topnav |
| `Sidebar` | `components/layout/Sidebar.tsx` | Fixed left nav, brand, sections, status footer |
| `TopNav` | `components/layout/TopNav.tsx` | Search trigger, freshness badge, bell, user dropdown |

### Dashboard
| Component | File | Role |
|-----------|------|------|
| `DashboardPage` | `pages/DashboardPage.tsx` | Main executive overview |
| `MetricCard` | `components/common/MetricCard.tsx` | KPI card with value, subtitle, source badge |
| `IndiaRiskMap` | `components/map/IndiaRiskMap.tsx` | Full Phase 6 GIS map |
| `EvidenceRoomModal` | `components/explainer/EvidenceRoomModal.tsx` | 7-tab Investigation Workspace |

### Common
| Component | Notes |
|-----------|-------|
| `SourceBadge` | Tag showing data lineage type |
| `CardSkeleton` | Loading skeleton for cards |
| `TableSkeleton` | Loading skeleton for tables |

---

## 3. Current API Endpoints Used by Dashboard

| API | Endpoint | Status |
|-----|---------|--------|
| `getDashboardOverview()` | `GET /api/v1/dashboard/overview` | ✅ Real data |
| `getDashboardInsights()` | `GET /api/v1/dashboard/insights` | ✅ Real derived queries |
| `getDashboardTrends()` | `GET /api/v1/dashboard/trends` | ✅ Real FY data |
| `getRiskMapData()` | `GET /api/v1/risks/map` | ✅ Real state aggregations |

---

## 4. Current Data Sources

### Real (Verified)
- `total_projects` — `COUNT(*) FROM projects` = 96,654
- `total_sanctioned_funds` — `SUM(sanctioned_amount) FROM projects`
- `total_expenditure_funds` — `SUM(expenditure_amount) FROM projects`
- `completed_works` — `SUM(CASE WHEN status='Work Completed')` 
- `risk_level counts` — `FROM risk_scores GROUP BY risk_level`
- `financial_year_trends` — `GROUP BY financial_year`
- `category_distribution` — `GROUP BY category`
- `narrative insights` — derived from real queries

### Hardcoded / Stale (Problems Identified)
| Field | Value | Issue |
|-------|-------|-------|
| `total_vouchers` | 106,442 hardcoded | Should be `COUNT(*) FROM expenditure_vouchers` |
| `total_unique_vendors` | 24,651 hardcoded | Not queried from DB |
| `potential_duplicates_count` | 3,558 hardcoded | Should be queried from comparable_projects |
| `data_health.completeness_pct` | 98.4 hardcoded | Should be calculated |
| `data_health.source_files_count` | 12 hardcoded | Static |
| `data_health.last_analysis` | "2026-08-23T20:31:00Z" hardcoded | Static string |
| State freshness in TopNav | "23 Aug 2026" | Hardcoded date string |
| Sidebar "374,141" | Static | Not queried |

---

## 5. Current Dashboard Sections

| Section | Visual Weight | Content | Quality |
|---------|--------------|---------|---------|
| Hero Banner | Medium | Title + "Priority Queue" button | Adequate |
| 5× KPI Cards | High | Projects, Funds, Expenditure, Completed, Signals | Good — real data |
| IndiaRiskMap | Very High | Full 6-mode GIS map | Excellent |
| Narrative Insights | Medium | 3 AI-derived insight cards | Good — real data |
| FY Trend Chart | Medium | Sanctioned vs Expenditure area chart | Good |
| State Rankings | Medium | Sortable 7-state bar list | Good |

---

## 6. Visual Strengths
- Clean government palette (deep navy #102A43 + off-white + slate)
- Map is the visual centrepiece
- Source badges establish credibility
- MetricCard component is reusable
- Sidebar navigation is clear and well-structured
- Data is real, not fabricated

## 7. Current Weaknesses

### Information Architecture
- Dashboard answers "what" but not strongly "what changed?" or "what needs attention now?"
- No dedicated "Priority Review Queue" section on the dashboard itself
- No financial flow visualization (Recommended → Sanctioned → Disbursed → Expenditure)
- No signal type breakdown (cost / duplicate / progress / geographic)
- No risk distribution chart (CRITICAL / HIGH / MEDIUM / LOW)
- No data quality section
- No category analytics visualization

### Data Integrity
- Several hardcoded values in `dashboard_router.py` (see above)
- `data_health` section returns fully static values

### UX Gaps
- No "What Needs Attention?" surface with top 3–5 urgent signals linking directly to Evidence Room
- No "What Changed?" section (requires historical comparison)
- State rankings use word "Performance Leaderboard" — removed but labelling still implies ranking
- Loading state uses single full-page skeleton — sections should fail independently
- No URL-state filter persistence

### Technical
- `fyTrendsData` computes `recommended` as `sanctioned * 1.15` — fabricated value, not real recommended amounts
- Area chart silently fails to invalid array shapes

---

## 8. Phase 8 Transformation Plan

Transform into: **National Development Intelligence Cockpit**

Priority order:
1. Fix all hardcoded values in backend
2. Add Financial Flow visualization
3. Add Signal Distribution breakdown
4. Add Risk Distribution chart
5. Add "What Needs Attention?" section with Evidence Room deep links
6. Add Category distribution
7. Add Data Quality card with live queries
8. Create `EXECUTIVE_DASHBOARD_DATA_CONTRACT.md`
9. Write `tests/test_executive_dashboard.py`
10. Write Phase 8 final report
