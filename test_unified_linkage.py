import os
import glob
import csv
import re
from collections import defaultdict

data_dir = r"c:\SIH_PROJECT\DATA"

def clean_work_id(val):
    if not val:
        return None
    val = val.strip().replace("\t", "").replace(" ", "")
    # If formatted as WS/... or similar
    if val.startswith("WS/"):
        return val
    m = re.search(r"(WS/[A-Za-z0-9_-]+/\d{4}-\d{4}/\d+)", val)
    if m:
        return m.group(1)
    return val

def extract_from_row(headers, row):
    row_dict = dict(zip(headers, row))
    # 1. Check explicit Work ID
    for k in ["Work ID", "WorkID", "Work_ID"]:
        if k in row_dict and row_dict[k]:
            w = clean_work_id(row_dict[k])
            if w: return w
            
    # 2. Check Work or WORK column
    for k in ["Work", "WORK", "Work Name"]:
        if k in row_dict and row_dict[k]:
            val = row_dict[k]
            m = re.search(r"(WS/\s*[A-Za-z0-9_-]+/\d{4}-\d{4}/\d+)", val)
            if m:
                return clean_work_id(m.group(1))
            # Or pattern without WS/
            m2 = re.match(r"^([A-Z0-9_/ -]+?)-", val)
            if m2 and "/" in m2.group(1):
                return clean_work_id(m2.group(1))
    return None

results = defaultdict(lambda: defaultdict(set))

for house in ["lok sabha", "rajya sabha"]:
    house_dir = os.path.join(data_dir, house)
    for fpath in glob.glob(os.path.join(house_dir, "*.csv")):
        fname = os.path.basename(fpath)
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            if not headers: continue
            headers = [h.strip() for h in headers]
            
            for row in reader:
                wid = extract_from_row(headers, row)
                if wid:
                    results[house][fname].add(wid)

for house in ["lok sabha", "rajya sabha"]:
    print(f"\n==================== FINAL LINKAGE FOR {house.upper()} ====================")
    for fname, id_set in results[house].items():
        print(f"  {fname}: {len(id_set):,} unique work IDs")
        
    rec_file = next((f for f in results[house] if "recommended" in f.lower()), None)
    sanc_file = next((f for f in results[house] if "sanctioned" in f.lower()), None)
    comp_file = next((f for f in results[house] if "completed" in f.lower() and "expenditure" not in f.lower()), None)
    exp_file = next((f for f in results[house] if "expenditure" in f.lower()), None)
    
    rec_ids = results[house][rec_file]
    sanc_ids = results[house][sanc_file]
    comp_ids = results[house][comp_file]
    exp_ids = results[house][exp_file]
    
    print(f"\nLinkage percentages for {house.upper()}:")
    print(f"  Recommended Total: {len(rec_ids):,}")
    print(f"  Sanctioned Total:  {len(sanc_ids):,} ({round(len(sanc_ids & rec_ids)/len(sanc_ids)*100, 1)}% in Recommended)")
    print(f"  Completed Total:   {len(comp_ids):,} ({round(len(comp_ids & sanc_ids)/len(comp_ids)*100, 1)}% in Sanctioned)")
    print(f"  Expenditure Total: {len(exp_ids):,} ({round(len(exp_ids & sanc_ids)/len(exp_ids)*100, 1)}% in Sanctioned)")
    
    all_works = rec_ids | sanc_ids | comp_ids | exp_ids
    print(f"  Grand Total Distinct Works ({house.upper()}): {len(all_works):,}")
