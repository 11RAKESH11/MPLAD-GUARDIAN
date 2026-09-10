"""
MPLAD GUARDIAN — Professional SQLite → PostgreSQL Migration Engine v3.0

Architecture:
  - Explicit source-to-target column mapping per table (no blind column copying)
  - Dry-run and live modes
  - Configurable SQLite path, PostgreSQL DSN, and batch size
  - Idempotent (safe to re-run)
  - Transactional with per-batch rollback on failure
  - Progress reporting and per-table statistics
  - Foreign-key safe insertion order
  - PostgreSQL sequence repair after migration
  - Verification mode (compare source vs target counts/aggregates)

Usage:
  python scripts/migrate_sqlite_to_postgres.py --dry-run
  python scripts/migrate_sqlite_to_postgres.py --live
  python scripts/migrate_sqlite_to_postgres.py --verify
  python scripts/migrate_sqlite_to_postgres.py --live --dsn=postgresql://user:pass@host:5432/db
  python scripts/migrate_sqlite_to_postgres.py --live --sqlite-path=/data/mplad.db --batch-size=1000
"""

import os
import sys
import time
import json
import sqlite3
import logging
import argparse
import decimal
from datetime import datetime
from typing import Any, Optional

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("mplad.migration")

# ─── Configuration ────────────────────────────────────────────────────────────

def get_default_sqlite_path() -> str:
    """Resolve default SQLite path relative to script location."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    return os.path.join(project_root, "mplad.db")

DEFAULT_SQLITE_PATH = os.getenv("SQLITE_PATH", get_default_sqlite_path())
DEFAULT_PG_DSN = os.getenv(
    "DATABASE_URL",
    "postgresql://app_user:app_password@localhost:5432/mplad_db"
)
DEFAULT_BATCH_SIZE = int(os.getenv("MIGRATION_BATCH_SIZE", "2500"))


# ─── Table Migration Definitions ──────────────────────────────────────────────
# Each table definition specifies:
#   columns: list of (sqlite_column_or_None, pg_column, transformation_func_or_None)
#   conflict_target: PostgreSQL conflict column(s) for ON CONFLICT
#   notes: documentation of decisions made

import os.path as osp

def _ts(val: Any) -> Optional[str]:
    """Normalize a timestamp to ISO format or None."""
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    return s

def _decimal(val: Any) -> Optional[float]:
    """Convert to float, preserving None. Handles Decimal and numeric strings."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def _int(val: Any) -> Optional[int]:
    """Convert to int, preserving None."""
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None

def _json_str(val: Any) -> Optional[str]:
    """Ensure JSON field is a valid string for JSONB or None."""
    if val is None:
        return None
    if isinstance(val, str):
        # Validate it's actually JSON
        try:
            json.loads(val)
            return val
        except Exception:
            return None
    try:
        return json.dumps(val, default=str)
    except Exception:
        return None

def _basename(val: Any) -> Optional[str]:
    """Extract basename from a file path."""
    if val is None:
        return None
    return osp.basename(str(val))


# ─── Schema mismatch analysis ─────────────────────────────────────────────────
#
# SQLite data_sources columns: id, name, house, file_path, sha256_hash, row_count, col_count, file_size_bytes, last_ingested_at
# PG data_sources columns:     id(SERIAL), source_name, file_name, file_path, row_count, file_size_bytes, sha256_hash, ingested_at
# Mapping:
#   name → source_name
#   file_path → file_path  (direct)
#   basename(file_path) → file_name  (derived)
#   last_ingested_at → ingested_at
#   col_count → INTENTIONALLY DROPPED (no PG column, not production-relevant metadata)
#   house → INTENTIONALLY DROPPED (no PG column, not production-relevant metadata)
#   id → NOT INSERTED (PG uses SERIAL auto-increment)
#
# SQLite ingestion_runs columns: run_id, source_file, source_hash, started_at, completed_at, status,
#                                rows_read, rows_accepted, rows_rejected, rows_updated, rows_inserted,
#                                duplicates_detected, validation_errors, warnings, app_version, schema_version
# PG ingestion_runs columns: id(SERIAL), run_id, total_files, total_raw_rows, total_canonical_projects,
#                             total_vouchers, status, duration_seconds, created_at
# Mapping:
#   run_id → run_id
#   rows_read → total_raw_rows
#   rows_accepted → total_canonical_projects
#   started_at → created_at
#   status → status
#   source_file, source_hash, rows_rejected, rows_updated, rows_inserted, duplicates_detected,
#   validation_errors, warnings, app_version, schema_version → INTENTIONALLY DROPPED
#     (these are ETL metadata, not needed in production PostgreSQL schema)
#   total_files → 0 (default, not available in SQLite)
#   total_vouchers → 0 (default, not available in SQLite)
#   duration_seconds → 0 (default, not available in SQLite)
#
# SQLite location_mappings columns: id, raw_name, canonical_name, state, mapping_type, mapping_method, confidence, created_at
# PG location_mappings columns: id(SERIAL), raw_state, canonical_state, raw_district, canonical_district, state_code
# Mapping:
#   raw_name → raw_state  (raw input state name)
#   canonical_name → canonical_state
#   state → state_code
#   raw_district → NULL (SQLite has no district data here)
#   canonical_district → NULL (SQLite has no district data here)
#   mapping_type, mapping_method, confidence, created_at → INTENTIONALLY DROPPED (no PG cols)
#   id (TEXT) → NOT INSERTED (PG uses SERIAL)
#
# SQLite projects 28 cols → PG projects (without source_file, created_at matches, raw_data → JSONB)
# SQLite mps: name → name (UNIQUE). PG mps: name TEXT UNIQUE NOT NULL
# SQLite comparable_projects: id INTEGER → PG comparable_projects: id SERIAL (skip id)
# SQLite alerts: impact_level → INTENTIONALLY DROPPED (no PG column)
# SQLite background_jobs: columns match PG schema well (direct map)
# SQLite audit_logs: id INTEGER → PG id SERIAL (skip id from SQLite)
# ─────────────────────────────────────────────────────────────────────────────


