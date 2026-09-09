import sqlite3
import os
import json

conn = sqlite3.connect('mplad.db')
cursor = conn.cursor()
cursor.execute('SELECT sqlite_version()')
sqlite_ver = cursor.fetchone()[0]

cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
tables_info = cursor.fetchall()

counts = {}
for name, sql in tables_info:
    cursor.execute(f'SELECT COUNT(*) FROM "{name}"')
    counts[name] = cursor.fetchone()[0]

cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
indexes_info = cursor.fetchall()

financial_stats = {}
cursor.execute("""
SELECT 
    SUM(sanctioned_amount), 
    SUM(recommended_amount), 
    SUM(expenditure_amount), 
    SUM(disbursed_amount) 
FROM projects
""")
p_fin = cursor.fetchone()
financial_stats['projects'] = {
    'sanctioned_amount': p_fin[0],
    'recommended_amount': p_fin[1],
    'expenditure_amount': p_fin[2],
    'disbursed_amount': p_fin[3]
}

cursor.execute("SELECT SUM(disbursed_amount) FROM expenditure_vouchers")
financial_stats['vouchers_disbursed_amount'] = cursor.fetchone()[0]

output = {
    'sqlite_version': sqlite_ver,
    'db_file_size_bytes': os.path.getsize('mplad.db'),
    'tables': counts,
    'indexes_count': len(indexes_info),
    'financial_stats': financial_stats
}

print(json.dumps(output, indent=2))
