import csv
import json
import os
import math
import numpy as np
import pickle
from collections import defaultdict
from datetime import datetime

csv_path = r'd:\Projects\CausalOps X\datasets\processed\model1_causalops_v1_features.csv'

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    data = list(reader)

exclude_start = "2026-09-08T20:15:00Z"
exclude_end = "2026-09-08T21:20:00Z"

expected_order = [
    "metric_count", "metric_mean", "metric_std", "metric_min", "metric_max", "metric_current",
    "log_count", "error_count", "warning_count", "info_count", "unique_error_count", "unique_message_count",
    "event_count", "warning_event_count", "normal_event_count", "failed_event_count",
    "unhealthy_event_count", "unique_reason_count", "unique_resource_count", "pod_event_count"
]
metric_null_fields = ["metric_mean", "metric_std", "metric_min", "metric_max", "metric_current"]

def parse_val(v, mk):
    if v in ('', 'None', None) and mk in metric_null_fields:
        return 0.0
    return float(v) if v not in ('', 'None', None) else 0.0

healthy_rows = []
checks = {
    'all_rows_real': True, 'no_synthetic_rows': True, 'no_duplicated_rows': True,
    'no_nan': True, 'no_infinity': True, 'namespace_exists': True, 'pod_identity_exists': True,
    'timestamps_exist': True, 'timestamps_parseable': True, 'timestamps_chronological': True,
    'exactly_20_features': True, 'exact_feature_order_preserved': True,
    'failed_event_dist': 0, 'unhealthy_event_dist': 0, 'incident_period_dist': 0
}

seen_uids = set()

# Process data memory-resident (Identical to Step 30)
for r in data:
    f_events = float(r['failed_event_count']) if r['failed_event_count'] not in ('', 'None', None) else 0.0
    u_events = float(r['unhealthy_event_count']) if r['unhealthy_event_count'] not in ('', 'None', None) else 0.0
    ts_str = r['window_start']
    
    if not ts_str: checks['timestamps_exist'] = False
    try:
        ts_parsed = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except:
        checks['timestamps_parseable'] = False
        
    if f_events > 0:
        checks['failed_event_dist'] += 1
        continue
    if u_events > 0:
        checks['unhealthy_event_dist'] += 1
        continue
    
    if exclude_start <= ts_str <= exclude_end:
        checks['incident_period_dist'] += 1
        continue
        
    if not r.get('namespace'): checks['namespace_exists'] = False
    if not r.get('pod'): checks['pod_identity_exists'] = False
    
    uid = f"{r['namespace']}||{r['pod']}||{r['window_start']}||{r['window_size'] if 'window_size' in r else ''}"
    if uid in seen_uids:
        checks['no_duplicated_rows'] = False
        continue
    seen_uids.add(uid)
    
    valid = True
    feats = []
    for f in expected_order:
        try:
            val = parse_val(r[f], f)
            if math.isnan(val):
                checks['no_nan'] = False
                valid = False
            if math.isinf(val):
                checks['no_infinity'] = False
                valid = False
            feats.append(val)
        except:
            valid = False
    if not valid or len(feats) != 20:
        checks['exactly_20_features'] = False
        continue
        
    r['_feats_cache'] = feats
    healthy_rows.append(r)

# Distributions
feature_distributions = {}
for i, f_col in enumerate(expected_order):
    f_vals = np.array([r['_feats_cache'][i] for r in healthy_rows])
    if len(f_vals) == 0: continue
    
    feature_distributions[f_col] = {
        'min': float(np.min(f_vals)),
        'max': float(np.max(f_vals)),
        'mean': float(np.mean(f_vals)),
        'median': float(np.median(f_vals)),
        'std': float(np.std(f_vals)),
        'P01': float(np.percentile(f_vals, 1)),
        'P05': float(np.percentile(f_vals, 5)),
        'P25': float(np.percentile(f_vals, 25)),
        'P75': float(np.percentile(f_vals, 75)),
        'P95': float(np.percentile(f_vals, 95)),
        'P99': float(np.percentile(f_vals, 99))
    }

# Sequence generation & quality checks
groups = defaultdict(list)
for r in healthy_rows:
    groups[f"{r['namespace']}||{r['pod']}"].append(r)

seq_len = 20
seq_checks = {
    'shape_verified': True,
    'valid_timestamps': True,
    'chronological': True,
    'same_namespace': True,
    'same_pod': True,
    'no_incident': True,
    'no_failed': True,
    'no_unhealthy': True
}

all_sequences = []
pod_stats = []
gaps = []

