import os
import torch
import numpy as np

ckpt_path = r"c:\ColabMockWorkspace\best_vae_model1_20f.pth"
ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
print(f"Checkpoint loads: PASS")
print(f"Input dimension: {ckpt['input_dim']}")
print(f"Hidden dimension: {ckpt['hidden_dim']}")
print(f"Latent dimension: {ckpt['latent_dim']}")
print(f"Sequence length: {ckpt['sequence_length']}")
print(f"Best epoch: {ckpt['epoch']}")
print(f"Best validation ELBO: {ckpt['best_validation_loss']:.4f}")

final_ckpt = torch.load(r"c:\ColabMockWorkspace\final_vae_model1_20f.pth", map_location="cpu", weights_only=False)
print(f"Training epochs completed: {final_ckpt['epoch']}")
print(f"Early stopping triggered: {'YES' if final_ckpt['epoch'] < 100 else 'NO'}")

err_path = r"c:\ColabMockWorkspace\model1_validation_errors.npy"
errors = np.load(err_path)
print(f"Validation errors File: {err_path}")
print(f"Count: {len(errors)}")
print(f"Finite: {'PASS' if np.isfinite(errors).all() else 'FAIL'}")
print(f"NaN: {'FAIL' if np.isnan(errors).any() else 'PASS'}")
print(f"Infinity: {'FAIL' if np.isinf(errors).any() else 'PASS'}")
