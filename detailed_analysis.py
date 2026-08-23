import os
import glob
import csv
import json

data_dir = r"c:\SIH_PROJECT\DATA"

report = {}

for house in ["lok sabha", "rajya sabha"]:
    house_dir = os.path.join(data_dir, house)
    report[house] = {}
    
    for fpath in glob.glob(os.path.join(house_dir, "*.csv")):
        fname = os.path.basename(fpath)
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            sample_rows = []
            for _ in range(3):
                row = next(reader, None)
                if row:
                    sample_rows.append(row)
            
            report[house][fname] = {
                "headers": headers,
                "samples": sample_rows
            }

with open(r"c:\SIH_PROJECT\schema_details.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print("Schema details extracted.")
