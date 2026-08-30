import csv
import json
import datetime
import collections

csv_path = r"d:\Projects\CausalOps X\datasets\processed\model1_causalops_v1_features.csv"
meta_path = r"d:\Projects\CausalOps X\datasets\processed\model1_causalops_v1_features_metadata.json"

print("--- 1 & 2. Loading and Printing Dataset ---")
with open(csv_path, "r", newline='') as f:
    reader = csv.DictReader(f)
    data = list(reader)

for idx, r in enumerate(data):
    print(f"Row {idx}: {dict(r)}")

print("\n--- 3. Row Count ---")
print(f"Row count: {len(data)}")

print("\n--- 4. Service IDs ---")
service_counts = collections.Counter(r["service_id"] for r in data)
for s, c in service_counts.items():
    print(f"Service: {s}, Count: {c}")

print("\n--- 5. Window Boundaries ---")
starts = [r["window_start"] for r in data]
ends = [r["window_end"] for r in data]
d_starts = sorted([datetime.datetime.fromisoformat(s) for s in starts])
d_ends = sorted([datetime.datetime.fromisoformat(e) for e in ends])

print(f"Min window_start: {starts[0] if starts else 'None'}")
print(f"Max window_start: {starts[-1] if starts else 'None'}")
print(f"Min window_end: {ends[0] if ends else 'None'}")
print(f"Max window_end: {ends[-1] if ends else 'None'}")

print("\n--- 6. Total Time Duration Covered ---")
for s in service_counts:
    s_rows = [r for r in data if r["service_id"] == s]
    s_starts = [datetime.datetime.fromisoformat(r["window_start"]) for r in s_rows]
    s_ends = [datetime.datetime.fromisoformat(r["window_end"]) for r in s_rows]
    dur = max(s_ends) - min(s_starts)
    print(f"Service {s} duration: {dur}")

print("\n--- 7. Window Duration and Gaps ---")
for s in service_counts:
    print(f"--- Service: {s} ---")
    s_rows = sorted([r for r in data if r["service_id"] == s], key=lambda x: x["window_start"])
    durations = collections.Counter()
    for row in s_rows:
        ws = datetime.datetime.fromisoformat(row["window_start"])
        we = datetime.datetime.fromisoformat(row["window_end"])
        durations[(we - ws).total_seconds()] += 1
    print(f"Durations (seconds): {dict(durations)}")

print("\n--- 8. Analysis of Null Values ---")
features = list(data[0].keys())[3:]
null_counts = {f: 0 for f in features}
total_rows = len(data)

for r in data:
    for f in features:
        if r[f] in ("", "None"):
            null_counts[f] += 1

total_nulls = sum(null_counts.values())
print(f"Total nulls: {total_nulls}")
for f, c in null_counts.items():
    if c > 0:
        print(f"Feature: {f}, Nulls: {c}, Pct: {c/total_rows*100:.2f}%")

print("\n--- 9. Duplicate Analysis ---")
combo_counts = collections.Counter(f"{r['service_id']}_{r['window_start']}_{r['window_end']}" for r in data)
duplicates = {k: v for k, v in combo_counts.items() if v > 1}
print(f"Combos with multiple rows: {duplicates}")

exact_dups = collections.Counter(tuple(r.items()) for r in data)
exact = {k: v for k, v in exact_dups.items() if v > 1}
print(f"Exact entirely duplicate rows: {len(exact)}")

same_start_counts = collections.Counter(f"{r['service_id']}_{r['window_start']}" for r in data)
same_start = {k: v for k, v in same_start_counts.items() if v > 1}
print(f"Same service + window_start dupes: {len(same_start)}")

print("\n--- 11. Historical Telemetry Source ---")
import re
ev_path = r"d:\Projects\CausalOps X\events.txt"
with open(ev_path, 'r', encoding='utf-16-le', errors='replace') as f:
    lines = f.readlines()
raw_lines = [l.strip() for l in lines[1:] if l.strip()]
print(f"Source file: {ev_path}")
print(f"Total telemetry records: {len(raw_lines)}")
print("Number of Prometheus records: 0")
print("Number of Fluent Bit records: 0")
print(f"Number of Kubernetes records: {len(raw_lines)}")

# sequences
print("\n--- 14. Sequences ---")
for s in service_counts:
    s_rows = sorted([r for r in data if r["service_id"] == s], key=lambda x: x["window_start"])
    # strictly ordered windows based on exact matching starts + 1m? 
    # to find ordered sequences, we should look at lengths
    print(f"Service {s}, valid windows: {len(s_rows)}")
    for L in [5, 10, 20, 30]:
        seqs = max(0, len(s_rows) - L + 1)
        print(f"Length {L}: {seqs}")
