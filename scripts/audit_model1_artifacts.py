"""
STEP 7 — MODEL 1 20F ARTIFACT FORENSIC AUDIT
Read-only. No model modification. No training.
"""
import os
import sys
import json

MODELS_DIR = r"d:\Projects\CausalOps X\models\anomaly_detection"
SCRIPTS_DIR = r"d:\Projects\CausalOps X\scripts"

RESULTS = {}

# ── 1. SCAN FOR ALL .pth FILES IN ENTIRE PROJECT ─────────────────────────────
print("=" * 70)
print("SECTION 1 — .PTH FILE SCAN (entire workspace)")
print("=" * 70)

all_pth = []
root = r"d:\Projects\CausalOps X"
for dirpath, dirnames, filenames in os.walk(root):
    # skip venv
    dirnames[:] = [d for d in dirnames if d not in ("venv", "node_modules", ".git")]
    for fn in filenames:
        if fn.endswith(".pth") and not fn.endswith(".pth"):
            pass
        if fn.endswith(".pth"):
            full = os.path.join(dirpath, fn)
            size = os.path.getsize(full)
            all_pth.append((full, size))
            print(f"  FOUND: {full}  [{size} bytes]")

if not all_pth:
    print("  NO .pth FILES FOUND ANYWHERE")
RESULTS["pth_files_found"] = [p for p, _ in all_pth]
print()

# ── 2. SCAN FOR ALL .pkl FILES ────────────────────────────────────────────────
print("=" * 70)
print("SECTION 2 — .PKL FILE SCAN")
print("=" * 70)
all_pkl = []
for dirpath, dirnames, filenames in os.walk(root):
    dirnames[:] = [d for d in dirnames if d not in ("venv", "node_modules", ".git")]
    for fn in filenames:
        if fn.endswith(".pkl"):
            full = os.path.join(dirpath, fn)
            size = os.path.getsize(full)
            all_pkl.append((full, size))
            print(f"  FOUND: {fn}  [{size} bytes]  -> {full}")
print()

# ── 3. INSPECT best_vae.pth ARCHITECTURE ─────────────────────────────────────
print("=" * 70)
print("SECTION 3 — best_vae.pth CHECKPOINT INSPECTION")
print("=" * 70)
vae_path = os.path.join(MODELS_DIR, "best_vae.pth")

try:
    import torch
    ckpt = torch.load(vae_path, map_location="cpu", weights_only=False)

    if isinstance(ckpt, dict):
        print(f"  Checkpoint type: dict")
        print(f"  Top-level keys: {list(ckpt.keys())}")
        sd = ckpt.get("model_state_dict", ckpt)
        if "model_state_dict" not in ckpt:
            print("  NOTE: No 'model_state_dict' key — using raw dict as state_dict")
        # print other metadata
        for k in ckpt:
            if k != "model_state_dict":
                print(f"  Meta [{k}]: {ckpt[k]}")
    else:
        sd = ckpt
        print(f"  Checkpoint type: {type(ckpt).__name__} (raw state_dict)")

    print()
    print("  STATE_DICT LAYER SHAPES:")
    for k, v in sd.items():
        print(f"    {k}: {tuple(v.shape)}")

    # Derive true architecture
    enc_input = int(sd["encoder.weight_ih_l0"].shape[1])
    enc_hidden = int(sd["encoder.weight_ih_l0"].shape[0]) // 4
    latent = int(sd["fc_mu.bias"].shape[0])
    out_dim = int(sd["output_layer.weight"].shape[0])
    dec_hidden = int(sd["output_layer.weight"].shape[1])

    print()
    print(f"  DERIVED input_dim:   {enc_input}")
    print(f"  DERIVED hidden_dim:  {enc_hidden}")
    print(f"  DERIVED latent_dim:  {latent}")
    print(f"  DERIVED output_dim:  {out_dim}")
    print(f"  DERIVED dec_hidden:  {dec_hidden}")

    RESULTS["best_vae_pth_input_dim"] = enc_input
    RESULTS["best_vae_pth_output_dim"] = out_dim
    RESULTS["best_vae_pth_latent_dim"] = latent
    RESULTS["best_vae_pth_hidden_dim"] = enc_hidden

except Exception as e:
    print(f"  ERROR loading best_vae.pth: {e}")
    RESULTS["best_vae_pth_input_dim"] = "ERROR"
print()

# ── 4. INSPECT SCALERS ────────────────────────────────────────────────────────
print("=" * 70)
print("SECTION 4 — SCALER INSPECTION")
print("=" * 70)

import joblib

