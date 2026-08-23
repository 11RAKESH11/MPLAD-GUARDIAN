import os
import glob
import csv
import json
from collections import defaultdict

data_dir = r"c:\SIH_PROJECT\DATA"
audit_results = {}

for house in ["lok sabha", "rajya sabha"]:
    house_dir = os.path.join(data_dir, house)
    audit_results[house] = {}
    csv_files = glob.glob(os.path.join(house_dir, "*.csv"))
    
    for fpath in csv_files:
        fname = os.path.basename(fpath)
        size_bytes = os.path.getsize(fpath)
        
        # Try reading file with different encodings
        encoding = 'utf-8'
        lines_sample = []
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                reader = csv.reader(f)
                headers = next(reader, None)
                row_count = 0
                sample_rows = []
                null_counts = defaultdict(int)
                for r in reader:
                    row_count += 1
                    if len(sample_rows) < 5:
                        sample_rows.append(r)
                    for idx, val in enumerate(r):
                        col = headers[idx] if headers and idx < len(headers) else f"col_{idx}"
                        if not val or val.strip() == '' or val.strip().lower() in ['null', 'na', 'n/a', 'none', '-']:
                            null_counts[col] += 1
                            
            audit_results[house][fname] = {
                "file_path": fpath,
                "size_bytes": size_bytes,
                "size_mb": round(size_bytes / (1024 * 1024), 2),
                "row_count": row_count,
                "headers": headers,
                "null_counts": dict(null_counts),
                "sample_rows": sample_rows
            }
        except Exception as e:
            audit_results[house][fname] = {
                "error": str(e)
            }

with open(r"c:\SIH_PROJECT\audit_raw.json", "w", encoding="utf-8") as out:
    json.dump(audit_results, out, indent=2, ensure_ascii=False)

print("Raw audit complete. Processed files summary:")
for house in audit_results:
    print(f"\n--- {house.upper()} ---")
    for fname, info in audit_results[house].items():
        if "error" in info:
            print(f"  {fname}: ERROR {info['error']}")
        else:
            print(f"  {fname}: {info['row_count']:,} rows, {len(info['headers'])} cols, {info['size_mb']} MB")
            print(f"    Headers: {info['headers']}")
