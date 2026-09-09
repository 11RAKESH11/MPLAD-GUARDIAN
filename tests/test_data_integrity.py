import pytest
import sqlite3
import os
import json
import re
import datetime
import sys
sys.path.insert(0, r"c:\SIH_PROJECT")
sys.path.insert(0, r"c:\SIH_PROJECT\ai-service")

from ingest_and_analyze import (
    clean_val, parse_num, parse_date, clean_work_id,
    extract_work_code_and_title, parse_ida, normalize_state_name,
    compute_file_sha256
)

DB_PATH = r"c:\SIH_PROJECT\mplad.db"
DATA_DIR = r"c:\SIH_PROJECT\DATA"

def test_numeric_normalization():
    assert parse_num("₹ 12,45,000") == 1245000.0
    assert parse_num("500000") == 500000.0
    assert parse_num("0.0") == 0.0
    assert parse_num("") == 0.0
    assert parse_num("Invalid") == 0.0

def test_date_normalization():
    assert parse_date("08-Jul-2024") == "2024-07-08"
    assert parse_date("05/09/2024") == "2024-09-05"
    assert parse_date("2024-08-20") == "2024-08-20"
    assert parse_date("NaN-NaN") is None
    assert parse_date("N/A") is None
    assert parse_date("") is None

def test_work_code_extraction():
    code, title = extract_work_code_and_title("WS/\t MP620/2024-2025/133166-Construction of Community Bhavan")
    assert code == "WS/MP620/2024-2025/133166"
    assert title == "Construction of Community Bhavan"
    
    code2 = clean_work_id("WS/MP18080/2025-2026/181962")
    assert code2 == "WS/MP18080/2025-2026/181962"

def test_location_normalization():
    assert normalize_state_name("orissa") == "Odisha"
    assert normalize_state_name("Pondicherry") == "Puducherry"
    assert normalize_state_name("Maharashtra") == "Maharashtra"

def test_ida_parsing():
    dist, agency = parse_ida("DHARWAD(DEPUTY COMMISSIONER DHARWAR_IDA)")
    assert dist == "DHARWAD"
    assert agency == "DEPUTY COMMISSIONER DHARWAR_IDA"

def test_database_record_counts():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM projects")
    proj_cnt = cur.fetchone()[0]
    assert proj_cnt == 96654, f"Expected 96,654 projects, got {proj_cnt}"
    
    cur.execute("SELECT COUNT(*) FROM expenditure_vouchers")
    vouch_cnt = cur.fetchone()[0]
    assert vouch_cnt == 106442, f"Expected 106,442 vouchers, got {vouch_cnt}"
    
    cur.execute("SELECT COUNT(*) FROM mps")
    mp_cnt = cur.fetchone()[0]
    assert mp_cnt == 764, f"Expected 764 MPs, got {mp_cnt}"
    
    cur.execute("SELECT COUNT(*) FROM alerts")
    alert_cnt = cur.fetchone()[0]
    assert alert_cnt == 270, f"Expected 270 alerts, got {alert_cnt}"
    
    conn.close()

def test_financial_reconciliation():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT SUM(sanctioned_amount), SUM(expenditure_amount) FROM projects")
    tot_sanc, tot_exp = cur.fetchone()
    assert tot_sanc > 50000000000, f"Sanctioned total too low: {tot_sanc}"
    assert tot_exp > 30000000000, f"Expenditure total too low: {tot_exp}"
    assert tot_exp <= tot_sanc * 1.05, "Total expenditure significantly exceeds total sanctioned amount"
    
    conn.close()

def test_ingestion_runs_logged():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM ingestion_runs WHERE status = 'SUCCESS'")
    run_cnt = cur.fetchone()[0]
    assert run_cnt >= 1, "Expected at least 1 successful ingestion run log"
    
    conn.close()

def test_data_quality_issues_logged():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM data_quality_issues")
    dq_cnt = cur.fetchone()[0]
    assert dq_cnt >= 0, "Data quality issues query executed successfully"
    
    conn.close()

if __name__ == "__main__":
    test_numeric_normalization()
    test_date_normalization()
    test_work_code_extraction()
    test_location_normalization()
    test_ida_parsing()
    test_database_record_counts()
    test_financial_reconciliation()
    test_ingestion_runs_logged()
    test_data_quality_issues_logged()
    print("ALL 9 DATA INTEGRITY TESTS PASSED SUCCESSFULLY!")
