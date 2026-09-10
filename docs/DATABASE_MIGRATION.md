# MPLAD GUARDIAN — Database Migration Architecture & Runbook

**SIH 2026 | Problem Statement SIH26102**  
**SQLite 3 Source Database -> Production PostgreSQL 15+ with PostGIS**

---

## 1. Overview & Architectural Principles

The production deployment of MPLAD GUARDIAN transitions the source dataset (~473 MB SQLite database at `mplad.db`) to enterprise PostgreSQL 15+ with PostGIS.

### Absolute Safety Invariants
1. **Source Database Immutability**: `mplad.db` and its backup `mplad.db.phase1_backup` are strictly treated as read-only.
2. **Explicit Column Mappings**: SQLite schemas and PostgreSQL schemas differ in naming conventions, types, and column presence. Every table uses an explicit, typed column mapping.
3. **No Silent Data Loss**: Unmapped or SQLite-specific operational metadata is explicitly reviewed and handled.
4. **Transactional Idempotency**: Migrations execute within per-table transactions; re-running the migration uses `ON CONFLICT DO NOTHING` to ensure idempotency.
5. **Deterministic Sequence Repair**: PostgreSQL auto-incrementing serial sequences (`nextval`) are automatically reset to `MAX(id) + 1` post-migration.

---

## 2. Source-to-Target Schema Mapping Matrix

| Table | SQLite Columns | PostgreSQL Columns | Transformation / Strategy |
|---|---|---|---|
| `data_sources` | `id`, `name`, `house`, `file_path`, `sha256_hash`, `row_count`, `col_count`, `file_size_bytes`, `last_ingested_at` | `id` (SERIAL), `source_name`, `file_name`, `file_path`, `row_count`, `file_size_bytes`, `sha256_hash`, `ingested_at` | `name` -> `source_name`; `file_name` derived from `basename(file_path)`; `last_ingested_at` -> `ingested_at`; `id` skipped (PG SERIAL assigns). `house` and `col_count` dropped as not part of target relation. |
| `ingestion_runs` | `id`, `started_at`, `status`, `rows_read`, `rows_accepted`, `error_message`, + 10 ETL metrics | `id` (SERIAL), `data_source_id`, `run_type`, `status`, `total_raw_rows`, `total_canonical_projects`, `error_message`, `created_at` | `rows_read` -> `total_raw_rows`; `rows_accepted` -> `total_canonical_projects`; `started_at` -> `created_at`; `id` skipped. |
| `location_mappings` | `id`, `raw_name`, `canonical_name`, `state`, `created_at` | `id` (SERIAL), `raw_state`, `canonical_state`, `state_code`, `raw_district`, `canonical_district`, `created_at` | `raw_name` -> `raw_state`; `canonical_name` -> `canonical_state`; `state` -> `state_code`; districts default to NULL. |
| `users` | `id`, `username`, `password_hash`, `role`, `is_active`, `created_at` | Identical | Direct 1:1 migration with `ON CONFLICT (username) DO NOTHING`. |
| `projects` | `work_code`, `title`, `sanctioned_amount`, `expenditure_amount`, `status`, `state`, `district`, `constituency`, etc. (27 cols) | Identical (with PostGIS `geom` column) | Direct typed migration with date/numeric validation. `geom` populated as NULL unless valid GPS coordinates exist (strictly zero fabricated coordinates). |
| `mps` | `mp_code`, `name`, `house`, `constituency`, `state`, `allocated_limit`, `expenditure`, etc. (16 cols) | Identical | Direct 1:1 migration. |
| `risk_scores` | `work_code`, `overall_risk_score`, `risk_level`, `confidence`, `cost_anomaly_score`, `duplicate_score`, `progress_gap_score`, `geographic_score`, `explanation_json`, etc. (15 cols) | Identical | Direct typed migration; numeric scores bounded [0, 100]; JSON validated. |
| `expenditure_vouchers`| `id`, `work_code`, `voucher_no`, `voucher_date`, `amount`, `vendor_name`, `epay_code`, `created_at` | `id` (SERIAL), `work_code`, `voucher_no`, `voucher_date`, `amount`, `vendor_name`, `epay_code`, `created_at` | `id` skipped to allow PG serial sequencing. |
| `comparable_projects`| `id`, `source_work_code`, `target_work_code`, `similarity_score`, `match_type`, `created_at` | `id` (SERIAL), `source_work_code`, `target_work_code`, `similarity_score`, `match_type`, `created_at` | `id` skipped; scores converted to float. |
| `alerts` | `id`, `work_code`, `alert_type`, `title`, `severity`, `status`, `evidence`, `priority_score`, `impact_level`, etc. | `id` (SERIAL), `work_code`, `alert_type`, `title`, `severity`, `status`, `evidence`, `priority_score`, etc. | `impact_level` dropped as obsolete; other fields mapped directly. |
| `data_quality_issues`| `id`, `issue_type`, `table_name`, `record_id`, `description`, `created_at` | Identical | 0 source rows (skipped cleanly). |
| `audit_logs` | `id`, `user_id`, `action`, `entity_type`, `entity_id`, `details`, `timestamp` | Identical | Direct 1:1 migration. |
| `background_jobs` | `job_id`, `status`, `job_type`, `created_at`, `updated_at`, `started_at`, `completed_at`, `result_json`, etc. | Identical | Direct 1:1 migration with `ON CONFLICT (job_id) DO NOTHING`. |

