import csv
import json
import os
import numpy as np

csv_path = r'd:\Projects\CausalOps X\datasets\processed\model1_causalops_v1_features.csv'

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    data = list(reader)

namespaces = list(set(r['namespace'] for r in data))
pods = list(set(r['pod'] for r in data))
services = list(set(r['service_id'] for r in data))

groups = {}
for r in data:
    key = f"{r['namespace']}|{r['pod']}"
    if key not in groups:
        groups[key] = 0
    groups[key] += 1

data.sort(key=lambda x: x['window_start'])
train_end = int(len(data) * 0.70)
val_end = int(len(data) * 0.85)

train_rows = data[:train_end]
val_rows = data[train_end:val_end]
test_rows = data[val_end:]

train_ts = [r['window_start'] for r in train_rows]
val_ts = [r['window_start'] for r in val_rows]
test_ts = [r['window_start'] for r in test_rows]

ts_ranges = {
    'train': f"{min(train_ts)} to {max(train_ts)}",
    'val': f"{min(val_ts)} to {max(val_ts)}",
    'test': f"{min(test_ts)} to {max(test_ts)}"
}

metric_keys = ['metric_count', 'metric_mean', 'metric_std', 'metric_current', 'log_count', 'error_count', 'info_count', 'event_count', 'failed_event_count', 'unhealthy_event_count']
metric_null_fields = ['metric_mean', 'metric_std', 'metric_min', 'metric_max', 'metric_current']

means = {}
for mk in metric_keys:
    vals = []
    for r in data:
        v = r[mk]
        if v in ('', 'None', None) and mk in metric_null_fields:
            v = 0.0
        vals.append(float(v) if v not in ('', 'None', None) else 0.0)
    means[mk] = float(np.mean(vals))

output = {
    'namespaces': len(namespaces),
    'pods': len(pods),
    'services': len(services),
    'groups': groups,
    'ts_ranges': ts_ranges,
    'means': means
}

with open(r'd:\Projects\CausalOps X\scripts\audit_report.json', 'w') as f:
    json.dump(output, f, indent=2)
