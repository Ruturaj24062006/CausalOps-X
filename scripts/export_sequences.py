import csv
import json
import os
import pickle
import numpy as np
import collections
from sklearn.preprocessing import StandardScaler

csv_path = r"d:\Projects\CausalOps X\datasets\processed\model1_causalops_v1_features.csv"
scaler_path = r"d:\Projects\CausalOps X\models\anomaly_detection\model1_scaler.pkl"

expected_order = [
    "metric_count", "metric_mean", "metric_std", "metric_min", "metric_max", "metric_current",
    "log_count", "error_count", "warning_count", "info_count", "unique_error_count", "unique_message_count",
    "event_count", "warning_event_count", "normal_event_count", "failed_event_count",
    "unhealthy_event_count", "unique_reason_count", "unique_resource_count", "pod_event_count"
]

def export():
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = list(reader)
        
    for row in data:
        mcount = row["metric_count"]
        val_mcount = float(mcount) if mcount not in ('', 'None', None) else 0.0
        for field in ["metric_mean", "metric_std", "metric_min", "metric_max", "metric_current"]:
            if row[field] in ('', 'None', None): row[field] = '0.0'
                
    data.sort(key=lambda x: x['window_start'])
    train_cutoff = data[int(len(data) * 0.70)]['window_start']
    val_cutoff = data[int(len(data) * 0.85)]['window_start']
    
    train_rows, val_rows, test_rows = [], [], []
    for row in data:
        w_start = row['window_start']
        if w_start < train_cutoff:
            train_rows.append(row)
            row['_split'] = 'train'
        elif w_start < val_cutoff:
            val_rows.append(row)
            row['_split'] = 'val'
        else:
            test_rows.append(row)
            row['_split'] = 'test'
            
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
        
    for row in data:
        feat_vec = [float(row[f]) for f in expected_order]
        row['_scaled_feats'] = scaler.transform([feat_vec])[0]
        
    seq_len = 20
    train_seqs, val_seqs, test_seqs = [], [], []
    
    groups = collections.defaultdict(list)
    for r in data: groups[f"{r['namespace']}||{r['pod']}"].append(r)
        
    for key, group_rows in groups.items():
        group_rows.sort(key=lambda x: x['window_start'])
        N = len(group_rows)
        if N >= seq_len:
            for i in range(N - seq_len + 1):
                seq = group_rows[i:i+seq_len]
                splits = {r['_split'] for r in seq}
                s_feat = [r['_scaled_feats'] for r in seq]
                if len(splits) == 1:
                    if "train" in splits: train_seqs.append(s_feat)
                    elif "val" in splits: val_seqs.append(s_feat)
                    elif "test" in splits: test_seqs.append(s_feat)
                    
    np.save(r"d:\Projects\CausalOps X\datasets\processed\train_seqs.npy", np.array(train_seqs, dtype=np.float32))
    np.save(r"d:\Projects\CausalOps X\datasets\processed\val_seqs.npy", np.array(val_seqs, dtype=np.float32))
    np.save(r"d:\Projects\CausalOps X\datasets\processed\test_seqs.npy", np.array(test_seqs, dtype=np.float32))
    print(f"Exported arrays: {len(train_seqs)} train, {len(val_seqs)} val, {len(test_seqs)} test.")

if __name__ == "__main__":
    export()
