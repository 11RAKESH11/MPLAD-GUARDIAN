-- ==============================================================================
-- MPLAD GUARDIAN — PostgreSQL Production Schema Migration (001_initial_postgres_schema.sql)
-- Authoritative, hardened schema definition with NUMERIC financial precision and JSONB
-- ==============================================================================

-- 1. Enable Required PostgreSQL Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 2. Projects Canonical Master Table
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    work_code TEXT UNIQUE NOT NULL,
    house TEXT NOT NULL,
    mp_code TEXT,
    mp_name TEXT NOT NULL,
    mp_type TEXT,
    state TEXT NOT NULL,
    district TEXT NOT NULL,
    constituency TEXT,
    ida_name TEXT,
    category TEXT NOT NULL,
    work_type TEXT,
    description TEXT,
    status TEXT NOT NULL,
    recommended_date DATE,
    sanction_date DATE,
    completion_date DATE,
    financial_year TEXT NOT NULL,
    recommended_amount NUMERIC(18, 2) DEFAULT 0.00 NOT NULL,
    sanctioned_amount NUMERIC(18, 2) DEFAULT 0.00 NOT NULL,
    disbursed_amount NUMERIC(18, 2) DEFAULT 0.00 NOT NULL,
    expenditure_amount NUMERIC(18, 2) DEFAULT 0.00 NOT NULL,
    utilization_pct NUMERIC(6, 2) DEFAULT 0.00 NOT NULL,
    vendor_count INTEGER DEFAULT 0 NOT NULL,
    voucher_count INTEGER DEFAULT 0 NOT NULL,
    has_image INTEGER DEFAULT 0 NOT NULL,
    source_file TEXT,
    raw_data JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 3. Risk Scores Deterministic Intelligence Table
