import torch

m1_path = r"d:\Projects\CausalOps X\models\anomaly_detection\best_vae.pth"
m1 = torch.load(m1_path, map_location='cpu')

print("M1 state dict keys:")
for k, v in m1['model_state_dict'].items():
    if 'weight' in k:
        print(f"{k}: {v.shape}")
