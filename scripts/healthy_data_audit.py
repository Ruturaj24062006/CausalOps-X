import csv
import json
import os
from collections import defaultdict
from datetime import datetime

csv_path = r'd:\Projects\CausalOps X\datasets\processed\model1_causalops_v1_features.csv'

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    data = list(reader)

total_rows = len(data)

# Known incidents from prompt Context:
# Step 20+ faults occurred logically AFTER 2026-09-08 20:00:00 UTC.
# The historical dataset ends at 2026-09-08 18:47:00 UTC. 
last_ts = max(r['window_start'] for r in data)
eval_start_ts = "2026-09-08T20:00:00Z"
leakage = "PASS" if last_ts < eval_start_ts else "FAIL"

known_incidents = ["2026-09-08T20:15:00Z to 2026-09-08T21:20:00Z (Steps 20, 23, 25, 26 evaluation windows)"]

healthy_rows = []
for r in data:
    f_events = float(r['failed_event_count']) if r['failed_event_count'] not in ('', 'None', None) else 0.0
    u_events = float(r['unhealthy_event_count']) if r['unhealthy_event_count'] not in ('', 'None', None) else 0.0
    
    # We do NOT use warning_event_count or error_count strictly, as standard operation produces log warnings natively.
    # We strictly target structural kubernetes failures or explicitly marked 'unhealthy' probe failures.
    if f_events == 0 and u_events == 0:
        healthy_rows.append(r)

healthy_count = len(healthy_rows)
healthy_retention = (healthy_count / total_rows) * 100

groups = defaultdict(list)
for r in healthy_rows:
    p = r['pod']
    groups[p].append(r)

per_pod_avail = {}
seq_len = 20
total_seqs = 0
pod_seq_counts = {}

# Keep sequence construction strictly pod-isolated
for pod, rows in groups.items():
    rows.sort(key=lambda x: x['window_start'])
    per_pod_avail[pod] = len(rows)
    
    # Simple count of sliding windows (chronology might have gaps technically, but max potential sequences given ordered data):
    seqs = max(0, len(rows) - seq_len + 1)
    pod_seq_counts[pod] = seqs
    total_seqs += seqs

min_seqs_per_pod = min(pod_seq_counts.values()) if pod_seq_counts else 0

insufficient_pods = []
viable_pods = []
for pod, count in pod_seq_counts.items():
    if count < 50:
        insufficient_pods.append(f"{pod} ({count} seqs)")
    else:
        viable_pods.append(pod)

# Chronological split on total valid sequences
train_seqs = int(total_seqs * 0.70)
val_seqs = int(total_seqs * 0.15)
test_seqs = total_seqs - train_seqs - val_seqs

report = {
    "total_rows": total_rows,
    "healthy_count": healthy_count,
    "healthy_retention": healthy_retention,
    "last_ts": last_ts,
    "leakage": leakage,
    "known_incidents": known_incidents,
    "train_seqs": train_seqs,
    "val_seqs": val_seqs,
    "test_seqs": test_seqs,
    "min_seqs_per_pod": min_seqs_per_pod,
    "insufficient_pods_count": len(insufficient_pods),
    "insufficient_pods_examples": insufficient_pods[:5]
}

with open(r'd:\Projects\CausalOps X\scripts\curation_audit.json', 'w') as f:
    json.dump(report, f, indent=2)
