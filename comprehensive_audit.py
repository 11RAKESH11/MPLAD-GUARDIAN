import os
import glob
import csv
import json
import re
from collections import defaultdict, Counter

data_dir = r"c:\SIH_PROJECT\DATA"
audit_results = {
    "summary": {
        "total_files": 0,
        "total_rows": 0,
        "total_size_bytes": 0,
        "total_size_mb": 0,
    },
    "houses": {}
}

def clean_val(val):
    if val is None:
        return ""
    return str(val).strip()

def is_null(val):
    cleaned = clean_val(val).lower()
    return cleaned == "" or cleaned in ["null", "na", "n/a", "none", "-", "nil", "nan"]

def parse_num(val):
    cleaned = clean_val(val).replace("₹", "").replace(",", "").replace(" ", "")
    try:
        return float(cleaned)
    except:
        return None

def infer_type(sample_values):
    non_nulls = [v for v in sample_values if not is_null(v)]
    if not non_nulls:
        return "UNKNOWN (ALL_NULL)"
    
    num_count = 0
    date_count = 0
    
    date_patterns = [
        r"^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$",
        r"^\d{4}[/-]\d{1,2}[/-]\d{1,2}$",
        r"^\d{1,2}-[a-zA-Z]{3}-\d{2,4}$",
        r"^\d{4}-\d{2}$", # Financial year like 2023-24
    ]
    
    for v in non_nulls:
        if parse_num(v) is not None:
            num_count += 1
        elif any(re.match(p, v.strip()) for p in date_patterns):
            date_count += 1
            
    total = len(non_nulls)
    if num_count / total > 0.8:
        return "NUMERIC"
    elif date_count / total > 0.8:
        return "DATE_OR_YEAR"
    else:
        return "TEXT"

total_files = 0
total_rows = 0
total_size = 0

for house in ["lok sabha", "rajya sabha"]:
    house_dir = os.path.join(data_dir, house)
    audit_results["houses"][house] = {}
    csv_files = glob.glob(os.path.join(house_dir, "*.csv"))
    
    for fpath in csv_files:
        fname = os.path.basename(fpath)
        size_bytes = os.path.getsize(fpath)
        total_files += 1
        total_size += size_bytes
        
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.reader(f)
            try:
                headers = next(reader, None)
            except Exception as e:
                headers = []
            
            if not headers:
                continue
                
            headers = [h.strip() for h in headers]
            row_count = 0
            null_counts = defaultdict(int)
            val_samples = defaultdict(list)
            num_stats = defaultdict(lambda: {"min": float('inf'), "max": float('-inf'), "sum": 0.0, "count": 0})
            cat_counts = defaultdict(Counter)
            duplicate_check = set()
            exact_duplicate_rows = 0
            
            for row in reader:
                row_count += 1
                row_tuple = tuple(row)
                if row_tuple in duplicate_check:
                    exact_duplicate_rows += 1
                else:
                    duplicate_check.add(row_tuple)
                    
                for idx, val in enumerate(row):
                    col = headers[idx] if idx < len(headers) else f"col_{idx}"
                    cleaned = clean_val(val)
                    if is_null(cleaned):
                        null_counts[col] += 1
                    else:
                        if len(val_samples[col]) < 20:
                            val_samples[col].append(cleaned)
                            
                        # If numeric column candidate
                        p_val = parse_num(cleaned)
                        if p_val is not None:
                            ns = num_stats[col]
                            ns["count"] += 1
                            ns["sum"] += p_val
                            if p_val < ns["min"]: ns["min"] = p_val
                            if p_val > ns["max"]: ns["max"] = p_val
                        
                        if len(cat_counts[col]) < 50:
                            cat_counts[col][cleaned] += 1

            total_rows += row_count
            
            # Column analysis
            columns_audit = {}
            for idx, col in enumerate(headers):
                samples = val_samples[col]
                inferred = infer_type(samples)
                n_count = null_counts[col]
                null_pct = round((n_count / row_count * 100), 2) if row_count > 0 else 0
                
                col_info = {
                    "index": idx,
                    "name": col,
                    "inferred_type": inferred,
                    "null_count": n_count,
                    "null_percentage": null_pct,
                    "sample_values": samples[:5]
                }
                
                if col in num_stats and num_stats[col]["count"] > 0:
                    ns = num_stats[col]
                    col_info["numeric_stats"] = {
                        "count": ns["count"],
                        "min": round(ns["min"], 2),
                        "max": round(ns["max"], 2),
                        "mean": round(ns["sum"] / ns["count"], 2),
                        "sum": round(ns["sum"], 2)
                    }
                
                if len(cat_counts[col]) <= 20 and len(cat_counts[col]) > 0:
                    col_info["top_categories"] = dict(cat_counts[col].most_common(10))
                    
                columns_audit[col] = col_info
                
            # Classify record granularity
            # Check if project-level or aggregate
            is_project_level = any("work" in col.lower() or "project" in col.lower() or "recommend" in col.lower() or "sanction" in col.lower() for col in headers)
            is_mp_summary = any("allocated" in fname.lower() or "calamity" in fname.lower() for fname in [fname])
            
            audit_results["houses"][house][fname] = {
                "file_name": fname,
                "file_path": fpath,
                "size_bytes": size_bytes,
                "size_mb": round(size_bytes / (1024 * 1024), 2),
                "row_count": row_count,
                "column_count": len(headers),
                "exact_duplicate_rows": exact_duplicate_rows,
                "headers": headers,
                "columns": columns_audit,
                "source_classification": "MP_AGGREGATE" if is_mp_summary else "PROJECT_RECORD_LEVEL"
            }

audit_results["summary"]["total_files"] = total_files
audit_results["summary"]["total_rows"] = total_rows
audit_results["summary"]["total_size_bytes"] = total_size
audit_results["summary"]["total_size_mb"] = round(total_size / (1024 * 1024), 2)

with open(r"c:\SIH_PROJECT\data-profile.json", "w", encoding="utf-8") as out:
    json.dump(audit_results, out, indent=2, ensure_ascii=False)

print(f"AUDIT SUCCESS: {total_files} files, {total_rows:,} rows, {audit_results['summary']['total_size_mb']} MB analyzed.")
