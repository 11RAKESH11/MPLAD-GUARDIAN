import sqlite3
import time

DB_PATH = r"c:\SIH_PROJECT\mplad.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("Applying SQLite Performance Optimizations & PRAGMAs...")
t0 = time.time()

# 1. Enable WAL Mode & High-Performance Cache
cur.execute("PRAGMA journal_mode = WAL;")
cur.execute("PRAGMA synchronous = NORMAL;")
cur.execute("PRAGMA cache_size = -64000;") # 64MB cache
cur.execute("PRAGMA temp_store = MEMORY;")
cur.execute("PRAGMA mmap_size = 30000000000;")

# 2. Add Critical Performance Indices
indices = [
    ("idx_risk_cost_anom", "CREATE INDEX IF NOT EXISTS idx_risk_cost_anom ON risk_scores(cost_anomaly_score);"),
    ("idx_risk_dup_score", "CREATE INDEX IF NOT EXISTS idx_risk_dup_score ON risk_scores(duplicate_score);"),
    ("idx_risk_prog_gap", "CREATE INDEX IF NOT EXISTS idx_risk_prog_gap ON risk_scores(progress_gap_score);"),
    ("idx_risk_level", "CREATE INDEX IF NOT EXISTS idx_risk_level ON risk_scores(risk_level);"),
    ("idx_proj_category", "CREATE INDEX IF NOT EXISTS idx_proj_category ON projects(category);"),
    ("idx_proj_state_dist", "CREATE INDEX IF NOT EXISTS idx_proj_state_dist ON projects(state, district);"),
    ("idx_proj_sanc_amt", "CREATE INDEX IF NOT EXISTS idx_proj_sanc_amt ON projects(sanctioned_amount);"),
    ("idx_comp_sim_score", "CREATE INDEX IF NOT EXISTS idx_comp_sim_score ON comparable_projects(similarity_score);"),
    ("idx_risk_scores_work_code", "CREATE INDEX IF NOT EXISTS idx_risk_scores_work_code ON risk_scores(work_code);"),
    ("idx_vouchers_vendor_name", "CREATE INDEX IF NOT EXISTS idx_vouchers_vendor_name ON expenditure_vouchers(vendor_name);"),
    ("idx_alerts_status_priority", "CREATE INDEX IF NOT EXISTS idx_alerts_status_priority ON alerts(status, priority_score DESC);"),
    ("idx_projects_fy_covering", "CREATE INDEX IF NOT EXISTS idx_projects_fy_covering ON projects(financial_year, sanctioned_amount, expenditure_amount, status);"),
    ("idx_projects_state_covering", "CREATE INDEX IF NOT EXISTS idx_projects_state_covering ON projects(state, sanctioned_amount, expenditure_amount, status);"),
    ("idx_projects_financial_covering", "CREATE INDEX IF NOT EXISTS idx_projects_financial_covering ON projects(recommended_amount, sanctioned_amount, disbursed_amount, expenditure_amount);"),
    ("idx_risk_scores_level_conf", "CREATE INDEX IF NOT EXISTS idx_risk_scores_level_conf ON risk_scores(risk_level, confidence);")
]

for name, sql in indices:
    t_idx0 = time.time()
    cur.execute(sql)
    print(f"  Created {name} in {(time.time() - t_idx0)*1000:.1f} ms")

conn.commit()
conn.close()

print(f"Database optimization complete in {(time.time() - t0)*1000:.1f} ms!")
