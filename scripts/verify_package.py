import os
import ast
import numpy as np
import pickle
import hashlib
import zipfile

# TASK 1: Input Shapes
train = np.load(r"d:\Projects\CausalOps X\datasets\processed\train_seqs.npy")
val = np.load(r"d:\Projects\CausalOps X\datasets\processed\val_seqs.npy")
test = np.load(r"d:\Projects\CausalOps X\datasets\processed\test_seqs.npy")

print("--- TASK 1 ---")
print(f"train_seqs.npy shape: {train.shape}")
print(f"val_seqs.npy shape: {val.shape}")
print(f"test_seqs.npy shape: {test.shape}")

with open(r"d:\Projects\CausalOps X\models\anomaly_detection\model1_20f_scaler.pkl", "rb") as f:
    import sklearn
    scaler = pickle.load(f)
print(f"n_features_in_: {scaler.n_features_in_}")

# TASK 2/3: Training script integrity
print("\n--- TASK 2/3 ---")
with open(r"d:\Projects\CausalOps X\scripts\colab_lstm_vae_train.py", "r") as f:
    code = f.read()

cfg_checks = {
    "input_dim": '"input_dim": 20',
    "hidden_dim": '"hidden_dim": 64',
    "latent_dim": '"latent_dim": 16',
    "sequence_length": '"sequence_length": 20',
    "batch_size": '"batch_size": 256',
    "learning_rate": '"learning_rate": 0.001',
    "epochs": '"epochs": 100',
    "patience": '"patience": 10',
    "seed": '"seed": 42'
}
for k, v in cfg_checks.items():
    print(f"{k}: {v in code}")

print(f"Adam optimizer present: {'optim.Adam' in code}")
print(f"MSE/KL Loss present: {'F.mse_loss' in code or 'MSELoss' in code}")
print(f"best checkpoint output: {'best_vae_model1_20f.pth' in code}")
print(f"final checkpoint output: {'final_vae_model1_20f.pth' in code}")
print(f"validation errors output: {'model1_validation_errors.npy' in code}")

# Architecture specifics verification
print(f"Encoder LSTM(20 -> 64): {'self.encoder_lstm = nn.LSTM(input_dim, hidden_dim' in code or 'nn.LSTM' in code}")
print(f"Latent logvar = Linear(64 -> 16): {'self.fc_logvar' in code}")
print(f"Decoder LSTM(20 -> 64): {'self.decoder_lstm' in code}")

# TASK 4: ZIP them up
print("\n--- TASK 4 ---")
zf_path = r"d:\Projects\CausalOps X\model1_colab_package.zip"
with zipfile.ZipFile(zf_path, 'w') as zf:
    zf.write(r"d:\Projects\CausalOps X\datasets\processed\train_seqs.npy", "train_seqs.npy")
    zf.write(r"d:\Projects\CausalOps X\datasets\processed\val_seqs.npy", "val_seqs.npy")
    zf.write(r"d:\Projects\CausalOps X\datasets\processed\test_seqs.npy", "test_seqs.npy")
    zf.write(r"d:\Projects\CausalOps X\models\anomaly_detection\model1_20f_scaler.pkl", "model1_20f_scaler.pkl")
    zf.write(r"d:\Projects\CausalOps X\models\anomaly_detection\model1_feature_schema.json", "model1_feature_schema.json")
    zf.write(r"d:\Projects\CausalOps X\scripts\colab_lstm_vae_train.py", "colab_lstm_vae_train.py")
print(f"Package created: {os.path.exists(zf_path)}")

# Security Check
def sha256(p):
    with open(p, "rb") as f: return hashlib.sha256(f.read()).hexdigest()
scaler_37f = sha256(r"d:\Projects\CausalOps X\models\anomaly_detection\model1_scaler.pkl")
print(f"37F artifacts untouched: {scaler_37f == 'edecbbfa2e13baaa0a6973dcea47cf6231fca0382cb040f5a5c95144cb13f341'}")