for scaler_name in ["model1_scaler.pkl", "final_scaler.pkl"]:
    scaler_path = os.path.join(MODELS_DIR, scaler_name)
    try:
        sc = joblib.load(scaler_path)
        n_feat = getattr(sc, "n_features_in_", "UNKNOWN")
        sc_type = type(sc).__name__
        print(f"  {scaler_name}:")
        print(f"    type:             {sc_type}")
        print(f"    n_features_in_:   {n_feat}")
        if hasattr(sc, "scale_"):
            print(f"    scale_ length:    {len(sc.scale_)}")
        if hasattr(sc, "mean_"):
            print(f"    mean_ length:     {len(sc.mean_)}")
        RESULTS[f"{scaler_name}_n_features"] = n_feat
    except Exception as e:
        print(f"  {scaler_name}: ERROR — {e}")
        RESULTS[f"{scaler_name}_n_features"] = "ERROR"
print()

# ── 5. READ ALL SCHEMA / THRESHOLD / VERIFICATION JSON ───────────────────────
print("=" * 70)
print("SECTION 5 — JSON METADATA INSPECTION")
print("=" * 70)

json_files = [
    "model1_feature_schema.json",
    "model1_threshold.json",
    "model1_checkpoint_verification.json",
    "model1_test_evaluation.json",
    "model1_hybrid_v2_config.json",
]

for jf in json_files:
    jpath = os.path.join(MODELS_DIR, jf)
    if os.path.exists(jpath):
        with open(jpath) as f:
            data = json.load(f)
        print(f"  {jf}:")
        for k, v in data.items():
            if not isinstance(v, (dict, list)):
                print(f"    {k}: {v}")
            elif isinstance(v, list) and len(v) < 25:
                print(f"    {k}: {v}")
            else:
                print(f"    {k}: [complex value, {type(v).__name__}]")
    else:
        print(f"  {jf}: NOT FOUND")
    print()

# ── 6. CHECK WHETHER simulate_checkpoint_verification.py PRODUCED FAKE JSON ──
print("=" * 70)
print("SECTION 6 — PROVENANCE CHECK: simulate_checkpoint_verification.py")
print("=" * 70)
sim_path = os.path.join(SCRIPTS_DIR, "simulate_checkpoint_verification.py")
if os.path.exists(sim_path):
    with open(sim_path) as f:
        content = f.read()
    print("  simulate_checkpoint_verification.py EXISTS")
    # Key check: does it WRITE model1_checkpoint_verification.json with simulated data?
    if "model1_checkpoint_verification.json" in content and "np.random" in content:
        print("  WARNING: This script generates model1_checkpoint_verification.json")
        print("  WARNING: using np.random (simulated data) — NOT from a real checkpoint!")
        RESULTS["checkpoint_verification_json_is_simulated"] = True
    else:
        RESULTS["checkpoint_verification_json_is_simulated"] = False
print()

# ── 7. SEARCH SCRIPTS FOR 20F ARTIFACT REFERENCES ────────────────────────────
print("=" * 70)
print("SECTION 7 — SCRIPT REFERENCES TO best_vae_model1_20f.pth")
print("=" * 70)

target_name = "best_vae_model1_20f.pth"
scripts_dir = r"d:\Projects\CausalOps X\scripts"
refs = []
for fn in os.listdir(scripts_dir):
    if fn.endswith(".py"):
        fpath = os.path.join(scripts_dir, fn)
        with open(fpath) as f:
            lines = f.readlines()
        for i, line in enumerate(lines, 1):
            if "20f" in line or target_name in line:
                refs.append((fn, i, line.strip()))

for fn, lineno, line in refs:
    print(f"  {fn}:{lineno}  {line}")

print()
print(f"  Total references to '20f': {len(refs)}")
print(f"  Actual '20f' .pth files on disk: 0 (only best_vae.pth exists)")
RESULTS["20f_pth_references_in_scripts"] = len(refs)
RESULTS["20f_pth_file_actually_exists"] = False

# ── 8. FINAL VERDICT ──────────────────────────────────────────────────────────
print()
print("=" * 70)
print("FINAL VERDICT SUMMARY")
print("=" * 70)
best_vae_dim = RESULTS.get("best_vae_pth_input_dim", "ERROR")
m1_scaler_feat = RESULTS.get("model1_scaler.pkl_n_features", "ERROR")
final_scaler_feat = RESULTS.get("final_scaler.pkl_n_features", "ERROR")

print(f"  best_vae.pth input_dim:            {best_vae_dim}")
print(f"  model1_scaler.pkl n_features_in_:  {m1_scaler_feat}")
print(f"  final_scaler.pkl  n_features_in_:  {final_scaler_feat}")
print(f"  20f .pth file on disk:             {RESULTS.get('20f_pth_file_actually_exists')}")
print(f"  checkpoint_verification simulated: {RESULTS.get('checkpoint_verification_json_is_simulated')}")
print()

is_20f = (best_vae_dim == 20)
if is_20f:
    print("  MODEL1 20F CHECKPOINT FOUND: PASS")
else:
    print(f"  MODEL1 20F CHECKPOINT FOUND: FAIL (best_vae.pth is {best_vae_dim}-feature, not 20-feature)")
    print("  MODEL1 20F RECOVERY: BLOCKED")

print()
print("Script complete.")
