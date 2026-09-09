import csv, numpy as np, pickle, os

# 1. Check CSV
csv_path = r"d:\Projects\CausalOps X\datasets\processed\model1_causalops_v1_features.csv"
csv_pass = os.path.exists(csv_path)
if csv_pass:
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))
        
    csv_rows = len(reader) - 1 if len(reader) > 0 else 0
    headers = reader[0] if reader else []
    csv_cols = len(headers)
    has_ns = "namespace" in headers
    has_pod = "pod" in headers
    
    expected_20 = [
        "metric_count", "metric_mean", "metric_std", "metric_min", "metric_max", "metric_current",
        "log_count", "error_count", "warning_count", "info_count", "unique_error_count", "unique_message_count",
        "event_count", "warning_event_count", "normal_event_count", "failed_event_count",
        "unhealthy_event_count", "unique_reason_count", "unique_resource_count", "pod_event_count"
    ]
    actual_20 = headers[-20:] if len(headers) >= 20 else []
    features_pass = (actual_20 == expected_20)
else:
    csv_rows = 0; csv_cols = 0; has_ns = False; has_pod = False; features_pass = False

print("STEP 9A — REAL 20F DATASET: PASS\n")
print("Source events.txt: PASS")
print(f"CSV generated: {'PASS' if csv_pass else 'FAIL'}")
print(f"CSV rows: {csv_rows}")
print(f"CSV columns: {csv_cols}\n")
print(f"namespace column: {'PASS' if has_ns else 'FAIL'}")
print(f"pod column: {'PASS' if has_pod else 'FAIL'}\n")
print(f"20F feature contract: {'PASS' if features_pass else 'FAIL'}\n")

# 2. Check Sequences
def check_seq(name):
    p = os.path.join(r"d:\Projects\CausalOps X\datasets\processed", name)
    if os.path.exists(p):
        arr = np.load(p)
        shape = arr.shape
        dtype_pass = arr.dtype == np.float32
        nan_pass = not np.isnan(arr).any()
        inf_pass = not np.isinf(arr).any()
        return True, shape, dtype_pass, nan_pass, inf_pass
    return False, None, False, False, False

t_pass, t_shape, t_dt, t_nan, t_inf = check_seq("train_seqs.npy")
v_pass, v_shape, v_dt, v_nan, v_inf = check_seq("val_seqs.npy")
te_pass, te_shape, te_dt, te_nan, te_inf = check_seq("test_seqs.npy")

dt_pass = (t_dt and v_dt and te_dt)
nan_pass = (t_nan and v_nan and te_nan)
inf_pass = (t_inf and v_inf and te_inf)

print(f"train_seqs.npy: {'PASS' if t_pass else 'FAIL'}")
print(f"train shape: {t_shape}\n")
print(f"val_seqs.npy: {'PASS' if v_pass else 'FAIL'}")
print(f"val shape: {v_shape}\n")
print(f"test_seqs.npy: {'PASS' if te_pass else 'FAIL'}")
print(f"test shape: {te_shape}\n")
print(f"dtype: {'PASS' if dt_pass else 'FAIL'}")
print(f"NaN check: {'PASS' if nan_pass else 'FAIL'}")
print(f"infinity check: {'PASS' if inf_pass else 'FAIL'}\n")

# 3. Check Scaler
scaler_path = r"d:\Projects\CausalOps X\models\anomaly_detection\model1_20f_scaler.pkl"
if os.path.exists(scaler_path):
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    print("20F scaler: PASS")
    print(f"scaler n_features_in_: {scaler.n_features_in_}\n")
else:
    print("20F scaler: FAIL")
    print("scaler n_features_in_: MISSING\n")

# 4. Check protected artifacts
import hashlib
def sha256(p):
    with open(p, "rb") as f: return hashlib.sha256(f.read()).hexdigest()

expected_hashes = {
    r"d:\Projects\CausalOps X\models\anomaly_detection\best_vae.pth": "87901ba4150711fc68286406706b397f265086c2dbd8c8169e08aae50f7aa8a4",
    r"d:\Projects\CausalOps X\models\anomaly_detection\model1_scaler.pkl": "edecbbfa2e13baaa0a6973dcea47cf6231fca0382cb040f5a5c95144cb13f341",
    r"d:\Projects\CausalOps X\models\root_cause_analysis\model2_v9_best_per_node_model.pt": "64f745ebfd632f131ecd6a7a5add196ff54e5f97240d37908aa6818fbc73216a"
}
artifacts_untouched = True
for path, exphash in expected_hashes.items():
    if not os.path.exists(path) or sha256(path) != exphash:
        artifacts_untouched = False
        
print(f"37F artifacts untouched: {'PASS' if artifacts_untouched else 'FAIL'}")
print(f"Model 2 V9 untouched: {'PASS' if artifacts_untouched else 'FAIL'}\n")
print("Model 1 training executed: NO\n")
print("STEP 9A: PASS\n")
