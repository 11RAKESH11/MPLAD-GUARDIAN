import json

with open("data-profile.json", "r", encoding="utf-8") as f:
    d = json.load(f)

for fkey, finfo in d["files"].items():
    print("=" * 80)
    print(f"FILE: {fkey}")
    print(f"Rows: {finfo['row_count']:,} | Cols: {finfo['column_count']} | Duplicates: {finfo['exact_duplicate_rows']}")
    print("Columns:")
    for c in finfo["headers"]:
        cdata = finfo["columns"][c]
        stats = ""
        if "numeric_stats" in cdata:
            stats = f" [SUM: {cdata['numeric_stats']['total']:,}, AVG: {cdata['numeric_stats']['avg']:,}]"
        print(f"  - {c} (Nulls: {cdata['null_percentage']}%, Samples: {cdata['samples'][:2]}){stats}")
