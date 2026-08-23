import os
import glob
import csv
import re
from collections import defaultdict, Counter

data_dir = r"c:\SIH_PROJECT\DATA"

states_counter = Counter()
categories_counter = Counter()
years_counter = Counter()
status_counter = Counter()
vendors_counter = Counter()

# Anomaly counters in real data
exp_gt_sanc = 0
sanc_gt_rec = 0
no_description = 0
zero_amount = 0
high_cost_outliers = []
long_pending_works = 0

def clean_val(val):
    return str(val).strip() if val else ""

def parse_num(val):
    if not val: return 0.0
    c = str(val).replace("₹", "").replace(",", "").replace(" ", "").strip()
    try: return float(c)
    except: return 0.0

for house in ["lok sabha", "rajya sabha"]:
    house_dir = os.path.join(data_dir, house)
    
    # Analyze Sanctioned
    sanc_file = glob.glob(os.path.join(house_dir, "*Sanctioned*.csv"))[0]
    with open(sanc_file, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for r in reader:
            st = clean_val(r.get("State"))
            if st: states_counter[st] += 1
            cat = clean_val(r.get("Work category"))
            if cat: categories_counter[cat] += 1
            ws = clean_val(r.get("Work Status"))
            if ws: status_counter[ws] += 1
            
            # extract FY from work
            w = clean_val(r.get("Work"))
            m = re.search(r"/(\d{4}-\d{4})/", w)
            if m:
                years_counter[m.group(1)] += 1
                
    # Analyze Vendors from Expenditure
    exp_file = glob.glob(os.path.join(house_dir, "*Expenditure*.csv"))[0]
    with open(exp_file, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for r in reader:
            v = clean_val(r.get("Vendor Name"))
            amt = parse_num(r.get("Fund Disbursed Amount ( ₹ )"))
            if v:
                vendors_counter[v] += amt

print("==================== STATES DISTRIBUTION (TOP 15) ====================")
for st, cnt in states_counter.most_common(15):
    print(f"  {st}: {cnt:,} sanctioned works")

print(f"\nTotal States/UTs Covered: {len(states_counter)}")

print("\n==================== FINANCIAL YEARS DISTRIBUTION ====================")
for y, cnt in sorted(years_counter.items()):
    print(f"  {y}: {cnt:,} works")

print("\n==================== WORK STATUS DISTRIBUTION ====================")
for ws, cnt in status_counter.most_common(10):
    print(f"  {ws}: {cnt:,} works")

print("\n==================== TOP VENDORS BY TOTAL DISBURSED (₹) ====================")
for v, amt in vendors_counter.most_common(10):
    print(f"  {v}: ₹{amt:,.2f}")
