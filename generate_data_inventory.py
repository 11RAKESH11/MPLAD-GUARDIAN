import os
import glob
import csv
import json
import hashlib
import re
from collections import Counter, defaultdict

DATA_DIR = r"c:\SIH_PROJECT\DATA"
OUTPUT_FILE = r"c:\SIH_PROJECT\data_inventory.json"

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def detect_date(val):
    if not val:
        return None
    val = str(val).strip()
    if val in ["NaN-NaN", "NA", "N/A", "-", "", "None"]:
        return None
    for fmt in ["%d-%b-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
        try:
            import datetime
            return datetime.datetime.strptime(val, fmt).strftime("%Y-%m-%d")
        except:
            continue
    return None

def inspect_file(filepath):
    rel_path = os.path.relpath(filepath, DATA_DIR).replace("\\", "/")
    file_size = os.path.getsize(filepath)
    sha256_hash = compute_sha256(filepath)
    
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            header = []
            
        rows = list(reader)
        
    row_count = len(rows)
    col_count = len(header)
    
    # Analyze columns and missing values
    missing_summary = {col: 0 for col in header}
    states = set()
    districts = set()
    financial_years = set()
    dates = []
    
    # Sample hash (first 5 rows)
    sample_str = json.dumps(rows[:5])
    sample_hash = hashlib.sha256(sample_str.encode("utf-8")).hexdigest()
    
    for row in rows:
        for idx, col in enumerate(header):
            val = row[idx].strip() if idx < len(row) else ""
            if not val or val in ["NA", "N/A", "NaN", "NaN-NaN", "-", "None", "null"]:
                missing_summary[col] += 1
            
            # State
            if "state" in col.lower():
                if val and val not in ["Total", ""]:
                    states.add(val)
            
            # District / IDA
            if "ida" in col.lower() or "district" in col.lower():
                m = re.match(r"^([^(]+)\((.+)\)$", val)
                if m:
                    districts.add(m.group(1).strip())
                elif val:
                    districts.add(val)
                    
            # Financial year
            fy_match = re.search(r"(20\d{2}-20\d{2}|\d{4}-\d{4})", val)
            if fy_match:
                financial_years.add(fy_match.group(1))
                
            # Date fields
            if "date" in col.lower():
                d = detect_date(val)
                if d:
                    dates.append(d)
                    
    # Missing summary with percentage
    missing_formatted = {}
    for col, count in missing_summary.items():
        pct = round((count / row_count * 100), 2) if row_count > 0 else 0.0
        missing_formatted[col] = {
            "missing_count": count,
            "missing_percentage": pct
        }
        
    date_range = {
        "earliest": min(dates) if dates else None,
        "latest": max(dates) if dates else None,
        "valid_dates_count": len(dates)
    }
    
    return {
        "filename": rel_path,
        "file_size_bytes": file_size,
        "file_size_mb": round(file_size / (1024 * 1024), 3),
        "sha256": sha256_hash,
        "row_count": row_count,
        "column_count": col_count,
        "columns": header,
        "encoding": "utf-8",
        "delimiter": ",",
        "sample_hash": sample_hash,
        "date_range": date_range,
        "financial_years": sorted(list(financial_years)),
        "state_count": len(states),
        "district_count": len(districts),
        "states_sample": sorted(list(states))[:5],
        "missing_value_summary": missing_formatted
    }

def main():
    files = sorted(glob.glob(os.path.join(DATA_DIR, "**", "*.csv"), recursive=True))
    inventory = {
        "dataset_name": "MPLADS Official Operational Dataset (MoSPI)",
        "inventory_generated_at": "2026-08-24T00:30:00Z",
        "total_files": len(files),
        "total_raw_rows": 0,
        "total_size_bytes": 0,
        "files": []
    }
    
    for f in files:
        res = inspect_file(f)
        inventory["files"].append(res)
        inventory["total_raw_rows"] += res["row_count"]
        inventory["total_size_bytes"] += res["file_size_bytes"]
        
    inventory["total_size_mb"] = round(inventory["total_size_bytes"] / (1024 * 1024), 2)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        json.dump(inventory, out, indent=2)
        
    print(f"Generated {OUTPUT_FILE} with {len(files)} files and {inventory['total_raw_rows']:,} rows.")

if __name__ == "__main__":
    main()
