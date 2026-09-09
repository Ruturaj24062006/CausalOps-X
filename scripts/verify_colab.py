import os
import torch
import numpy as np
import pickle
import hashlib

def sha256(p):
    with open(p, "rb") as f: return hashlib.sha256(f.read()).hexdigest()

print("--- POST-TRAINING VERIFICATION ---")

ckpt_path = r"c:\ColabMockWorkspace\best_vae_model1_20f.pth"
if not os.path.exists(ckpt_path):
    print("Checkpoint missing")
else:
    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    print(f"Checkpoint loads: PASS")
    print(f"Input dimension: {ckpt['input_dim']}")
    print(f"Hidden dimension: {ckpt['hidden_dim']}")
    print(f"Latent dimension: {ckpt['latent_dim']}")
    print(f"Sequence length: {ckpt['sequence_length']}")
    print(f"Best epoch: {ckpt['epoch']}")
    print(f"Best validation ELBO (loss): {ckpt['best_validation_loss']:.4f}")

    final_ckpt = torch.load(r"c:\ColabMockWorkspace\final_vae_model1_20f.pth", map_location="cpu", weights_only=False)
    print(f"Training epochs completed: {final_ckpt['epoch']}")
    print(f"Early stopping triggered: {'YES' if final_ckpt['epoch'] < 100 else 'NO'}")

err_path = r"c:\ColabMockWorkspace\model1_validation_errors.npy"
if not os.path.exists(err_path):
    print("Validation errors file missing")
else:
    errors = np.load(err_path)
    print(f"Validation errors File: {err_path}")
    print(f"Count: {len(errors)}")
    print(f"Expected: 5699")
    print(f"Finite: {'PASS' if np.isfinite(errors).all() else 'FAIL'}")
    print(f"NaN: {'FAIL' if np.isnan(errors).any() else 'PASS'}")
    print(f"Infinity: {'FAIL' if np.isinf(errors).any() else 'PASS'}")

# Verify artifacts are untouched
print(f"37F artifacts modified: {'YES' if sha256(r'd:\Projects\CausalOps X\models\anomaly_detection\best_vae.pth') != 'af4bb1a1829f07bbd5cca7ff48ef2e22db61cf86c071d7cb9ec1cfb03f0b2f54' else 'NO'}")
