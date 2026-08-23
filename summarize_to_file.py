import json

with open("data-profile.json", "r", encoding="utf-8") as f:
    d = json.load(f)

with open("summary_readable.txt", "w", encoding="utf-8") as out:
    for k, v in d["files"].items():
        out.write("=" * 80 + "\n")
        out.write(f"FILE: {k}\n")
        out.write(f"Rows: {v['row_count']:,} | Cols: {v['column_count']} | Duplicates: {v['exact_duplicate_rows']}\n")
        out.write("COLUMNS:\n")
        for col_name in v["headers"]:
            col_info = v["columns"][col_name]
            samples = col_info.get("samples", [])
            null_pct = col_info.get("null_percentage", 0)
            stats = col_info.get("numeric_stats", None)
            stat_str = f" | SUM={stats['total']:,}, AVG={stats['avg']:,}" if stats else ""
            out.write(f"  * [{col_name}] (Nulls: {null_pct}%){stat_str}\n")
            out.write(f"      Samples: {samples[:3]}\n")

print("summary_readable.txt written successfully!")