CREATE TABLE IF NOT EXISTS risk_scores (
    work_code TEXT PRIMARY KEY REFERENCES projects(work_code) ON DELETE CASCADE,
    state TEXT NOT NULL,
    district TEXT NOT NULL,
    overall_risk_score NUMERIC(6, 2) NOT NULL,
    risk_level TEXT NOT NULL,
    confidence NUMERIC(6, 2) NOT NULL,
    cost_anomaly_score NUMERIC(6, 2) NOT NULL,
    duplicate_score NUMERIC(6, 2) NOT NULL,
    progress_gap_score NUMERIC(6, 2) NOT NULL,
    geographic_score NUMERIC(6, 2) NOT NULL,
    data_quality_score NUMERIC(6, 2) DEFAULT 0.00,
    coverage_pct NUMERIC(6, 2) DEFAULT 0.00,
    cost_zscore NUMERIC(10, 4) DEFAULT 0.00,
    cost_mad_score NUMERIC(10, 4) DEFAULT 0.00,
    comparison_group_size INTEGER DEFAULT 0,
    explanation_json JSONB,
    recommendation TEXT,
    model_version TEXT DEFAULT 'risk-engine-v1.0' NOT NULL,
    calculated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 4. Expenditure Vouchers Transactional Table
CREATE TABLE IF NOT EXISTS expenditure_vouchers (
    id SERIAL PRIMARY KEY,
    work_code TEXT NOT NULL REFERENCES projects(work_code) ON DELETE CASCADE,
    state TEXT NOT NULL,
    ida_name TEXT,
    mp_name TEXT,
    constituency TEXT,
    expenditure_date DATE,
    vendor_name TEXT,
    payment_status TEXT,
    disbursed_amount NUMERIC(18, 2) DEFAULT 0.00 NOT NULL,
    house TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 5. Parliamentarian Intelligence Table (MPs)
CREATE TABLE IF NOT EXISTS mps (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    house TEXT NOT NULL,
    state TEXT NOT NULL,
    constituency TEXT,
    mp_type TEXT,
    allocated_limit NUMERIC(18, 2) DEFAULT 0.00 NOT NULL,
    calamity_consent_amount NUMERIC(18, 2) DEFAULT 0.00 NOT NULL,
    total_recommended_works INTEGER DEFAULT 0 NOT NULL,
    total_sanctioned_works INTEGER DEFAULT 0 NOT NULL,
    total_completed_works INTEGER DEFAULT 0 NOT NULL,
    total_sanctioned_amount NUMERIC(18, 2) DEFAULT 0.00 NOT NULL,
    total_expenditure_amount NUMERIC(18, 2) DEFAULT 0.00 NOT NULL,
    avg_risk_score NUMERIC(6, 2) DEFAULT 0.00 NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 6. Comparable Projects Graph Relationship Table
CREATE TABLE IF NOT EXISTS comparable_projects (
    id SERIAL PRIMARY KEY,
    target_work_code TEXT NOT NULL REFERENCES projects(work_code) ON DELETE CASCADE,
    comparable_work_code TEXT NOT NULL REFERENCES projects(work_code) ON DELETE CASCADE,
    similarity_score NUMERIC(6, 2) NOT NULL,
    similarity_type TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT unique_comp_pair UNIQUE (target_work_code, comparable_work_code)
);

-- 7. Alerts Management Center Table
CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    work_code TEXT NOT NULL REFERENCES projects(work_code) ON DELETE CASCADE,
    alert_type TEXT NOT NULL,
    title TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT DEFAULT 'OPEN' NOT NULL,
    state TEXT NOT NULL,
    district TEXT NOT NULL,
    evidence TEXT NOT NULL,
    impact TEXT NOT NULL,
    action_recommendation TEXT NOT NULL,
    assigned_to TEXT,
    priority_score NUMERIC(6, 2) DEFAULT 0.00,
    acknowledged_by TEXT,
    acknowledged_at TIMESTAMP WITHOUT TIME ZONE,
    resolved_by TEXT,
    resolved_at TIMESTAMP WITHOUT TIME ZONE,
    resolution_notes TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 8. Users & Role-Based Access Control Table (Argon2id)
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL,
    department TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 9. Immutable Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    username TEXT NOT NULL,
    user_role TEXT NOT NULL,
    action TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    previous_state TEXT,
    new_state TEXT,
    notes TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 10. Data Sources Registry Table
CREATE TABLE IF NOT EXISTS data_sources (
    id SERIAL PRIMARY KEY,
    source_name TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    row_count INTEGER DEFAULT 0 NOT NULL,
    file_size_bytes BIGINT DEFAULT 0 NOT NULL,
    sha256_hash TEXT NOT NULL,
    ingested_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 11. Ingestion Runs Log Table
CREATE TABLE IF NOT EXISTS ingestion_runs (
    id SERIAL PRIMARY KEY,
    run_id TEXT UNIQUE NOT NULL,
    total_files INTEGER DEFAULT 0 NOT NULL,
    total_raw_rows INTEGER DEFAULT 0 NOT NULL,
    total_canonical_projects INTEGER DEFAULT 0 NOT NULL,
    total_vouchers INTEGER DEFAULT 0 NOT NULL,
    status TEXT NOT NULL,
    duration_seconds NUMERIC(10, 2) DEFAULT 0.00 NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 12. Location Mappings Table
CREATE TABLE IF NOT EXISTS location_mappings (
    id SERIAL PRIMARY KEY,
    raw_state TEXT NOT NULL,
    canonical_state TEXT NOT NULL,
    raw_district TEXT,
    canonical_district TEXT,
    state_code TEXT NOT NULL
);

-- 13. Data Quality Issues Registry Table
CREATE TABLE IF NOT EXISTS data_quality_issues (
    id SERIAL PRIMARY KEY,
    issue_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    file_name TEXT NOT NULL,
    source_identifier TEXT NOT NULL,
    field_name TEXT NOT NULL,
    invalid_value TEXT,
    description TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 14. Durable Background Jobs Table
CREATE TABLE IF NOT EXISTS background_jobs (
    job_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    job_type TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    started_at TIMESTAMP WITHOUT TIME ZONE,
    completed_at TIMESTAMP WITHOUT TIME ZONE,
    failed_at TIMESTAMP WITHOUT TIME ZONE,
    attempt INTEGER DEFAULT 1 NOT NULL,
    result_json JSONB,
    error_message TEXT
);

-- ==============================================================================
-- 15. High-Performance B-Tree & Trigram Indexes
-- ==============================================================================

-- Projects Indexes
CREATE INDEX IF NOT EXISTS idx_projects_state ON projects(state);
CREATE INDEX IF NOT EXISTS idx_projects_district ON projects(district);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_category ON projects(category);
CREATE INDEX IF NOT EXISTS idx_projects_financial_year ON projects(financial_year);
CREATE INDEX IF NOT EXISTS idx_projects_mp_name ON projects(mp_name);
CREATE INDEX IF NOT EXISTS idx_projects_state_district ON projects(state, district);
CREATE INDEX IF NOT EXISTS idx_projects_work_code ON projects(work_code);
CREATE INDEX IF NOT EXISTS idx_projects_sanction_date ON projects(sanction_date DESC);

-- Risk Scores Indexes
CREATE INDEX IF NOT EXISTS idx_risk_scores_state ON risk_scores(state);
CREATE INDEX IF NOT EXISTS idx_risk_scores_district ON risk_scores(district);
CREATE INDEX IF NOT EXISTS idx_risk_scores_level ON risk_scores(risk_level);
CREATE INDEX IF NOT EXISTS idx_risk_scores_overall ON risk_scores(overall_risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_risk_scores_cost_anomaly ON risk_scores(cost_anomaly_score DESC);
CREATE INDEX IF NOT EXISTS idx_risk_scores_duplicate ON risk_scores(duplicate_score DESC);

-- Expenditure Vouchers Indexes
CREATE INDEX IF NOT EXISTS idx_vouchers_work_code ON expenditure_vouchers(work_code);
CREATE INDEX IF NOT EXISTS idx_vouchers_date ON expenditure_vouchers(expenditure_date DESC);

-- Comparable Projects Indexes
CREATE INDEX IF NOT EXISTS idx_comparable_target ON comparable_projects(target_work_code);
CREATE INDEX IF NOT EXISTS idx_comparable_comp ON comparable_projects(comparable_work_code);
CREATE INDEX IF NOT EXISTS idx_comparable_score ON comparable_projects(similarity_score DESC);

-- Alerts Indexes
CREATE INDEX IF NOT EXISTS idx_alerts_work_code ON alerts(work_code);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_state ON alerts(state);
CREATE INDEX IF NOT EXISTS idx_alerts_district ON alerts(district);
CREATE INDEX IF NOT EXISTS idx_alerts_priority ON alerts(priority_score DESC);

-- Audit Logs Indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_target ON audit_logs(target_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at DESC);

-- Background Jobs Indexes
CREATE INDEX IF NOT EXISTS idx_background_jobs_status ON background_jobs(status);
CREATE INDEX IF NOT EXISTS idx_background_jobs_type ON background_jobs(job_type);
