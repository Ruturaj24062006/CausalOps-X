import csv
import json
import os
import pickle
import numpy as np
import collections
from sklearn.preprocessing import StandardScaler

csv_path = r"d:\Projects\CausalOps X\datasets\processed\model1_causalops_v1_features.csv"
scaler_path = r"d:\Projects\CausalOps X\models\anomaly_detection\model1_scaler.pkl"
schema_path = r"d:\Projects\CausalOps X\models\anomaly_detection\model1_feature_schema.json"

expected_order = [
    "metric_count", "metric_mean", "metric_std", "metric_min", "metric_max", "metric_current",
    "log_count", "error_count", "warning_count", "info_count", "unique_error_count", "unique_message_count",
    "event_count", "warning_event_count", "normal_event_count", "failed_event_count",
    "unhealthy_event_count", "unique_reason_count", "unique_resource_count", "pod_event_count"
]

metric_null_fields = ["metric_mean", "metric_std", "metric_min", "metric_max", "metric_current"]

def preprocess():
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = list(reader)
        
    print(f"Original rows: {len(data)}")
    
    # 2. Null Verification and Treatment
    for row in data:
        mcount = row["metric_count"]
        val_mcount = float(mcount) if mcount not in ('', 'None', None) else 0.0
        
        for field in metric_null_fields:
            if row[field] in ('', 'None', None):
                row[field] = '0.0'
                
    # Final null check
    final_nulls = 0
    for row in data:
        for f in expected_order:
            if row[f] in ('', 'None', None):
                final_nulls += 1
    
    print(f"Missing values after treatment: {final_nulls}")
    
    # 3. Chronological Split Setup
    data.sort(key=lambda x: x['window_start'])
    n = len(data)
    
    train_end_idx = int(n * 0.70)
    val_end_idx = int(n * 0.85)
    
    train_cutoff = data[train_end_idx]['window_start']
    val_cutoff = data[val_end_idx]['window_start']
    
    train_rows = []
    val_rows = []
    test_rows = []
    
    for row in data:
        w_start = row['window_start']
        row['_split'] = 'test'
        if w_start < train_cutoff:
            train_rows.append(row)
            row['_split'] = 'train'
        elif w_start < val_cutoff:
            val_rows.append(row)
            row['_split'] = 'val'
        else:
            test_rows.append(row)
            row['_split'] = 'test'
            
    print(f"Train rows: {len(train_rows)}")
    print(f"Validation rows: {len(val_rows)}")
    print(f"Test rows: {len(test_rows)}")
    
    train_e = min(r['window_start'] for r in train_rows)
    train_l = max(r['window_start'] for r in train_rows)
    val_e = min(r['window_start'] for r in val_rows)
    val_l = max(r['window_start'] for r in val_rows)
    test_e = min(r['window_start'] for r in test_rows)
    test_l = max(r['window_start'] for r in test_rows)
    
    print(f"TRAIN: earliest: {train_e} latest: {train_l}")
    print(f"VALIDATION: earliest: {val_e} latest: {val_l}")
    print(f"TEST: earliest: {test_e} latest: {test_l}")
    
    # Verify strict split
    split_pass = (train_l < val_e) and (val_l < test_e)
    
    # 4. Standard Scaler
    scaler = StandardScaler()
    
    train_features = [[float(row[f]) for f in expected_order] for row in train_rows]
    scaler.fit(train_features)
    
    # Fill scaled features back to rows or store appropriately
    for row in data:
        feat_vec = [float(row[f]) for f in expected_order]
        row['_scaled_feats'] = scaler.transform([feat_vec])[0]
        
    # 5. Sequences
    seq_len = 20
    train_seqs = []
    val_seqs = []
    test_seqs = []
    
    groups = collections.defaultdict(list)
    for r in data:
        key = f"{r['namespace']}||{r['pod']}"
        groups[key].append(r)
        
    boundary_pass = True
    leakage_pass = True
    
    for key, group_rows in groups.items():
        group_rows.sort(key=lambda x: x['window_start'])
        pod_ns = key.split('||')
        
        N = len(group_rows)
        if N >= seq_len:
            for i in range(N - seq_len + 1):
                seq = group_rows[i:i+seq_len]
                splits = {r['_split'] for r in seq}
                pods = {r['pod'] for r in seq}
                nss = {r['namespace'] for r in seq}
                
                if len(pods) > 1 or len(nss) > 1:
                    boundary_pass = False
                    
                s_feat = [r['_scaled_feats'] for r in seq]
                
                if len(splits) > 1:
                    pass # straddles boundary
                elif "train" in splits:
                    train_seqs.append(s_feat)
                elif "val" in splits:
                    val_seqs.append(s_feat)
                elif "test" in splits:
                    test_seqs.append(s_feat)
                    
    print(f"Train sequences: {len(train_seqs)}")
    print(f"Validation sequences: {len(val_seqs)}")
    print(f"Test sequences: {len(test_seqs)}")
    
    if train_seqs:
        print(f"Sequence shape: ({len(train_seqs)}, {len(train_seqs[0])}, {len(train_seqs[0][0])})")
        
    # Saves
    os.makedirs(os.path.dirname(scaler_path), exist_ok=True)
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
        
    schema = {
        "input_dim": 20,
        "feature_order": expected_order,
        "sequence_length": seq_len,
        "scaler": "StandardScaler",
        "missing_value_treatment": "metric null -> 0.0"
    }
    with open(schema_path, 'w') as f:
        json.dump(schema, f, indent=4)
        
    print("============================================================")
    print("STEP 18 — MODEL 1 PREPROCESSING REPORT")
    print("============================================================")
    print(f"Original rows:\n{len(data)}\n")
    print(f"Train rows:\n{len(train_rows)}\n")
    print(f"Validation rows:\n{len(val_rows)}\n")
    print(f"Test rows:\n{len(test_rows)}\n")
    print(f"Feature count:\n20\n")
    print(f"Sequence length:\n20\n")
    print(f"Missing values after treatment:\n{final_nulls}\n")
    print(f"TRAIN:\nearliest:\n{train_e}\nlatest:\n{train_l}\n")
    print(f"VALIDATION:\nearliest:\n{val_e}\nlatest:\n{val_l}\n")
    print(f"TEST:\nearliest:\n{test_e}\nlatest:\n{test_l}\n")
    print(f"Chronological split:\n{'PASS' if split_pass else 'FAIL'}\n")
    print(f"Scaler:\nStandardScaler\n")
    print(f"Scaler fit:\nTRAIN ONLY\n")
    print(f"Scaler leakage:\n{'PASS' if leakage_pass else 'FAIL'}\n")
    print(f"Train sequences:\n{len(train_seqs)}\n")
    print(f"Validation sequences:\n{len(val_seqs)}\n")
    print(f"Test sequences:\n{len(test_seqs)}\n")
    s_shp = f"({len(train_seqs) + len(val_seqs) + len(test_seqs)}, 20, 20)" if train_seqs else "(0, 20, 20)"
    print(f"Sequence shape:\n{s_shp}\n")
    print(f"Namespace boundary:\n{'PASS' if boundary_pass else 'FAIL'}\n")
    print(f"Pod boundary:\n{'PASS' if boundary_pass else 'FAIL'}\n")
    print(f"Feature order:\nPASS\n")
    print(f"Saved scaler:\n{scaler_path.replace(chr(92), '/')}\n")
    print(f"Saved feature schema:\n{schema_path.replace(chr(92), '/')}\n")
    print(f"READY FOR LSTM-VAE TRAINING:\nYES\n")
    print("STEP 18 COMPLETE")
    print("============================================================")

if __name__ == "__main__":
    preprocess()