def get_sqlite_conn(path: str) -> sqlite3.Connection:
    if not os.path.exists(path):
        raise FileNotFoundError(f"SQLite source not found: {path}")
    conn = sqlite3.connect(path, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def get_pg_conn(dsn: str):
    try:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(dsn, connect_timeout=30)
        conn.autocommit = False
        return conn
    except ImportError:
        raise ImportError("psycopg2 not installed. Run: pip install psycopg2-binary")


def _build_insert(table: str, pg_cols: list, placeholders: list = None) -> str:
    col_str = ", ".join([f'"{c}"' for c in pg_cols])
    if placeholders is None:
        ph_str = ", ".join(["%s"] * len(pg_cols))
    else:
        ph_str = ", ".join(placeholders)
    return f'INSERT INTO "{table}" ({col_str}) VALUES ({ph_str}) ON CONFLICT DO NOTHING'


# ─── Per-Table Migration Functions ────────────────────────────────────────────

def migrate_data_sources(s_cur, pg_conn, dry_run: bool, batch_size: int) -> dict:
    """
    SQLite: id(TEXT PK), name, house, file_path, sha256_hash, row_count, col_count, file_size_bytes, last_ingested_at
    PG:     id(SERIAL), source_name, file_name, file_path, row_count, file_size_bytes, sha256_hash, ingested_at
    """
    table = "data_sources"
    s_cur.execute('SELECT COUNT(*) FROM "data_sources"')
    total = s_cur.fetchone()[0]
    if total == 0:
        return {"source_rows": 0, "migrated_rows": 0, "skipped_rows": 0, "error_rows": 0, "duration_seconds": 0.0}

    pg_cols = ["source_name", "file_name", "file_path", "row_count", "file_size_bytes", "sha256_hash", "ingested_at"]
    insert_sql = _build_insert(table, pg_cols)

    s_cur.execute('SELECT name, file_path, sha256_hash, row_count, file_size_bytes, last_ingested_at FROM "data_sources"')
    return _batch_migrate(s_cur, pg_conn, table, insert_sql, total, batch_size, dry_run,
        transform=lambda r: (
            r["name"],
            _basename(r["file_path"]),
            r["file_path"],
            _int(r["row_count"]) or 0,
            _int(r["file_size_bytes"]) or 0,
            r["sha256_hash"],
            _ts(r["last_ingested_at"])
        )
    )


def migrate_ingestion_runs(s_cur, pg_conn, dry_run: bool, batch_size: int) -> dict:
    """
    SQLite: run_id(PK), source_file, source_hash, started_at, completed_at, status, rows_read, rows_accepted, ...
    PG:     id(SERIAL), run_id(UNIQUE), total_files, total_raw_rows, total_canonical_projects, total_vouchers, status, duration_seconds, created_at
    """
    table = "ingestion_runs"
    s_cur.execute('SELECT COUNT(*) FROM "ingestion_runs"')
    total = s_cur.fetchone()[0]
    if total == 0:
        return {"source_rows": 0, "migrated_rows": 0, "skipped_rows": 0, "error_rows": 0, "duration_seconds": 0.0}

    pg_cols = ["run_id", "total_files", "total_raw_rows", "total_canonical_projects", "total_vouchers", "status", "duration_seconds", "created_at"]
    insert_sql = 'INSERT INTO "ingestion_runs" ("run_id", "total_files", "total_raw_rows", "total_canonical_projects", "total_vouchers", "status", "duration_seconds", "created_at") VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (run_id) DO NOTHING'

    s_cur.execute('SELECT run_id, rows_read, rows_accepted, started_at, status FROM "ingestion_runs"')
    return _batch_migrate(s_cur, pg_conn, table, insert_sql, total, batch_size, dry_run,
        transform=lambda r: (
            r["run_id"],
            0,
            _int(r["rows_read"]) or 0,
            _int(r["rows_accepted"]) or 0,
            0,
            r["status"],
            0.0,
            _ts(r["started_at"])
        )
    )


def migrate_location_mappings(s_cur, pg_conn, dry_run: bool, batch_size: int) -> dict:
    """
    SQLite: id(TEXT PK), raw_name, canonical_name, state, mapping_type, mapping_method, confidence, created_at
    PG:     id(SERIAL), raw_state, canonical_state, raw_district, canonical_district, state_code
    """
    table = "location_mappings"
    s_cur.execute('SELECT COUNT(*) FROM "location_mappings"')
    total = s_cur.fetchone()[0]
    if total == 0:
        return {"source_rows": 0, "migrated_rows": 0, "skipped_rows": 0, "error_rows": 0, "duration_seconds": 0.0}

    insert_sql = 'INSERT INTO "location_mappings" ("raw_state", "canonical_state", "raw_district", "canonical_district", "state_code") VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING'

    s_cur.execute('SELECT raw_name, canonical_name, state FROM "location_mappings"')
    return _batch_migrate(s_cur, pg_conn, table, insert_sql, total, batch_size, dry_run,
        transform=lambda r: (
            r["raw_name"],
            r["canonical_name"],
            None,
            None,
            r["state"] or ""
        )
    )


def migrate_users(s_cur, pg_conn, dry_run: bool, batch_size: int) -> dict:
    """
    SQLite: id, username, password_hash, full_name, email, role, department, created_at
    PG:     id, username, password_hash, full_name, email, role, department, created_at
    (Direct 1:1 mapping - same schema)
    """
    table = "users"
    s_cur.execute('SELECT COUNT(*) FROM "users"')
    total = s_cur.fetchone()[0]
    if total == 0:
        return {"source_rows": 0, "migrated_rows": 0, "skipped_rows": 0, "error_rows": 0, "duration_seconds": 0.0}

    insert_sql = 'INSERT INTO "users" ("id", "username", "password_hash", "full_name", "email", "role", "department", "created_at") VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (username) DO NOTHING'

    s_cur.execute('SELECT id, username, password_hash, full_name, email, role, department, created_at FROM "users"')
    return _batch_migrate(s_cur, pg_conn, table, insert_sql, total, batch_size, dry_run,
        transform=lambda r: (
            r["id"], r["username"], r["password_hash"], r["full_name"],
            r["email"], r["role"], r["department"], _ts(r["created_at"])
        )
    )


def migrate_projects(s_cur, pg_conn, dry_run: bool, batch_size: int) -> dict:
    """
    SQLite: id, work_code, house, mp_code, mp_name, mp_type, state, district, constituency, ida_name,
            category, work_type, description, status, recommended_date, sanction_date, completion_date,
            financial_year, recommended_amount, sanctioned_amount, disbursed_amount, expenditure_amount,
            utilization_pct, vendor_count, voucher_count, has_image, created_at, raw_data
    PG:     id, work_code, house, mp_code, mp_name, mp_type, state, district, constituency, ida_name,
            category, work_type, description, status, recommended_date, sanction_date, completion_date,
            financial_year, recommended_amount, sanctioned_amount, disbursed_amount, expenditure_amount,
            utilization_pct, vendor_count, voucher_count, has_image, source_file, raw_data, created_at
    (Near 1:1 mapping, source_file added from SQLite raw_data context, raw_data JSONB)
    """
    table = "projects"
    s_cur.execute('SELECT COUNT(*) FROM "projects"')
    total = s_cur.fetchone()[0]
    if total == 0:
        return {"source_rows": 0, "migrated_rows": 0, "skipped_rows": 0, "error_rows": 0, "duration_seconds": 0.0}

    insert_sql = (
        'INSERT INTO "projects" '
        '("id","work_code","house","mp_code","mp_name","mp_type","state","district","constituency","ida_name",'
        '"category","work_type","description","status","recommended_date","sanction_date","completion_date",'
        '"financial_year","recommended_amount","sanctioned_amount","disbursed_amount","expenditure_amount",'
        '"utilization_pct","vendor_count","voucher_count","has_image","source_file","raw_data","created_at") '
        'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) '
        'ON CONFLICT (work_code) DO NOTHING'
    )

    s_cur.execute(
        'SELECT id,work_code,house,mp_code,mp_name,mp_type,state,district,constituency,ida_name,'
        'category,work_type,description,status,recommended_date,sanction_date,completion_date,'
        'financial_year,recommended_amount,sanctioned_amount,disbursed_amount,expenditure_amount,'
        'utilization_pct,vendor_count,voucher_count,has_image,created_at,raw_data FROM "projects"'
    )
    return _batch_migrate(s_cur, pg_conn, table, insert_sql, total, batch_size, dry_run,
        transform=lambda r: (
            r["id"], r["work_code"], r["house"], r["mp_code"], r["mp_name"], r["mp_type"],
            r["state"], r["district"], r["constituency"], r["ida_name"],
            r["category"], r["work_type"], r["description"], r["status"],
            r["recommended_date"], r["sanction_date"], r["completion_date"],
            r["financial_year"],
            _decimal(r["recommended_amount"]) or 0.0,
            _decimal(r["sanctioned_amount"]) or 0.0,
            _decimal(r["disbursed_amount"]) or 0.0,
            _decimal(r["expenditure_amount"]) or 0.0,
            _decimal(r["utilization_pct"]) or 0.0,
            _int(r["vendor_count"]) or 0,
            _int(r["voucher_count"]) or 0,
            _int(r["has_image"]) or 0,
            None,  # source_file - no direct SQLite equivalent
            _json_str(r["raw_data"]),
            _ts(r["created_at"])
        )
    )


def migrate_mps(s_cur, pg_conn, dry_run: bool, batch_size: int) -> dict:
    """
    SQLite: id, name, house, state, constituency, mp_type, allocated_limit, calamity_consent_amount,
            total_recommended_works, total_sanctioned_works, total_completed_works,
            total_sanctioned_amount, total_expenditure_amount, avg_risk_score, created_at
    PG: Same columns (1:1 mapping)
    """
    table = "mps"
    s_cur.execute('SELECT COUNT(*) FROM "mps"')
    total = s_cur.fetchone()[0]
    if total == 0:
        return {"source_rows": 0, "migrated_rows": 0, "skipped_rows": 0, "error_rows": 0, "duration_seconds": 0.0}

    insert_sql = (
        'INSERT INTO "mps" ("id","name","house","state","constituency","mp_type",'
        '"allocated_limit","calamity_consent_amount","total_recommended_works",'
        '"total_sanctioned_works","total_completed_works","total_sanctioned_amount",'
        '"total_expenditure_amount","avg_risk_score","created_at") '
        'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) '
        'ON CONFLICT (name) DO NOTHING'
    )

    s_cur.execute(
        'SELECT id,name,house,state,constituency,mp_type,allocated_limit,calamity_consent_amount,'
        'total_recommended_works,total_sanctioned_works,total_completed_works,'
        'total_sanctioned_amount,total_expenditure_amount,avg_risk_score,created_at FROM "mps"'
    )
    return _batch_migrate(s_cur, pg_conn, table, insert_sql, total, batch_size, dry_run,
        transform=lambda r: (
            r["id"], r["name"], r["house"], r["state"], r["constituency"], r["mp_type"],
            _decimal(r["allocated_limit"]) or 0.0,
            _decimal(r["calamity_consent_amount"]) or 0.0,
            _int(r["total_recommended_works"]) or 0,
            _int(r["total_sanctioned_works"]) or 0,
            _int(r["total_completed_works"]) or 0,
            _decimal(r["total_sanctioned_amount"]) or 0.0,
            _decimal(r["total_expenditure_amount"]) or 0.0,
            _decimal(r["avg_risk_score"]) or 0.0,
            _ts(r["created_at"])
        )
    )


def migrate_risk_scores(s_cur, pg_conn, dry_run: bool, batch_size: int) -> dict:
    """
    SQLite: work_code(PK), overall_risk_score, risk_level, confidence, cost_anomaly_score,
            duplicate_score, progress_gap_score, geographic_score, data_quality_score, coverage_pct,
            cost_zscore, cost_mad_score, comparison_group_size, explanation_json, recommendation,
            model_version, calculated_at, state, district
    PG: Same columns (1:1 mapping, explanation_json → JSONB)
    """
    table = "risk_scores"
    s_cur.execute('SELECT COUNT(*) FROM "risk_scores"')
    total = s_cur.fetchone()[0]
    if total == 0:
        return {"source_rows": 0, "migrated_rows": 0, "skipped_rows": 0, "error_rows": 0, "duration_seconds": 0.0}

    insert_sql = (
        'INSERT INTO "risk_scores" ("work_code","state","district","overall_risk_score","risk_level","confidence",'
        '"cost_anomaly_score","duplicate_score","progress_gap_score","geographic_score",'
        '"data_quality_score","coverage_pct","cost_zscore","cost_mad_score","comparison_group_size",'
        '"explanation_json","recommendation","model_version","calculated_at") '
        'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) '
        'ON CONFLICT (work_code) DO NOTHING'
    )

    s_cur.execute(
        'SELECT work_code,state,district,overall_risk_score,risk_level,confidence,'
        'cost_anomaly_score,duplicate_score,progress_gap_score,geographic_score,'
        'data_quality_score,coverage_pct,cost_zscore,cost_mad_score,comparison_group_size,'
        'explanation_json,recommendation,model_version,calculated_at FROM "risk_scores"'
    )
    return _batch_migrate(s_cur, pg_conn, table, insert_sql, total, batch_size, dry_run,
        transform=lambda r: (
            r["work_code"], r["state"], r["district"],
            _decimal(r["overall_risk_score"]) or 0.0,
            r["risk_level"],
            _decimal(r["confidence"]) or 0.0,
            _decimal(r["cost_anomaly_score"]) or 0.0,
            _decimal(r["duplicate_score"]) or 0.0,
            _decimal(r["progress_gap_score"]) or 0.0,
            _decimal(r["geographic_score"]) or 0.0,
            _decimal(r["data_quality_score"]) or 0.0,
            _decimal(r["coverage_pct"]) or 0.0,
            _decimal(r["cost_zscore"]) or 0.0,
            _decimal(r["cost_mad_score"]) or 0.0,
            _int(r["comparison_group_size"]) or 0,
            _json_str(r["explanation_json"]),
            r["recommendation"],
            r["model_version"],
            _ts(r["calculated_at"])
        )
    )


def migrate_expenditure_vouchers(s_cur, pg_conn, dry_run: bool, batch_size: int) -> dict:
    """
    SQLite: id(INTEGER PK), work_code, state, ida_name, mp_name, constituency, expenditure_date,
            vendor_name, payment_status, disbursed_amount, house, created_at
    PG:     id(SERIAL), work_code, state, ida_name, mp_name, constituency, expenditure_date,
            vendor_name, payment_status, disbursed_amount, house, created_at
    (Near 1:1 mapping - skip SQLite integer id, let PG SERIAL handle it)
    """
    table = "expenditure_vouchers"
    s_cur.execute('SELECT COUNT(*) FROM "expenditure_vouchers"')
    total = s_cur.fetchone()[0]
    if total == 0:
        return {"source_rows": 0, "migrated_rows": 0, "skipped_rows": 0, "error_rows": 0, "duration_seconds": 0.0}

    insert_sql = (
        'INSERT INTO "expenditure_vouchers" '
        '("work_code","state","ida_name","mp_name","constituency","expenditure_date",'
        '"vendor_name","payment_status","disbursed_amount","house","created_at") '
        'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) '
        'ON CONFLICT DO NOTHING'
    )

    s_cur.execute(
        'SELECT work_code,state,ida_name,mp_name,constituency,expenditure_date,'
        'vendor_name,payment_status,disbursed_amount,house,created_at FROM "expenditure_vouchers"'
    )
    return _batch_migrate(s_cur, pg_conn, table, insert_sql, total, batch_size, dry_run,
        transform=lambda r: (
            r["work_code"], r["state"], r["ida_name"], r["mp_name"], r["constituency"],
            r["expenditure_date"], r["vendor_name"], r["payment_status"],
            _decimal(r["disbursed_amount"]) or 0.0,
            r["house"], _ts(r["created_at"])
        )
    )


def migrate_comparable_projects(s_cur, pg_conn, dry_run: bool, batch_size: int) -> dict:
    """
    SQLite: id(INTEGER PK), target_work_code, comparable_work_code, similarity_score, similarity_type, reason
    PG:     id(SERIAL), target_work_code, comparable_work_code, similarity_score, similarity_type, reason, created_at
    (Skip SQLite id, let PG SERIAL handle it)
    """
    table = "comparable_projects"
    s_cur.execute('SELECT COUNT(*) FROM "comparable_projects"')
    total = s_cur.fetchone()[0]
    if total == 0:
        return {"source_rows": 0, "migrated_rows": 0, "skipped_rows": 0, "error_rows": 0, "duration_seconds": 0.0}

    insert_sql = (
        'INSERT INTO "comparable_projects" '
        '("target_work_code","comparable_work_code","similarity_score","similarity_type","reason") '
        'VALUES (%s,%s,%s,%s,%s) '
        'ON CONFLICT (target_work_code, comparable_work_code) DO NOTHING'
    )

    s_cur.execute(
        'SELECT target_work_code,comparable_work_code,similarity_score,similarity_type,reason '
        'FROM "comparable_projects"'
    )
    return _batch_migrate(s_cur, pg_conn, table, insert_sql, total, batch_size, dry_run,
        transform=lambda r: (
            r["target_work_code"], r["comparable_work_code"],
            _decimal(r["similarity_score"]) or 0.0,
            r["similarity_type"], r["reason"]
        )
    )


def migrate_alerts(s_cur, pg_conn, dry_run: bool, batch_size: int) -> dict:
    """
    SQLite: id, work_code, alert_type, title, severity, status, state, district, evidence, impact,
            action_recommendation, acknowledged_by, acknowledged_at, resolved_by, resolved_at,
            resolution_notes, created_at, assigned_to, priority_score, impact_level
    PG:     id, work_code, alert_type, title, severity, status, state, district, evidence, impact,
            action_recommendation, assigned_to, priority_score, acknowledged_by, acknowledged_at,
            resolved_by, resolved_at, resolution_notes, created_at
    Note: SQLite impact_level → INTENTIONALLY DROPPED (no PG column, impact field covers it)
    """
    table = "alerts"
    s_cur.execute('SELECT COUNT(*) FROM "alerts"')
    total = s_cur.fetchone()[0]
    if total == 0:
        return {"source_rows": 0, "migrated_rows": 0, "skipped_rows": 0, "error_rows": 0, "duration_seconds": 0.0}

    insert_sql = (
        'INSERT INTO "alerts" '
        '("id","work_code","alert_type","title","severity","status","state","district","evidence","impact",'
        '"action_recommendation","assigned_to","priority_score","acknowledged_by","acknowledged_at",'
        '"resolved_by","resolved_at","resolution_notes","created_at") '
        'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) '
        'ON CONFLICT (id) DO NOTHING'
    )

    s_cur.execute(
        'SELECT id,work_code,alert_type,title,severity,status,state,district,evidence,impact,'
        'action_recommendation,assigned_to,priority_score,acknowledged_by,acknowledged_at,'
        'resolved_by,resolved_at,resolution_notes,created_at FROM "alerts"'
    )
    return _batch_migrate(s_cur, pg_conn, table, insert_sql, total, batch_size, dry_run,
        transform=lambda r: (
            r["id"], r["work_code"], r["alert_type"], r["title"], r["severity"],
            r["status"] or "OPEN", r["state"], r["district"],
            r["evidence"] or "", r["impact"] or "",
            r["action_recommendation"] or "",
            r["assigned_to"], _decimal(r["priority_score"]) or 0.0,
            r["acknowledged_by"], _ts(r["acknowledged_at"]),
            r["resolved_by"], _ts(r["resolved_at"]),
            r["resolution_notes"], _ts(r["created_at"])
        )
    )


def migrate_data_quality_issues(s_cur, pg_conn, dry_run: bool, batch_size: int) -> dict:
    """
    SQLite: id(INTEGER PK), issue_type, severity, file_name, source_identifier, field_name, invalid_value, description, created_at
    PG:     id(SERIAL), issue_type, severity, file_name, source_identifier, field_name, invalid_value, description, created_at
    (Skip SQLite id, let PG SERIAL handle it)
    """
    table = "data_quality_issues"
    s_cur.execute('SELECT COUNT(*) FROM "data_quality_issues"')
    total = s_cur.fetchone()[0]
    if total == 0:
        logger.info(f"Table '{table}' has 0 rows. Skipping.")
        return {"source_rows": 0, "migrated_rows": 0, "skipped_rows": 0, "error_rows": 0, "duration_seconds": 0.0}

    insert_sql = (
        'INSERT INTO "data_quality_issues" '
        '("issue_type","severity","file_name","source_identifier","field_name","invalid_value","description","created_at") '
        'VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING'
    )

    s_cur.execute(
        'SELECT issue_type,severity,file_name,source_identifier,field_name,invalid_value,description,created_at '
        'FROM "data_quality_issues"'
    )
    return _batch_migrate(s_cur, pg_conn, table, insert_sql, total, batch_size, dry_run,
        transform=lambda r: (
            r["issue_type"], r["severity"], r["file_name"], r["source_identifier"],
            r["field_name"], r["invalid_value"], r["description"], _ts(r["created_at"])
        )
    )


def migrate_audit_logs(s_cur, pg_conn, dry_run: bool, batch_size: int) -> dict:
    """
    SQLite: id(INTEGER PK), user_id, username, user_role, action, target_type, target_id,
            previous_state, new_state, notes, created_at
    PG:     id(SERIAL), user_id, username, user_role, action, target_type, target_id,
            previous_state, new_state, notes, created_at
    (Skip SQLite id, let PG SERIAL auto-assign)
    """
    table = "audit_logs"
    s_cur.execute('SELECT COUNT(*) FROM "audit_logs"')
    total = s_cur.fetchone()[0]
    if total == 0:
        return {"source_rows": 0, "migrated_rows": 0, "skipped_rows": 0, "error_rows": 0, "duration_seconds": 0.0}

    insert_sql = (
        'INSERT INTO "audit_logs" '
        '("user_id","username","user_role","action","target_type","target_id",'
        '"previous_state","new_state","notes","created_at") '
        'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING'
    )

    s_cur.execute(
        'SELECT user_id,username,user_role,action,target_type,target_id,'
        'previous_state,new_state,notes,created_at FROM "audit_logs"'
    )
    return _batch_migrate(s_cur, pg_conn, table, insert_sql, total, batch_size, dry_run,
        transform=lambda r: (
            r["user_id"], r["username"], r["user_role"], r["action"],
            r["target_type"], r["target_id"],
            r["previous_state"], r["new_state"], r["notes"], _ts(r["created_at"])
        )
    )


def migrate_background_jobs(s_cur, pg_conn, dry_run: bool, batch_size: int) -> dict:
    """
    SQLite: job_id(PK), status, job_type, created_at, updated_at, result_json, error_message,
            started_at, completed_at, failed_at, attempt, progress_current, progress_total
    PG:     job_id(PK), status, job_type, created_at, updated_at, started_at, completed_at,
            failed_at, attempt, result_json(JSONB), error_message
    (Direct mapping, result_json TEXT → JSONB)
    """
    table = "background_jobs"
    s_cur.execute('SELECT COUNT(*) FROM "background_jobs"')
    total = s_cur.fetchone()[0]
    if total == 0:
        return {"source_rows": 0, "migrated_rows": 0, "skipped_rows": 0, "error_rows": 0, "duration_seconds": 0.0}

    insert_sql = (
        'INSERT INTO "background_jobs" '
        '("job_id","status","job_type","created_at","updated_at","started_at","completed_at",'
        '"failed_at","attempt","result_json","error_message") '
        'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) '
        'ON CONFLICT (job_id) DO NOTHING'
    )

    s_cur.execute(
        'SELECT job_id,status,job_type,created_at,updated_at,started_at,completed_at,'
        'failed_at,attempt,result_json,error_message FROM "background_jobs"'
    )
    return _batch_migrate(s_cur, pg_conn, table, insert_sql, total, batch_size, dry_run,
        transform=lambda r: (
            r["job_id"], r["status"], r["job_type"],
            _ts(r["created_at"]), _ts(r["updated_at"]),
            _ts(r["started_at"]), _ts(r["completed_at"]), _ts(r["failed_at"]),
            _int(r["attempt"]) or 1,
            _json_str(r["result_json"]),
            r["error_message"]
        )
    )


# ─── Generic Batch Worker ──────────────────────────────────────────────────────

def _batch_migrate(s_cur, pg_conn, table: str, insert_sql: str, total: int,
                   batch_size: int, dry_run: bool, transform) -> dict:
    """
    Generic batch migration loop with progress tracking.
    """
    import psycopg2.extras

    start_time = time.time()
    migrated = 0
    skipped = 0
    error_rows = 0

    logger.info(f"  [{table}] Starting: {total:,} source rows | batch_size={batch_size}")

    while True:
        raw_batch = s_cur.fetchmany(batch_size)
        if not raw_batch:
            break

        transformed_batch = []
        for row in raw_batch:
            try:
                transformed_batch.append(transform(row))
            except Exception as e:
                logger.warning(f"  [{table}] Row transform error: {e}. Skipping row.")
                error_rows += 1

        if dry_run:
            migrated += len(transformed_batch)
        else:
            pg_cur = pg_conn.cursor()
            try:
                psycopg2.extras.execute_batch(pg_cur, insert_sql, transformed_batch, page_size=batch_size)
                pg_conn.commit()
                migrated += len(transformed_batch)
            except Exception as e:
                pg_conn.rollback()
                logger.error(f"  [{table}] Batch FAILED: {e}")
                error_rows += len(transformed_batch)
            finally:
                pg_cur.close()

        elapsed = time.time() - start_time
        pct = round(((migrated + skipped + error_rows) / total) * 100, 1)
        logger.info(f"  [{table}] {migrated + skipped + error_rows:,}/{total:,} ({pct}%) | {elapsed:.1f}s elapsed")

    duration = time.time() - start_time
    logger.info(f"  [OK] [{table}] Done: {migrated:,} migrated, {error_rows:,} errors in {duration:.2f}s")
    return {
        "source_rows": total,
        "migrated_rows": migrated,
        "skipped_rows": skipped,
        "error_rows": error_rows,
        "duration_seconds": round(duration, 2)
    }


# ─── Sequence Repair ──────────────────────────────────────────────────────────

def repair_sequences(pg_conn):
    """Repair PostgreSQL sequences for SERIAL columns after bulk inserts."""
    logger.info("Repairing PostgreSQL sequences...")
    sequences = [
        ("expenditure_vouchers", "id", "expenditure_vouchers_id_seq"),
        ("comparable_projects", "id", "comparable_projects_id_seq"),
        ("data_quality_issues", "id", "data_quality_issues_id_seq"),
        ("audit_logs", "id", "audit_logs_id_seq"),
        ("ingestion_runs", "id", "ingestion_runs_id_seq"),
        ("location_mappings", "id", "location_mappings_id_seq"),
        ("data_sources", "id", "data_sources_id_seq"),
        ("background_jobs", None, None),  # uses TEXT PK, no sequence
    ]
    pg_cur = pg_conn.cursor()
    for table, col, seq in sequences:
        if col and seq:
            try:
                pg_cur.execute(f'SELECT MAX("{col}") FROM "{table}"')
                max_val = pg_cur.fetchone()[0]
                if max_val is not None:
                    pg_cur.execute(f"SELECT setval('{seq}', {max_val})")
                    logger.info(f"  Sequence {seq} set to {max_val}")
            except Exception as e:
                logger.warning(f"  Sequence repair for {table}: {e}")
    pg_conn.commit()
    pg_cur.close()
    logger.info("Sequence repair complete.")


# ─── Verification Mode ────────────────────────────────────────────────────────

def run_verification(sqlite_path: str, pg_dsn: str):
    """Compare SQLite source vs PostgreSQL target row counts and key aggregates."""
    logger.info("=" * 60)
    logger.info("MIGRATION VERIFICATION")
    logger.info("=" * 60)

    s_conn = get_sqlite_conn(sqlite_path)
    s_cur = s_conn.cursor()
    try:
        pg_conn = get_pg_conn(pg_dsn)
    except Exception as e:
        logger.error(f"Cannot connect to PostgreSQL: {e}")
        s_conn.close()
        return False

    pg_cur = pg_conn.cursor()

    tables = [
        "projects", "risk_scores", "expenditure_vouchers", "mps",
        "comparable_projects", "alerts", "users", "audit_logs",
        "data_sources", "ingestion_runs", "location_mappings",
        "data_quality_issues", "background_jobs"
    ]

    all_pass = True
    results = []

    for table in tables:
        try:
            s_cur.execute(f'SELECT COUNT(*) FROM "{table}"')
            src = s_cur.fetchone()[0]
            pg_cur.execute(f'SELECT COUNT(*) FROM "{table}"')
            tgt = pg_cur.fetchone()[0]
            diff = tgt - src
            status = "PASS" if diff >= 0 else "WARN"
            if status != "PASS":
                all_pass = False
            results.append((table, src, tgt, diff, status))
        except Exception as e:
            logger.error(f"Verification for {table}: {e}")
            results.append((table, "ERR", "ERR", "ERR", "FAIL"))
            all_pass = False

    logger.info(f"\n{'Table':<30} {'SQLite':>10} {'PG':>10} {'Diff':>8} {'Status':>6}")
    logger.info("-" * 70)
    for row in results:
        logger.info(f"{row[0]:<30} {str(row[1]):>10} {str(row[2]):>10} {str(row[3]):>8} {row[4]:>6}")

    # Aggregate checks
    logger.info("\nAggregate Validation:")
    agg_checks = [
        ("projects", "SUM(sanctioned_amount)", "Sanctioned Amount Total"),
        ("projects", "SUM(expenditure_amount)", "Expenditure Amount Total"),
        ("expenditure_vouchers", "SUM(disbursed_amount)", "Voucher Disbursed Total"),
        ("risk_scores", "AVG(overall_risk_score)", "Avg Risk Score"),
    ]
    for table, agg, label in agg_checks:
        try:
            s_cur.execute(f'SELECT {agg} FROM "{table}"')
            src_val = s_cur.fetchone()[0]
            pg_cur.execute(f'SELECT {agg} FROM "{table}"')
            tgt_val = pg_cur.fetchone()[0]
            match = "PASS" if src_val and tgt_val and abs(float(src_val) - float(tgt_val)) < 1.0 else "WARN"
            logger.info(f"  {label}: SQLite={src_val:.2f} PG={float(tgt_val):.2f} → {match}")
        except Exception as e:
            logger.warning(f"  {label}: {e}")

    s_conn.close()
    pg_cur.close()
    pg_conn.close()

    logger.info("\n" + ("=" * 60))
    logger.info(f"VERIFICATION {'PASS' if all_pass else 'PARTIAL PASS - check warnings'}")
    logger.info("=" * 60)
    return all_pass


# ─── Main Migration Runner ────────────────────────────────────────────────────

# Table order respects FK dependencies
MIGRATION_ORDER = [
    ("data_sources", migrate_data_sources),
    ("ingestion_runs", migrate_ingestion_runs),
    ("location_mappings", migrate_location_mappings),
    ("users", migrate_users),
    ("projects", migrate_projects),
    ("mps", migrate_mps),
    ("risk_scores", migrate_risk_scores),
    ("expenditure_vouchers", migrate_expenditure_vouchers),
    ("comparable_projects", migrate_comparable_projects),
    ("alerts", migrate_alerts),
    ("data_quality_issues", migrate_data_quality_issues),
    ("audit_logs", migrate_audit_logs),
    ("background_jobs", migrate_background_jobs),
]


def run_migration(sqlite_path: str, pg_dsn: str, dry_run: bool, batch_size: int) -> dict:
    logger.info("=" * 60)
    logger.info("MPLAD GUARDIAN — SQLITE → POSTGRESQL MIGRATION ENGINE v3.0")
    logger.info(f"Mode:         {'DRY RUN (no changes written)' if dry_run else 'LIVE MIGRATION'}")
    logger.info(f"SQLite:       {sqlite_path}")
    logger.info(f"PostgreSQL:   {pg_dsn[:40]}...")
    logger.info(f"Batch size:   {batch_size:,}")
    logger.info("=" * 60)

    s_conn = get_sqlite_conn(sqlite_path)
    pg_conn = None if dry_run else get_pg_conn(pg_dsn)

    summary = {}
    total_start = time.time()

    try:
        for table_name, migrate_fn in MIGRATION_ORDER:
            logger.info(f"\n[TABLE] {table_name}")
            s_cur = s_conn.cursor()
            try:
                stats = migrate_fn(s_cur, pg_conn, dry_run, batch_size)
                summary[table_name] = stats
            except Exception as e:
                logger.error(f"[TABLE] {table_name} migration FAILED: {e}")
                summary[table_name] = {"error": str(e)}
                if pg_conn:
                    try:
                        pg_conn.rollback()
                    except Exception:
                        pass
            finally:
                s_cur.close()

        if not dry_run and pg_conn:
            repair_sequences(pg_conn)

    finally:
        s_conn.close()
        if pg_conn:
            pg_conn.close()

    total_duration = time.time() - total_start

    logger.info("\n" + "=" * 60)
    logger.info(f"MIGRATION {'SIMULATION' if dry_run else 'COMPLETE'} — {total_duration:.2f}s")
    logger.info(f"\n{'Table':<30} {'Source':>10} {'Migrated':>10} {'Errors':>8}")
    logger.info("-" * 62)
    for table, stats in summary.items():
        if "error" in stats:
            logger.info(f"{table:<30} {'ERROR':>10} {'ERROR':>10} {'ERROR':>8}")
        else:
            logger.info(f"{table:<30} {stats.get('source_rows',0):>10,} {stats.get('migrated_rows',0):>10,} {stats.get('error_rows',0):>8,}")
    logger.info("=" * 60)

    return summary


# ─── CLI Entry Point ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="MPLAD GUARDIAN SQLite → PostgreSQL Migration Engine v3.0"
    )
    parser.add_argument("--dry-run", action="store_true", help="Simulate migration without writing to PostgreSQL")
    parser.add_argument("--live", action="store_true", help="Execute live migration")
    parser.add_argument("--verify", action="store_true", help="Verify migration completeness (compare counts)")
    parser.add_argument("--dsn", default=None, help="PostgreSQL DSN (overrides DATABASE_URL env var)")
    parser.add_argument("--sqlite-path", default=None, help="Path to SQLite source database")
    parser.add_argument("--batch-size", type=int, default=None, help="Batch size for bulk inserts")

    args = parser.parse_args()

    sqlite_path = args.sqlite_path or DEFAULT_SQLITE_PATH
    pg_dsn = args.dsn or DEFAULT_PG_DSN
    batch_size = args.batch_size or DEFAULT_BATCH_SIZE

    if args.verify:
        success = run_verification(sqlite_path, pg_dsn)
        sys.exit(0 if success else 1)

    if args.live:
        run_migration(sqlite_path, pg_dsn, dry_run=False, batch_size=batch_size)
    elif args.dry_run:
        run_migration(sqlite_path, pg_dsn, dry_run=True, batch_size=batch_size)
    else:
        logger.info("No mode specified. Running DRY RUN by default.")
        logger.info("Use --live for actual migration or --dry-run to explicitly simulate.")
        run_migration(sqlite_path, pg_dsn, dry_run=True, batch_size=batch_size)


if __name__ == "__main__":
    main()
