import os
import glob
import csv
import json
import re
from collections import defaultdict, Counter

data_dir = r"c:\SIH_PROJECT\DATA"

def clean_val(val):
    if val is None:
        return ""
    return str(val).strip()

def is_null(val):
    c = clean_val(val).lower()
    return c == "" or c in ["null", "na", "n/a", "none", "-", "nil", "nan", "undefined"]

def parse_num(val):
    if is_null(val):
        return None
    c = clean_val(val).replace("₹", "").replace(",", "").replace(" ", "")
    try:
        return float(c)
    except:
        return None

def analyze():
    audit_data = {
        "overview": {},
        "files": {},
        "cross_linkages": {},
        "geographic_coverage": {},
        "financial_summary": {},
        "data_quality_issues": defaultdict(list),
        "categorical_distributions": {},
        "temporal_coverage": {}
    }

    total_rows = 0
    total_size = 0
    file_list = []

    # Map to hold work IDs across files for linkage checking
    # Key: house -> file_type -> set of work_ids / identifiers
    work_id_sets = defaultdict(lambda: defaultdict(set))
    
    for house in ["lok sabha", "rajya sabha"]:
        house_dir = os.path.join(data_dir, house)
        for fpath in glob.glob(os.path.join(house_dir, "*.csv")):
            fname = os.path.basename(fpath)
            size_bytes = os.path.getsize(fpath)
            total_size += size_bytes
            
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                try:
                    headers = next(reader, None)
                except:
                    headers = []
                
                if not headers:
                    continue
                
                headers = [h.strip() for h in headers]
                rows = []
                row_count = 0
                nulls = defaultdict(int)
                col_samples = defaultdict(list)
                num_cols = defaultdict(list)
                duplicate_rows = 0
                seen_rows = set()
                
                # Detect work_id column if present
                work_id_col = None
                for h in headers:
                    hl = h.lower()
                    if "work id" in hl or "work_id" in hl or "workid" in hl or "project id" in hl or "work code" in hl or "priority" in hl:
                        work_id_col = h
                        break
                
                for row in reader:
                    row_count += 1
                    t_row = tuple(row)
                    if t_row in seen_rows:
                        duplicate_rows += 1
                    else:
                        seen_rows.add(t_row)
                    
                    row_dict = {}
                    for idx, val in enumerate(row):
                        col = headers[idx] if idx < len(headers) else f"col_{idx}"
                        row_dict[col] = val
                        if is_null(val):
                            nulls[col] += 1
                        else:
                            if len(col_samples[col]) < 10:
                                col_samples[col].append(clean_val(val))
                            p = parse_num(val)
                            if p is not None:
                                num_cols[col].append(p)
                                
                    if work_id_col and not is_null(row_dict.get(work_id_col)):
                        work_id_sets[house][fname].add(clean_val(row_dict[work_id_col]))
                        
                    if row_count <= 5:
                        rows.append(row_dict)

                total_rows += row_count
                
                # Column statistics
                col_details = {}
                for col in headers:
                    n_count = nulls[col]
                    n_pct = round((n_count / row_count * 100), 2) if row_count > 0 else 0
                    info = {
                        "name": col,
                        "null_count": n_count,
                        "null_percentage": n_pct,
                        "samples": col_samples[col][:5]
                    }
                    if col in num_cols and len(num_cols[col]) > 0:
                        nums = num_cols[col]
                        info["numeric_stats"] = {
                            "count": len(nums),
                            "min": min(nums),
                            "max": max(nums),
                            "avg": round(sum(nums) / len(nums), 2),
                            "total": round(sum(nums), 2)
                        }
                    col_details[col] = info
                
                file_key = f"{house} :: {fname}"
                audit_data["files"][file_key] = {
                    "house": house,
                    "file_name": fname,
                    "size_mb": round(size_bytes / (1024 * 1024), 2),
                    "row_count": row_count,
                    "column_count": len(headers),
                    "exact_duplicate_rows": duplicate_rows,
                    "work_id_col": work_id_col,
                    "unique_work_ids": len(work_id_sets[house][fname]),
                    "headers": headers,
                    "columns": col_details,
                    "sample_records": rows
                }

    audit_data["overview"] = {
        "total_files": len(audit_data["files"]),
        "total_records": total_rows,
        "total_size_mb": round(total_size / (1024 * 1024), 2)
    }

    # Cross linkage analysis
    for house in ["lok sabha", "rajya sabha"]:
        house_files = [f for f in audit_data["files"] if audit_data["files"][f]["house"] == house]
        # Find files for rec, sanc, comp, exp
        rec_file = next((f for f in house_files if "recommended" in f.lower()), None)
        sanc_file = next((f for f in house_files if "sanctioned" in f.lower()), None)
        comp_file = next((f for f in house_files if "completed" in f.lower() and "expenditure" not in f.lower()), None)
        exp_file = next((f for f in house_files if "expenditure" in f.lower()), None)

        rec_ids = work_id_sets[house][os.path.basename(audit_data["files"][rec_file]["file_name"])] if rec_file else set()
        sanc_ids = work_id_sets[house][os.path.basename(audit_data["files"][sanc_file]["file_name"])] if sanc_file else set()
        comp_ids = work_id_sets[house][os.path.basename(audit_data["files"][comp_file]["file_name"])] if comp_file else set()
        exp_ids = work_id_sets[house][os.path.basename(audit_data["files"][exp_file]["file_name"])] if exp_file else set()

        audit_data["cross_linkages"][house] = {
            "recommended_works_count": len(rec_ids),
            "sanctioned_works_count": len(sanc_ids),
            "completed_works_count": len(comp_ids),
            "expenditure_works_count": len(exp_ids),
            "sanc_in_rec": len(sanc_ids.intersection(rec_ids)),
            "sanc_in_rec_pct": round(len(sanc_ids.intersection(rec_ids)) / len(sanc_ids) * 100, 2) if sanc_ids else 0,
            "comp_in_sanc": len(comp_ids.intersection(sanc_ids)),
            "comp_in_sanc_pct": round(len(comp_ids.intersection(sanc_ids)) / len(comp_ids) * 100, 2) if comp_ids else 0,
            "exp_in_sanc": len(exp_ids.intersection(sanc_ids)),
            "exp_in_sanc_pct": round(len(exp_ids.intersection(sanc_ids)) / len(exp_ids) * 100, 2) if exp_ids else 0
        }

    with open(r"c:\SIH_PROJECT\data-profile.json", "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2, ensure_ascii=False)

    print("Comprehensive audit finished successfully!")
    print(f"Total files: {audit_data['overview']['total_files']}")
    print(f"Total rows: {audit_data['overview']['total_records']:,}")
    print(f"Total size: {audit_data['overview']['total_size_mb']} MB")
    for house, links in audit_data["cross_linkages"].items():
        print(f"\nLinkages for {house.upper()}:")
        print(f"  Recommended Works: {links['recommended_works_count']:,}")
        print(f"  Sanctioned Works: {links['sanctioned_works_count']:,} ({links['sanc_in_rec_pct']}% matched to Recommended)")
        print(f"  Completed Works: {links['completed_works_count']:,} ({links['comp_in_sanc_pct']}% matched to Sanctioned)")
        print(f"  Expenditure Works: {links['expenditure_works_count']:,} ({links['exp_in_sanc_pct']}% matched to Sanctioned)")

if __name__ == "__main__":
    analyze()
