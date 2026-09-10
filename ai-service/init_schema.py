import os
import glob
import csv
import re
import json
import sqlite3
import datetime
import math
from collections import defaultdict, Counter
import numpy as np

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.getenv("DATA_DIR", os.path.join(_project_root, "DATA"))
DB_PATH = os.getenv("SQLITE_PATH", os.path.join(_project_root, "mplad.db"))

def clean_val(val):
    if val is None: return ""
    return str(val).strip()

def parse_num(val):
    if not val: return 0.0
    c = str(val).replace("₹", "").replace(",", "").replace(" ", "").strip()
    try: return float(c)
    except: return 0.0

def parse_date(date_str):
    if not date_str: return None
    date_str = clean_val(date_str)
    if date_str in ["NaN-NaN", "NA", "N/A", "-", ""]: return None
    
    # Common format: 08-Jul-2024, 05-Sep-2024
    for fmt in ["%d-%b-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
        try:
            return datetime.datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except:
            continue
    return None

def clean_work_id(val):
    if not val: return None
    val = val.strip().replace("\t", "").replace(" ", "")
    if val.startswith("WS/"):
        return val
    m = re.search(r"(WS/[A-Za-z0-9_-]+/\d{4}-\d{4}/\d+)", val)
    if m:
        return m.group(1)
    return val

def extract_work_code_and_title(work_str):
    if not work_str: return None, ""
    work_str = work_str.strip().replace("\t", " ")
    m = re.match(r"^(WS/\s*[A-Za-z0-9_-]+/\d{4}-\d{4}/\d+)", work_str)
    if m:
        code = clean_work_id(m.group(1))
        title = work_str[m.end():].lstrip(" -").strip()
        return code, title
    m2 = re.match(r"^([A-Z0-9_/ -]+?)-(.*)$", work_str)
    if m2 and "/" in m2.group(1):
        code = clean_work_id(m2.group(1))
        return code, m2.group(2).strip()
    return clean_work_id(work_str), ""

def parse_ida(ida_str):
    if not ida_str: return "", ""
    ida_str = ida_str.strip()
    m = re.match(r"^([^(]+)\((.+)\)$", ida_str)
    if m:
        district = m.group(1).strip()
        agency = m.group(2).strip()
        return district, agency
    return ida_str, ""

def init_db(conn):
    cur = conn.cursor()
    
    # 1. Projects Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        work_code TEXT UNIQUE,
        house TEXT,
        mp_code TEXT,
        mp_name TEXT,
        mp_type TEXT,
        state TEXT,
        district TEXT,
        constituency TEXT,
        ida_name TEXT,
        category TEXT,
        work_type TEXT,
        description TEXT,
        status TEXT,
        recommended_date TEXT,
        sanction_date TEXT,
        completion_date TEXT,
        financial_year TEXT,
        recommended_amount REAL DEFAULT 0.0,
        sanctioned_amount REAL DEFAULT 0.0,
        disbursed_amount REAL DEFAULT 0.0,
        expenditure_amount REAL DEFAULT 0.0,
        utilization_pct REAL DEFAULT 0.0,
        vendor_count INTEGER DEFAULT 0,
        voucher_count INTEGER DEFAULT 0,
        has_image INTEGER DEFAULT 0,
        created_at TEXT,
        raw_data TEXT
    );
    """)
    
    # 2. MPs Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS mps (
        id TEXT PRIMARY KEY,
        name TEXT,
        house TEXT,
        state TEXT,
        constituency TEXT,
        mp_type TEXT,
        allocated_limit REAL DEFAULT 0.0,
        calamity_consent_amount REAL DEFAULT 0.0,
        total_recommended_works INTEGER DEFAULT 0,
        total_sanctioned_works INTEGER DEFAULT 0,
        total_completed_works INTEGER DEFAULT 0,
        total_sanctioned_amount REAL DEFAULT 0.0,
        total_expenditure_amount REAL DEFAULT 0.0,
        avg_risk_score REAL DEFAULT 0.0,
        created_at TEXT
    );
    """)
    
    # 3. Expenditure Vouchers Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS expenditure_vouchers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_code TEXT,
        state TEXT,
        ida_name TEXT,
        mp_name TEXT,
        constituency TEXT,
        expenditure_date TEXT,
        vendor_name TEXT,
        payment_status TEXT,
        disbursed_amount REAL DEFAULT 0.0,
        house TEXT,
        created_at TEXT
    );
    """)
    
    # 4. Risk Scores Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS risk_scores (
        work_code TEXT PRIMARY KEY,
        overall_risk_score REAL DEFAULT 0.0,
        risk_level TEXT,
        confidence REAL DEFAULT 0.0,
        cost_anomaly_score REAL DEFAULT 0.0,
        duplicate_score REAL DEFAULT 0.0,
        progress_gap_score REAL DEFAULT 0.0,
        geographic_score REAL DEFAULT 0.0,
        data_quality_score REAL DEFAULT 0.0,
        coverage_pct REAL DEFAULT 100.0,
        cost_zscore REAL DEFAULT 0.0,
        cost_mad_score REAL DEFAULT 0.0,
        comparison_group_size INTEGER DEFAULT 0,
        explanation_json TEXT,
        recommendation TEXT,
        model_version TEXT,
        calculated_at TEXT
    );
    """)
    
    # 5. Comparable Projects Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS comparable_projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_work_code TEXT,
        comparable_work_code TEXT,
        similarity_score REAL,
        similarity_type TEXT,
        reason TEXT
    );
    """)
    
    # 6. Alerts Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id TEXT PRIMARY KEY,
        work_code TEXT,
        alert_type TEXT,
        title TEXT,
        severity TEXT,
        status TEXT DEFAULT 'OPEN',
        state TEXT,
        district TEXT,
        evidence TEXT,
        impact TEXT,
        action_recommendation TEXT,
        acknowledged_by TEXT,
        acknowledged_at TEXT,
        resolved_by TEXT,
        resolved_at TEXT,
        resolution_notes TEXT,
        created_at TEXT
    );
    """)
    
    # 7. Data Quality Issues Registry
    cur.execute("""
    CREATE TABLE IF NOT EXISTS data_quality_issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_type TEXT,
        severity TEXT,
        file_name TEXT,
        source_identifier TEXT,
        field_name TEXT,
        invalid_value TEXT,
        description TEXT,
        created_at TEXT
    );
    """)
    
    # 8. Audit Logs Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT,
        user_role TEXT,
        action TEXT,
        target_type TEXT,
        target_id TEXT,
        details TEXT,
        ip_address TEXT,
        created_at TEXT
    );
    """)
    
    # 9. Users Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE,
        password_hash TEXT,
        full_name TEXT,
        email TEXT,
        role TEXT,
        department TEXT,
        created_at TEXT
    );
    """)
    
    # Create Indices for Blazing-Fast Performance
    cur.execute("CREATE INDEX IF NOT EXISTS idx_proj_state ON projects(state);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_proj_district ON projects(district);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_proj_status ON projects(status);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_proj_mp ON projects(mp_name);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_proj_fy ON projects(financial_year);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_vouchers_wc ON expenditure_vouchers(work_code);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_vouchers_vendor ON expenditure_vouchers(vendor_name);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_wc ON alerts(work_code);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_risk_score ON risk_scores(overall_risk_score);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_comp_target ON comparable_projects(target_work_code);")
    
    conn.commit()
    print("Database tables & indexes initialized successfully.")

if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        try: os.remove(DB_PATH)
        except: pass
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    conn.close()
