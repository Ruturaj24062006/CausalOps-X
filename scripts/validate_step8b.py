"""
STEP 8B — Static validation. No training, no model loading, pure text/AST audit.
"""
import os, ast, hashlib

def sha256(p):
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

print("=" * 60)
print("STEP 8B — STATIC VALIDATION")
print("=" * 60)

# ── READ ALL 3 CHANGED FILES ──────────────────────────────────────────────────
FILES = {
    "generate_dataset.py":
        r"d:\Projects\CausalOps X\generate_dataset.py",
    "preprocess_dataset.py":
        r"d:\Projects\CausalOps X\scripts\preprocess_dataset.py",
    "colab_lstm_vae_train.py":
        r"d:\Projects\CausalOps X\scripts\colab_lstm_vae_train.py",
}

srcs = {}
for label, path in FILES.items():
    with open(path, "r", encoding="utf-8-sig") as f:
        srcs[label] = f.read()

# ── SYNTAX CHECK ──────────────────────────────────────────────────────────────
print("\n--- SYNTAX VALIDATION ---")
for label, src in srcs.items():
    try:
        ast.parse(src)
        print(f"  {label}: SYNTAX OK")
    except SyntaxError as e:
        print(f"  {label}: SYNTAX ERROR line {e.lineno}: {e.msg}")

# ── BUG 1: generate_dataset.py ───────────────────────────────────────────────
print("\n--- BUG 1: generate_dataset.py ---")
src = srcs["generate_dataset.py"]

r1a = ('service_id", "namespace", "pod", "window_start"' in src)
r1b = ('getattr(v, "namespace")' in src)
r1c = ('getattr(v, "pod")' in src)
r1d = ('col_names[5:]' in src)
r1e = ('"metric_count", "metric_mean"' in src)    # 20-feature order present
r1f = ('np.random' not in src)                     # no synthetic values

print(f"  namespace+pod in header string  : {r1a}")
print(f"  getattr(v, namespace) in code   : {r1b}")
print(f"  getattr(v, pod) in code         : {r1c}")
print(f"  feature_cols slice = [5:]       : {r1d}")
print(f"  20-feature order intact         : {r1e}")
print(f"  no np.random (no fake values)   : {r1f}")
bug1 = all([r1a, r1b, r1c, r1d, r1e, r1f])
print(f"  BUG 1: {'PASS' if bug1 else 'FAIL'}")

# ── BUG 2: preprocess_dataset.py ─────────────────────────────────────────────
print("\n--- BUG 2: preprocess_dataset.py ---")
src2 = srcs["preprocess_dataset.py"]

# 2a: 20F scaler path
r2a = "model1_20f_scaler.pkl" in src2

# 2b: 37F scaler NOT referenced (after removing the 20f occurrence)
cleaned = src2.replace("model1_20f_scaler.pkl", "")
r2b = "model1_scaler.pkl" not in cleaned

# 2c: all three npy saves
r2c_train = "train_seqs.npy" in src2
r2c_val   = "val_seqs.npy" in src2
r2c_test  = "test_seqs.npy" in src2
r2c_save  = "np.save" in src2

# 2d: dtype float32
r2d = "dtype=np.float32" in src2

# 2e: no synthetic data
r2e = "np.random" not in src2

# 2f: seq_len still 20
r2f = "seq_len = 20" in src2

# 2g: 70/15/15 split intact
r2g = "0.70" in src2 and "0.85" in src2

# 2h: scaler fit on train only
r2h = "scaler.fit(train_features)" in src2

# 2i: boundary rejection intact
r2i = "straddles" in src2 or "len(splits) > 1" in src2

# 2j: 20 features intact
r2j = "pod_event_count" in src2 and "metric_count" in src2

print(f"  20F scaler = model1_20f_scaler.pkl : {r2a}")
print(f"  37F scaler NOT overwritten         : {r2b}")
print(f"  np.save train_seqs.npy             : {r2c_train}")
print(f"  np.save val_seqs.npy               : {r2c_val}")
print(f"  np.save test_seqs.npy              : {r2c_test}")
print(f"  np.save() call present             : {r2c_save}")
print(f"  dtype=np.float32                   : {r2d}")
print(f"  no np.random (no synthetic data)   : {r2e}")
print(f"  seq_len=20                         : {r2f}")
print(f"  70/15/15 split intact              : {r2g}")
print(f"  scaler fit on TRAIN ONLY           : {r2h}")
print(f"  boundary-straddling rejection      : {r2i}")
print(f"  20 features intact                 : {r2j}")
bug2 = all([r2a, r2b, r2c_train, r2c_val, r2c_test, r2c_save,
            r2d, r2e, r2f, r2g, r2h, r2j])
print(f"  BUG 2: {'PASS' if bug2 else 'FAIL'}")

# ── BUG 3: colab_lstm_vae_train.py ───────────────────────────────────────────
print("\n--- BUG 3: colab_lstm_vae_train.py ---")
src3 = srcs["colab_lstm_vae_train.py"]