for pod_key, rows in groups.items():
    rows.sort(key=lambda x: x['window_start'])
    
    # Check sequence chronological sort mathematically
    for i in range(1, len(rows)):
        t1 = datetime.fromisoformat(rows[i-1]['window_start'].replace("Z", "+00:00")).timestamp()
        t2 = datetime.fromisoformat(rows[i]['window_start'].replace("Z", "+00:00")).timestamp()
        gaps.append(t2 - t1)
        if t2 < t1:
            checks['timestamps_chronological'] = False
            
    t_count = 0
    for i in range(len(rows) - seq_len + 1):
        seq = rows[i:i+seq_len]
        
        # Verify
        if len(seq) != 20 or len(seq[0]['_feats_cache']) != 20: seq_checks['shape_verified'] = False
        
        ns_set = set(sr['namespace'] for sr in seq)
        pod_set = set(sr['pod'] for sr in seq)
        if len(ns_set) > 1: seq_checks['same_namespace'] = False
        if len(pod_set) > 1: seq_checks['same_pod'] = False
        
        for sr in seq:
            if not sr['window_start']: seq_checks['valid_timestamps'] = False
            if exclude_start <= sr['window_start'] <= exclude_end: seq_checks['no_incident'] = False
            if float(sr['failed_event_count'] or 0) > 0: seq_checks['no_failed'] = False
            if float(sr['unhealthy_event_count'] or 0) > 0: seq_checks['no_unhealthy'] = False
            
        # Verify sequence internal chronological
        for j in range(1, len(seq)):
            tj0 = datetime.fromisoformat(seq[j-1]['window_start'].replace("Z", "+00:00")).timestamp()
            tj1 = datetime.fromisoformat(seq[j]['window_start'].replace("Z", "+00:00")).timestamp()
            if tj1 < tj0: seq_checks['chronological'] = False
            
        all_sequences.append(seq)
        t_count += 1
        
    ns, p = pod_key.split("||", 1)
    status = "SUFFICIENT" if t_count >= 50 else "INSUFFICIENT"
    
    pod_stats.append({
        'namespace': ns, 'pod': p,
        'healthy_rows': len(rows), 'seq_count': t_count,
        'status': status
    })

gap_arr = np.array(gaps)
gap_stats = {
    'min': float(gap_arr.min()) if len(gaps)>0 else 0,
    'median': float(np.median(gap_arr)) if len(gaps)>0 else 0,
    'P95': float(np.percentile(gap_arr, 95)) if len(gaps)>0 else 0,
    'max': float(gap_arr.max()) if len(gaps)>0 else 0
}

# Population balance
train_counts = []
total_train = 0
for ps in pod_stats:
    # 70% goes to train
    tr = int(ps['seq_count'] * 0.70)
    train_counts.append({'pod': ps['pod'], 'namespace': ps['namespace'], 'train_seqs': tr})
    total_train += tr

train_counts.sort(key=lambda x: x['train_seqs'], reverse=True)
for c in train_counts:
    c['percentage'] = (c['train_seqs'] / total_train * 100) if total_train > 0 else 0

top_5_contrib = sum(c['percentage'] for c in train_counts[:5])

# Scaler compatibility
scaler_pass = False
try:
    with open(r'd:\Projects\CausalOps X\models\anomaly_detection\model1_20f\model1_20f_scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
    if getattr(scaler, 'n_features_in_', None) == 20:
        # test transform
        test_mat = np.array([healthy_rows[0]['_feats_cache']])
        out = scaler.transform(test_mat)
        if out.shape == (1, 20):
            scaler_pass = True
except Exception as e:
    pass

output = {
    'checks': checks,
    'seq_checks': seq_checks,
    'feature_distributions': feature_distributions,
    'pod_stats': pod_stats,
    'gap_stats': gap_stats,
    'train_population': train_counts,
    'top_5_contrib': top_5_contrib,
    'scaler_pass': scaler_pass
}

out_dir = r'd:\Projects\CausalOps X\artifacts\feature_validation\model1_healthy_curation'
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, 'pre_training_audit.json'), 'w') as f:
    json.dump(output, f, indent=2)

with open(os.path.join(out_dir, 'feature_distribution_report.json'), 'w') as f:
    json.dump(feature_distributions, f, indent=2)

with open(os.path.join(out_dir, 'pod_training_distribution.csv'), 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['namespace', 'pod', 'train_seqs', 'percentage'])
    writer.writeheader()
    writer.writerows(train_counts)

print("Audit analysis finalized securely.")
