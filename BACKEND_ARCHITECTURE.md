# MPLAD GUARDIAN — BACKEND ARCHITECTURE (CURRENT STATE)

## 1. System Overview
**Framework**: FastAPI (Python 3.11)
**Database**: SQLite 3 (WAL Mode, stored at `C:\SIH_PROJECT\mplad.db`)
**Current Records**:
- Projects: 96,654
- Vouchers: 106,442
- MPs: 764
- Risk Scores: 96,654
- Alerts: 270

## 2. API Routes
All routes are currently mounted directly under `/api` or at the root without an active `/v1/` versioning strategy, though `projects_router` uses `/api/projects`.

**Available Routers**:
1. `auth_router` (`/api/auth`)
2. `dashboard_router` (`/api/dashboard`)
3. `projects_router` (`/api/projects`)
4. `risks_router` (`/api/risk`)
5. `states_router` (`/api/states`)
6. `mps_router` (`/api/mps`)
7. `alerts_router` (`/api/alerts`)
8. `data_quality_router` (`/api/data-quality`)
9. `audit_router` (`/api/audit`)
10. `analytics_router` (`/api/analytics`)

## 3. Database Architecture & Access
- **Connection**: Managed via `backend/app/database.py` with custom `_get_connection()`.
- **Query Strategy**: Direct parameterized SQL using standard SQLite DB-API 2.0 cursor execution (`query_db`, `execute_db`). No heavy ORM is currently used, keeping queries raw and close to the metal.
- **Transactions**: Write operations handle manual `conn.commit()`.

## 4. Current Request Flow
1. Client HTTP Request
2. **CORS Middleware**: Evaluates origins (strict in prod).
3. **Security & Tracing Middleware**: Attaches `X-Request-ID`, calculates timing, injects strict CSP and HTTP security headers, catches global unhandled exceptions.
4. **FastAPI Router**: Maps request to handler.
5. **Database Access**: Handler executes SQL via `query_db()`.
6. **AI Service Invocation**: (If applicable) Syncs/blocks until AI resolves.
7. **Response Serialization**: Row factories returned as dicts, serialized to JSON.

## 5. Middleware & Security
- `CORSMiddleware`: Validated origins.
- `security_and_tracing_middleware`: Request IDs, timing, header hardening (CSP, HSTS, X-Frame-Options, X-Content-Type-Options).
- **Authentication**: JWT-based with Argon2id hashing, tested in Phase 3.
- **RBAC**: Handled in auth/route dependencies.

## 6. Caching Layer
- Custom in-memory `@timed_cache` decorator implemented in `cache.py`.
- No external Redis/Memcached cluster is currently connected. Cache is strictly ephemeral process memory.

## 7. Known Expensive Operations & AI Calls
- **N+1 Vulnerabilities**: Iterating over projects and subsequently fetching risk scores or comparables per project if not properly JOINed.
- **Aggregation Queries**: `dashboard_router` and `analytics_router` potentially scan large portions of `projects` and `vouchers` tables.
- **AI Analytics**: Direct Python blocking calls on routes like `/analyze/batch` or `/detect/duplicates`. Needs migration to async queue.

## 8. Current Limitations & Actionable Forensics
- **Pagination**: Implemented functionally in some routes (like `/api/projects`), but missing a strict standardized wrapper structure (`{ data, meta }`).
- **Database Scalability**: Still utilizing SQLite. A PostGIS/PostgreSQL migration is required for large-scale spatial/geospatial operations.
- **Job Processing**: Missing a dedicated queue (Celery/RQ) for AI and large PDF exports.

*Document generated during Phase 4.0 Forensics Inspection.*