# 3a: val errors saved
r3a = "model1_validation_errors.npy" in src3
r3a2 = "np.save" in src3

# 3b: uses real best checkpoint
r3b = "best_vae_model1_20f.pth" in src3
r3c = "best_model_eval" in src3
r3d_torch_load = "torch.load" in src3

# 3e: no synthetic
r3e = "np.random" not in src3
r3f_nosim = "simulate_checkpoint_verification" not in src3

# 3g: per-sequence MSE
r3g = "per_seq_mse" in src3
r3h = "best_model_eval.eval()" in src3

# 3i: architecture intact
r3i = ('"input_dim": 20' in src3 and
       '"hidden_dim": 64' in src3 and
       '"latent_dim": 16' in src3 and
       '"sequence_length": 20' in src3)

# 3j: training config intact
r3j = ('"batch_size": 256' in src3 and
       '"learning_rate": 0.001' in src3 and
       '"epochs": 100' in src3 and
       '"patience": 10' in src3 and
       '"seed": 42' in src3)

# 3k: Adam optimizer intact
r3k = "optim.Adam" in src3

print(f"  model1_validation_errors.npy saved : {r3a}")
print(f"  np.save() call present             : {r3a2}")
print(f"  loads best_vae_model1_20f.pth      : {r3b}")
print(f"  best_model_eval instance used      : {r3c}")
print(f"  torch.load call present            : {r3d_torch_load}")
print(f"  no np.random (real errors only)    : {r3e}")
print(f"  no simulate_checkpoint_verif.      : {r3f_nosim}")
print(f"  per_seq_mse computed               : {r3g}")
print(f"  best_model set to eval() mode      : {r3h}")
print(f"  arch intact (20/64/16/seq20)       : {r3i}")
print(f"  train cfg intact (256/0.001/100)   : {r3j}")
print(f"  Adam optimizer intact              : {r3k}")
bug3 = all([r3a, r3a2, r3b, r3c, r3d_torch_load, r3e, r3f_nosim,
            r3g, r3h, r3i, r3j, r3k])
print(f"  BUG 3: {'PASS' if bug3 else 'FAIL'}")

# ── ARTIFACT PROTECTION CHECK ────────────────────────────────────────────────
print("\n--- PROTECTED ARTIFACT INTEGRITY ---")
PROTECTED = [
    ("best_vae.pth",
     r"d:\Projects\CausalOps X\models\anomaly_detection\best_vae.pth",
     "87901ba4150711fc68286406706b397f265086c2dbd8c8169e08aae50f7aa8a4"),
    ("final_scaler.pkl",
     r"d:\Projects\CausalOps X\models\anomaly_detection\final_scaler.pkl",
     "edecbbfa2e13baaa0a6973dcea47cf6231fca0382cb040f5a5c95144cb13f341"),
    ("model1_scaler.pkl (37F)",
     r"d:\Projects\CausalOps X\models\anomaly_detection\model1_scaler.pkl",
     "edecbbfa2e13baaa0a6973dcea47cf6231fca0382cb040f5a5c95144cb13f341"),
    ("model2_v9_best_per_node_model.pt",
     r"d:\Projects\CausalOps X\models\root_cause_analysis\model2_v9_best_per_node_model.pt",
     "64f745ebfd632f131ecd6a7a5add196ff54e5f97240d37908aa6818fbc73216a"),
    ("model2_v9_step35_training_only_scaler.pkl",
     r"d:\Projects\CausalOps X\models\root_cause_analysis\model2_v9_step35_training_only_scaler.pkl",
     "df36200bc4924486a652528b6fd0ddb6dfa053a697b11b0de517922342cb3d85"),
]
artifacts_ok = True
for name, path, expected in PROTECTED:
    actual = sha256(path)
    ok = actual == expected
    if not ok:
        artifacts_ok = False
    print(f"  {name}: {'UNTOUCHED' if ok else 'CHANGED !!!'}")

new20f_on_disk = os.path.exists(
    r"d:\Projects\CausalOps X\models\anomaly_detection\model1_20f_scaler.pkl"
)
print(f"  model1_20f_scaler.pkl pre-exists: {new20f_on_disk} (False expected — created only when preprocessing runs)")

# ── SUMMARY ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
overall = all([bug1, bug2, bug3, artifacts_ok])
print(f"BUG 1 (namespace+pod CSV)    : {'PASS' if bug1 else 'FAIL'}")
print(f"BUG 2 (sequence npy saves)   : {'PASS' if bug2 else 'FAIL'}")
print(f"BUG 3 (real val errors save) : {'PASS' if bug3 else 'FAIL'}")
print(f"37F + M2 artifacts untouched : {'PASS' if artifacts_ok else 'FAIL'}")
print(f"Training executed            : NO")
print(f"OVERALL: {'PASS' if overall else 'FAIL'}")
