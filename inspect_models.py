import torch
import pickle
import joblib

import os

print("--- MODEL 1 ---")
m1_path = r"d:\Projects\CausalOps X\models\anomaly_detection\best_vae.pth"
scaler_path = r"d:\Projects\CausalOps X\models\anomaly_detection\final_scaler.pkl"

if os.path.exists(m1_path):
    print("File exists:", m1_path)
    try:
        m1 = torch.load(m1_path, map_location='cpu')
        print("Model 1 Loaded successfully.")
        print("Type:", type(m1).__name__)
        if isinstance(m1, dict):
            for k, v in m1.items():
                if hasattr(v, 'shape'):
                    print(f"Key: {k}, Shape: {v.shape}")
        else:
            print("Model architecture directly loaded:")
            print(m1)
    except Exception as e:
        print("Model 1 Error:", e)
else:
    print("Model 1 not found.")

if os.path.exists(scaler_path):
    try:
        scaler = joblib.load(scaler_path)
        print("Scaler Loaded.")
        print("Scaler type:", type(scaler).__name__)
        print("Scaler features:", getattr(scaler, "n_features_in_", "Unknown"))
        if hasattr(scaler, "feature_names_in_"):
            print("Feature names:", scaler.feature_names_in_)
    except Exception as e:
        print("Scaler Error:", e)

print("\n--- MODEL 2 ---")
m2_path = r"d:\Projects\CausalOps X\models\root_cause_analysis\best_model_v8.pth"

if os.path.exists(m2_path):
    print("File exists:", m2_path)
    try:
        m2 = torch.load(m2_path, map_location='cpu', weights_only=False)
        print("Model 2 Loaded successfully.", type(m2).__name__)
        if isinstance(m2, dict):
            # Might be a state dict or checkpoint with multiple keys
            print("Keys:", list(m2.keys())[:10])
            for k, v in m2.items():
                if isinstance(v, dict):
                    print(f"Dict {k} keys:", list(v.keys())[:5])
                    for subk, subv in v.items():
                        if hasattr(subv, 'shape'):
                            print(f" - {subk} shape: {subv.shape}")
                elif hasattr(v, 'shape'):
                    print(f"Key {k} shape: {v.shape}")
        else:
            print("Model architecture directly loaded:")
            print(m2)
    except Exception as e:
        print("Model 2 Error:", e)
else:
    print("Model 2 not found.")
