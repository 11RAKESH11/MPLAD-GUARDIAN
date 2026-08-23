import sqlite3
import json

conn = sqlite3.connect("mplad.db")
cur = conn.cursor()

p_count = cur.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
v_count = cur.execute("SELECT COUNT(*) FROM expenditure_vouchers").fetchone()[0]
m_count = cur.execute("SELECT COUNT(*) FROM mps").fetchone()[0]
r_count = cur.execute("SELECT COUNT(*) FROM risk_scores").fetchone()[0]
a_count = cur.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]

print(f"Projects: {p_count:,}")
print(f"Vouchers: {v_count:,}")
print(f"MPs: {m_count:,}")
print(f"Risk Scores: {r_count:,}")
print(f"Alerts: {a_count:,}")

# Sample risk record
row = cur.execute("""
SELECT p.work_code, p.work_type, p.state, p.district, p.sanctioned_amount, p.status, 
       r.overall_risk_score, r.risk_level, r.confidence, r.explanation_json
FROM projects p 
JOIN risk_scores r ON p.work_code = r.work_code 
WHERE r.risk_level IN ('CRITICAL', 'HIGH')
LIMIT 1
""").fetchone()

if row:
    print("\nSAMPLE HIGH RISK PROJECT:")
    print(f"  Code: {row[0]}")
    print(f"  Title: {row[1]}")
    print(f"  State/District: {row[2]} / {row[3]}")
    print(f"  Sanctioned: ₹{row[4]:,.0f} | Status: {row[5]}")
    print(f"  Risk: {row[6]} ({row[7]}) | Confidence: {row[8]}%")
    exp = json.loads(row[9])
    print(f"  Why Flagged: {exp['why_flagged']}")
    print(f"  Recommendation: {exp['recommendation']}")

conn.close()
