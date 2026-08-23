import os
import glob
import csv
import re
from collections import defaultdict, Counter

data_dir = r"c:\SIH_PROJECT\DATA"

def extract_work_code(work_str):
    if not work_str:
        return None, None
    work_str = work_str.strip().replace("\t", " ")
    # Match pattern like WS/MP620/2024-2025/133166 or WS/ MP620/2024-2025/133166
    m = re.match(r"^(WS/\s*[A-Z0-9_-]+/\d{4}-\d{4}/\d+)", work_str)
    if m:
        code = re.sub(r"\s+", "", m.group(1))
        title = work_str[m.end():].lstrip(" -").strip()
        return code, title
    # Alternate formats
    m2 = re.match(r"^([A-Z0-9_/ -]+?)-(.*)$", work_str)
    if m2 and "/" in m2.group(1):
        code = re.sub(r"\s+", "", m2.group(1))
        return code, m2.group(2).strip()
    return None, work_str

def parse_ida(ida_str):
    if not ida_str:
        return "", ""
    ida_str = ida_str.strip()
    m = re.match(r"^([^(]+)\((.+)\)$", ida_str)
    if m:
        district = m.group(1).strip()
        agency = m.group(2).strip()
        return district, agency
    return ida_str, ""

# Let's test extraction across all files
code_tracker = defaultdict(lambda: defaultdict(dict))

for house in ["lok sabha", "rajya sabha"]:
    house_dir = os.path.join(data_dir, house)
    for fpath in glob.glob(os.path.join(house_dir, "*.csv")):
        fname = os.path.basename(fpath)
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            if not headers: continue
            
            headers = [h.strip() for h in headers]
            
            work_col = None
            for h in headers:
                if h.lower() in ["work", "work id", "workid"]:
                    work_col = h
                    break
                    
            if not work_col:
                continue
                
            w_idx = headers.index(work_col)
            valid_codes = 0
            total_rows = 0
            
            for row in reader:
                if not row or len(row) <= w_idx: continue
                total_rows += 1
                val = row[w_idx]
                code, title = extract_work_code(val)
                if code:
                    valid_codes += 1
                    code_tracker[house][fname][code] = title
                    
            print(f"[{house.upper()}] {fname}: {valid_codes:,} / {total_rows:,} ({round(valid_codes/total_rows*100, 1)}%) valid work codes extracted")

# Now check cross-file overlaps with clean codes
for house in ["lok sabha", "rajya sabha"]:
    files = code_tracker[house]
    rec_codes = set(files.get(next((f for f in files if "recommended" in f.lower()), ""), {}).keys())
    sanc_codes = set(files.get(next((f for f in files if "sanctioned" in f.lower()), ""), {}).keys())
    comp_codes = set(files.get(next((f for f in files if "completed" in f.lower() and "expenditure" not in f.lower()), ""), {}).keys())
    exp_codes = set(files.get(next((f for f in files if "expenditure" in f.lower()), ""), {}).keys())
    
    print(f"\n==================== OVERLAPS FOR {house.upper()} ====================")
    print(f"Unique Recommended Codes: {len(rec_codes):,}")
    print(f"Unique Sanctioned Codes:   {len(sanc_codes):,}")
    print(f"Unique Completed Codes:    {len(comp_codes):,}")
    print(f"Unique Expenditure Codes:  {len(exp_codes):,}")
    
    print(f"Sanctioned in Recommended: {len(sanc_codes & rec_codes):,} ({round(len(sanc_codes & rec_codes)/len(sanc_codes)*100, 1)}%)")
    print(f"Completed in Sanctioned:   {len(comp_codes & sanc_codes):,} ({round(len(comp_codes & sanc_codes)/len(comp_codes)*100, 1)}%)")
    print(f"Expenditure in Sanctioned: {len(exp_codes & sanc_codes):,} ({round(len(exp_codes & sanc_codes)/len(exp_codes)*100, 1)}%)")
    
    all_unique = rec_codes | sanc_codes | comp_codes | exp_codes
    print(f"TOTAL UNIQUE LIFECYCLE WORK CODES: {len(all_unique):,}")
