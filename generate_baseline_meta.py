import sqlite3
import json
import os

conn = sqlite3.connect('mplad.db')
c = conn.cursor()

c.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
tables = c.fetchall()

c.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
indexes = c.fetchall()

table_stats = {}
for name, sql in tables:
    c.execute(f'SELECT COUNT(*) FROM "{name}"')
    count = c.fetchone()[0]
    
    c.execute(f'PRAGMA table_info("{name}")')
    columns = [{'cid': col[0], 'name': col[1], 'type': col[2], 'notnull': col[3], 'dflt_value': col[4], 'pk': col[5]} for col in c.fetchall()]
    
    table_stats[name] = {
        'row_count': count,
        'column_count': len(columns),
        'columns': columns,
        'create_sql': sql
    }

index_list = []
for name, sql in indexes:
    index_list.append({'name': name, 'sql': sql})

baseline = {
    'sqlite_version': '3.38.4',
    'database_file': 'mplad.db',
    'file_size_bytes': os.path.getsize('mplad.db'),
    'file_size_mb': round(os.path.getsize('mplad.db') / (1024 * 1024), 2),
    'tables': table_stats,
    'indexes': index_list
}

with open('baseline_data.json', 'w', encoding='utf-8') as f:
    json.dump(baseline, f, indent=2)

print("Generated baseline_data.json successfully.")
