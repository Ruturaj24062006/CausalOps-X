import torch
import pickle
import json
import os
import pprint

print("--- SCALER INSPECTION ---")
with open("models/root_cause_analysis/model2_v9_step35_training_only_scaler.pkl", "rb") as f:
    scaler = pickle.load(f)

print("Scaler n_features_in_:", getattr(scaler, "n_features_in_", "NOT FOUND"))
if hasattr(scaler, "feature_names_in_"):
    print("Scaler feature_names_in_:")
    pprint.pprint(list(scaler.feature_names_in_))
else:
    print("Scaler feature names: NOT FOUND")

print("\n--- CHECKPOINT INSPECTION ---")
try:
    checkpoint = torch.load("models/root_cause_analysis/model2_v9_best_per_node_model.pt", map_location="cpu")
    print("Checkpoint type:", type(checkpoint))
    if isinstance(checkpoint, dict):
        print("Keys:", checkpoint.keys())
        for k, v in checkpoint.items():
            if torch.is_tensor(v):
                print(k, v.shape)
            elif isinstance(v, dict):
                print(f"DICT {k}")
                for sub_k, sub_v in v.items():
                    if torch.is_tensor(sub_v):
                        print(f"  {sub_k}: {sub_v.shape}")
            else:
                print(f"{k}: {type(v)}")
except Exception as e:
    print("Error loading checkpoint:", e)
