import pandas as pd
import numpy as np
import pickle
import hashlib
import sys

csv_path = r'd:\Projects\CausalOps X\datasets\processed\model1_causalops_v1_features.csv'
df = pd.read_csv(csv_path)

print("--- TASK 6: CSV STATS ---")
print(f"Total feature rows: {len(df)}")
groups = df.groupby(['namespace', 'pod'])
print(f"Number of service/pod groups: {len(groups)}")
print(f"Earliest window: {df['window_start'].min()}")
print(f"Latest window: {df['window_start'].max()}")

missing = df.isna().sum().sum()
infs = np.isinf(df.select_dtypes(include=np.number)).sum().sum()
print(f"Missing values: {missing}")
print(f"Infinite values: {infs}")

features = [
    'metric_count', 'metric_mean', 'metric_std', 'metric_min', 'metric_max', 'metric_current',
    'log_count', 'error_count', 'warning_count', 'info_count', 'unique_error_count', 'unique_message_count',
    'event_count', 'warning_event_count', 'normal_event_count', 'failed_event_count',
    'unhealthy_event_count', 'unique_reason_count', 'unique_resource_count', 'pod_event_count'
]
has_variation = []
is_constant = []
for f in features:
    if f in df.columns:
        if df[f].nunique() > 1:
            has_variation.append(f)
        else:
            is_constant.append(f)

print("Features with real variation:", has_variation)
print("Constant features:", is_constant)

print("\n--- TASK 8: NPY SEQUENCE STATS ---")
try:
    train = np.load(r"d:\Projects\CausalOps X\datasets\processed\train_seqs.npy")
    val = np.load(r"d:\Projects\CausalOps X\datasets\processed\val_seqs.npy")
    test = np.load(r"d:\Projects\CausalOps X\datasets\processed\test_seqs.npy")
    print(f"train_seqs.npy shape: {train.shape}")
    print(f"val_seqs.npy shape: {val.shape}")
    print(f"test_seqs.npy shape: {test.shape}")
    print(f"No NaN: {not (np.isnan(train).any() or np.isnan(val).any() or np.isnan(test).any())}")
    print(f"No infinity: {not (np.isinf(train).any() or np.isinf(val).any() or np.isinf(test).any())}")
except Exception as e:
    print("NPY load failed:", e)

print("\n--- TASK 9: SCALER CHECK ---")
try:
    import sklearn
    with open(r"d:\Projects\CausalOps X\models\anomaly_detection\model1_20f_scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
    print(f"20F scaler n_features_in_: {scaler.n_features_in_}")
except Exception as e:
    print("Scaler check failed:", e)

import hashlib
def sha256(p):
    with open(p, "rb") as f: return hashlib.sha256(f.read()).hexdigest()

scaler_37f = sha256(r"d:\Projects\CausalOps X\models\anomaly_detection\model1_scaler.pkl")
print(f"37F artifacts untouched: {scaler_37f == 'edecbbfa2e13baaa0a6973dcea47cf6231fca0382cb040f5a5c95144cb13f341'}")