---

## 3. CLI Commands & Execution Guide

The migration engine is executed using `scripts/migrate_sqlite_to_postgres.py`.

### 3.1 Dry-Run Simulation (Safe & Fast)
Simulates extracting, transforming, and batching all rows without writing to PostgreSQL:
```bash
python scripts/migrate_sqlite_to_postgres.py --dry-run
```

### 3.2 Live Execution Against PostgreSQL
Runs live migration inside transactional batches with progress logging:
```bash
python scripts/migrate_sqlite_to_postgres.py --live \
  --dsn "postgresql://app_user:app_password@localhost:5432/mplad_db" \
  --batch-size 2500
```

### 3.3 Post-Migration Integrity Verification
Compares row counts, financial aggregate sums, and distributions between SQLite and PostgreSQL:
```bash
python scripts/migrate_sqlite_to_postgres.py --verify \
  --dsn "postgresql://app_user:app_password@localhost:5432/mplad_db"
```

---

## 4. Expected Target Counts & Validation Baselines

| Table | Expected Minimum Rows | Verification Metric |
|---|---|---|
| `projects` | 96,654 | Sum of sanctioned funds = Sum of recommended funds |
| `risk_scores` | 96,654 | Overall risk score distribution matches SQLite |
| `expenditure_vouchers` | 106,442 | Total disbursed voucher amount matches SQLite |
| `mps` | 764 | Total allocations and completed works match |
| `comparable_projects` | 36,732 | Duplicate pair linkages verified |
| `alerts` | 270 | Open/Resolved triage status counts match |
| `audit_logs` | 287 | Security log records preserved |
| `background_jobs` | 11 | Initial job execution history preserved |
| `data_sources` | 12 | Ingested source files registered |

---

## 5. Rollback & Recovery Procedures

If a network or hardware interruption occurs during live migration:
1. **Per-Table Atomicity**: Each table is committed within a single atomic transaction. A failure in table $N$ leaves tables $1 \dots N-1$ safely intact.
2. **Idempotent Resumption**: Re-running `--live` safely resumes using primary key `ON CONFLICT DO NOTHING`.
3. **Emergency Target Reset**:
   ```sql
   DROP DATABASE IF EXISTS mplad_db;
   CREATE DATABASE mplad_db;
   \c mplad_db
   \i migrations/001_initial_postgres_schema.sql
   ```
   Then re-run `--live`. The SQLite database is never modified or at risk.
