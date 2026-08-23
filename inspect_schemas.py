import json
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

with open('schema_details.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for house, files in data.items():
    print('================================================================================')
    print(f'HOUSE: {house.upper()}')
    print('================================================================================')
    for fname, d in files.items():
        print(f"\nFILE: {fname}")
        print(f"COLUMNS ({len(d['headers'])}):")
        for i, h in enumerate(d['headers']):
            print(f"  [{i}] {h}")
        print("SAMPLE ROWS:")
        for r_idx, row in enumerate(d['samples']):
            print(f"  Row {r_idx+1}:")
            for c_idx, val in enumerate(row):
                header_name = d['headers'][c_idx] if c_idx < len(d['headers']) else f"Col_{c_idx}"
                print(f"    {header_name}: {val}")
