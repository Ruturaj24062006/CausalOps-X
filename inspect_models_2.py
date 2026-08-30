import torch
import joblib

m1_path = r"d:\Projects\CausalOps X\models\anomaly_detection\best_vae.pth"
scaler_path = r"d:\Projects\CausalOps X\models\anomaly_detection\final_scaler.pkl"
m2_path = r"d:\Projects\CausalOps X\models\root_cause_analysis\best_model_v8.pth"

print("=== MODEL 1 ===")
m1 = torch.load(m1_path, map_location='cpu')
print("Keys in m1:", m1.keys() if isinstance(m1, dict) else type(m1))
if isinstance(m1, dict):
    for k, v in m1.items():
        if hasattr(v, 'shape'):
            print(f"M1 {k}: {v.shape}")
        
scaler = joblib.load(scaler_path)
print("M1 Scaler features in:", getattr(scaler, "n_features_in_", "Unknown"))
if hasattr(scaler, "feature_names_in_"):
    print("M1 Scaler feature names:", list(scaler.feature_names_in_))

print("\n=== MODEL 2 ===")
m2 = torch.load(m2_path, map_location='cpu', weights_only=False)
if 'config' in m2:
    print("M2 Config:", m2['config'])
else:
    print("M2 no config found")

if 'model_state_dict' in m2:
    for k, v in m2['model_state_dict'].items():
        if 'weight' in k and 'encoder.0' in k:
            print(f"M2 Layer {k}: {v.shape}")
