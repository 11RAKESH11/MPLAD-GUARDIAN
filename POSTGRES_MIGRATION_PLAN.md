# PostgreSQL & PostGIS Migration Plan

## 1. Objective
Migrate MPLAD GUARDIAN from its current high-performance embedded SQLite database (WAL mode) to a production-grade PostgreSQL cluster with the PostGIS extension, enabling robust spatial queries, horizontal scaling, and enterprise backup/restore capabilities.

## 2. Current State Assessment
- **Database:** SQLite 3 (using WAL mode and PRAGMA optimizations for throughput).
- **Data Footprint:** 
  - `projects` (96,654 records)
  - `risk_scores` (96,654 records)
  - `comparable_projects` (36,732 records)
  - `expenditure_vouchers` (106,442 records)
  - Various other tables (`alerts`, `mps`, `audit_logs`, `background_jobs`).
- **Connection Strategy:** Synchronous connection pooling via Python's `sqlite3`.

## 3. Pre-Migration Prerequisites
1. **Provision PostgreSQL Cluster:** Provision a PostgreSQL 15+ instance with PostGIS installed.
2. **Environment Variables:** Introduce `DATABASE_URL` for dynamic connection switching.
3. **ORM / Abstraction Strategy:** Currently, queries are raw SQL using `query_db` and `execute_db`. 
   - *Option A:* Refactor raw SQL to account for syntax differences (`?` vs `%s` or `$1`).
   - *Option B:* Introduce a lightweight query builder or ORM (e.g., SQLAlchemy Core or databases).

## 4. Migration Steps

### Step 4.1: Database Abstraction Refactoring
1. Update `database.py` to support connection pooling using `psycopg2` or `asyncpg`.
2. Implement a unified placeholder converter (e.g., parsing `?` to `%s`) or rewrite existing raw queries to conform to psycopg2's `%s` format.
3. Replace SQLite-specific functions (like `COALESCE(..., 0)` vs PostgreSQL's handling of specific casting, or text/blob differences).

### Step 4.2: Schema Translation
1. **Data Types:** Convert SQLite `TEXT` / `INTEGER` / `REAL` to PostgreSQL `VARCHAR`, `TEXT`, `INTEGER`, `BIGINT`, `NUMERIC`, `TIMESTAMP`, and `JSONB` (especially for `raw_data` and `explanation_json`).
2. **Spatial Data:** Integrate PostGIS. Add a `geom geometry(Point, 4326)` column to `projects` for exact geospatial mapping, replacing generic state/district text mapping.

### Step 4.3: Data Migration
1. Export SQLite data to CSVs or write a bespoke Python script (ETL) to select from SQLite and insert into PostgreSQL.
2. Example ETL Flow:
   ```python
   # Read from SQLite
   projects = sqlite_conn.execute("SELECT * FROM projects").fetchall()
   # Write to PostgreSQL
   pg_cursor.executemany("INSERT INTO projects (...) VALUES (...)", projects)
   pg_conn.commit()
   ```
3. Calculate and populate the `geom` column using a PostGIS `ST_SetSRID(ST_MakePoint(lon, lat), 4326)` logic if lat/lon can be geocoded from state/district values.

### Step 4.4: Application Testing
1. Execute the `tests/test_data_integrity.py` and `tests/test_security_suite.py` against the PostgreSQL connection.
2. Ensure no N+1 query regressions occur due to different driver behaviors.
3. Verify JSON parsing works natively with PostgreSQL `JSONB` columns, removing the need for manual `json.loads()` inside the routers.

## 5. Rollback Strategy
1. Maintain the SQLite database as read-only during migration.
2. If the PostgreSQL switch introduces latency or failures, flip the `DATABASE_URL` environment variable back to the SQLite file path and restart the Fastapi service.

## 6. Timeline and Effort Estimate
- **Refactoring Queries:** 3 Days
- **Schema & ETL Scripting:** 2 Days
- **Testing & QA:** 2 Days
- **Production Cutover:** 4 Hours
