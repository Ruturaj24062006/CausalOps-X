import csv
import json
import os
import numpy as np

csv_path = r'd:\Projects\CausalOps X\datasets\processed\model1_causalops_v1_features.csv'

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    data = list(reader)

# 1. Namespaces, pods, services
namespaces = set(r['namespace'] for r in data)
pods = set(r['pod'] for r in data)
services = set(r['service_id'] for r in data)

print(f"Unique namespaces: {len(namespaces)}")
print(f"Unique pods: {len(pods)}")
print(f"Unique services: {len(services)}")

print("\n--- Training Windows by Service/Pod ---")
groups = {}
for r in data:
    sid = r['service_id']
    pod = r['pod']
    key = f"{sid}|{pod}"
    if key not in groups:
        groups[key] = 0
    groups[key] += 1

total_rows = len(data)
for k, v in groups.items():
    print(f"{k}: {v} ({(v/total_rows)*100:.2f}%)")

# 2. Sequence integrity (check preprocess_dataset.py logic internally)
data.sort(key=lambda x: x['window_start'])
train_end = int(len(data) * 0.70)
val_end = int(len(data) * 0.85)

train_rows = data[:train_end]
val_rows = data[train_end:val_end]
test_rows = data[val_end:]

train_ts = [r['window_start'] for r in train_rows]
val_ts = [r['window_start'] for r in val_rows]
test_ts = [r['window_start'] for r in test_rows]

print(f"\nTraining range: {min(train_ts)} to {max(train_ts)}")
print(f"Validation range: {min(val_ts)} to {max(val_ts)}")
print(f"Test range: {min(test_ts)} to {max(test_ts)}")

# 3. Distribution metrics by major service
major_services = list(services)

metric_keys = [
    'metric_count', 'metric_mean', 'metric_std', 'metric_current',
    'log_count', 'error_count', 'info_count', 'event_count',
    'failed_event_count', 'unhealthy_event_count'
]
metric_null_fields = ['metric_mean', 'metric_std', 'metric_min', 'metric_max', 'metric_current']

print("\n--- Major Service Feature Distributions (Approx Means) ---")
for s in major_services:
    s_rows = [r for r in data if r['service_id'] == s]
    print(f"Service: {s}")
    means = {}
    for mk in metric_keys:
        vals = []
        for r in s_rows:
            v = r[mk]
            if v in ('', 'None', None) and mk in metric_null_fields:
                v = 0.0
            vals.append(float(v) if v not in ('', 'None', None) else 0.0)
        means[mk] = np.mean(vals)
    print(means)
